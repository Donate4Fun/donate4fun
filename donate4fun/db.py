import logging
from uuid import UUID
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import select, desc, update, Column, TIMESTAMP, String, BigInteger, ForeignKey, func, text, literal
from sqlalchemy.dialects.postgresql import insert, UUID as Uuid
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.orm.exc import NoResultFound  # noqa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy_utils.functions import get_referencing_foreign_keys

from .models import Donation, Donator, YoutubeChannel, YoutubeVideo, Notification, Credentials
from .types import RequestHash, NotEnoughBalance, NotFound
from .settings import DbSettings

logger = logging.getLogger(__name__)


Base = declarative_base()


class YoutubeChannelDb(Base):
    __tablename__ = 'youtube_channel'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    channel_id = Column(String, unique=True, nullable=False)
    title = Column(String)
    thumbnail_url = Column(String)
    balance = Column(BigInteger, nullable=False, server_default=text('0'))
    total_donated = Column(BigInteger, nullable=False, server_default=text('0'))


class YoutubeVideoDb(Base):
    __tablename__ = 'youtube_video'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    video_id = Column(String, unique=True, nullable=False)
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id), nullable=False)
    title = Column(String)
    thumbnail_url = Column(String)
    total_donated = Column(BigInteger, nullable=False, server_default=text('0'))
    default_audio_language = Column(String)

    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')


class DonatorDb(Base):
    __tablename__ = 'donator'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String)
    avatar_url = Column(String)
    lnauth_pubkey = Column(String, unique=True)
    balance = Column(BigInteger, nullable=False, server_default=text('0'))

    linked_youtube_channels = relationship(
        YoutubeChannelDb,
        lazy='noload',
        secondary=lambda: Base.metadata.tables['youtube_channel_link'],
    )


class YoutubeChannelLink(Base):
    __tablename__ = 'youtube_channel_link'

    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id), primary_key=True)
    donator_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id), primary_key=True)


class DonationDb(Base):
    __tablename__ = 'donation'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    r_hash = Column(String, unique=True)
    amount = Column(BigInteger, nullable=False)
    donator_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id), nullable=False)
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id))
    youtube_video_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeVideoDb.id))
    receiver_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    paid_at = Column(TIMESTAMP)
    cancelled_at = Column(TIMESTAMP)

    donator = relationship(DonatorDb, lazy='joined', foreign_keys=[donator_id])
    receiver = relationship(DonatorDb, lazy='joined', foreign_keys=[receiver_id])
    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')
    youtube_video = relationship(YoutubeVideoDb, lazy='joined')


class WithdrawalDb(Base):
    __tablename__ = 'withdrawal'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    donator_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id), nullable=False)
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id), nullable=False)
    amount = Column(BigInteger)

    created_at = Column(TIMESTAMP, nullable=False)
    paid_at = Column(TIMESTAMP)

    donator = relationship(DonatorDb, lazy='joined')
    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')


Base.registry.configure()  # Create backrefs


class Database:
    def __init__(self, db_settings: DbSettings):
        self.engine = create_async_engine(**db_settings.dict())
        self.session_maker = sessionmaker(self.engine, class_=AsyncSession, future=True)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            await conn.run_sync(Base.metadata.create_all)
            for foreign_key in get_referencing_foreign_keys(DonatorDb):
                table_name = foreign_key.parent.table.name
                await conn.execute(text(
                    f'ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {table_name}_{foreign_key.parent.key}_fkey'
                ))

    async def execute(self, query: str):
        async with self.engine.connect() as connection:
            await connection.execute(text(query))

    async def dispose(self):
        await self.engine.dispose()

    async def create_database(self, db_name: str):
        return await self.execute(f'CREATE DATABASE "{db_name}"')

    async def drop_database(self, db_name: str):
        return await self.execute(f'DROP DATABASE "{db_name}"')

    @asynccontextmanager
    async def session(self) -> 'DbSession':
        async with self.raw_session() as session, session.begin():
            db_session = DbSession(self, session)
            await session.connection(execution_options=dict(logging_token=str(db_session)))
            yield db_session

    @asynccontextmanager
    async def raw_session(self):
        async with self.session_maker() as session:
            yield session


class DbSession:
    def __init__(self, db, session):
        self.db = db
        self.session = session

    def __str__(self):
        return f'{type(self).__name__}<{hex(id(self))}>'

    async def execute(self, query):
        return await self.session.execute(query)

    async def notify(self, channel: str, notification: Notification):
        await self.execute(select(func.pg_notify(channel, notification.json())))

    async def query_youtube_channel(self, youtube_channel_id: UUID) -> YoutubeChannel:
        resp = await self.execute(
            select(YoutubeChannelDb)
            .where(YoutubeChannelDb.id == youtube_channel_id)
        )
        return YoutubeChannel.from_orm(resp.scalars().one())

    async def find_youtube_channel(self, channel_id: str) -> YoutubeChannel:
        resp = await self.execute(
            select(YoutubeChannelDb)
            .where(YoutubeChannelDb.channel_id == channel_id)
        )
        return YoutubeChannel.from_orm(resp.scalars().one())

    async def query_youtube_channels(self) -> list[YoutubeChannel]:
        resp = await self.execute(
            select(YoutubeChannelDb)
        )
        return [YoutubeChannel.from_orm(data) for data in resp.scalars()]

    async def lock_youtube_channel(self, youtube_channel_id: UUID) -> YoutubeChannel:
        result = await self.execute(
            select(YoutubeChannelDb)
            .with_for_update(of=YoutubeChannelDb)
            .where(YoutubeChannelDb.id == youtube_channel_id)
        )
        return YoutubeChannel.from_orm(result.scalars().one())

    async def create_withdrawal(self, youtube_channel_id: UUID, donator_id: UUID) -> UUID:
        result = await self.execute(
            insert(WithdrawalDb)
            .values(dict(
                donator_id=donator_id,
                youtube_channel_id=youtube_channel_id,
                created_at=datetime.utcnow(),
            ))
            .returning(WithdrawalDb.id)
        )
        return result.scalars().one()

    async def lock_withdrawal(self, withdrawal_id: UUID):
        result = await self.execute(
            select(WithdrawalDb)
            .with_for_update(of=WithdrawalDb)
            .where(
                (WithdrawalDb.id == withdrawal_id)
                & WithdrawalDb.paid_at.is_(None)
            )
        )
        return result.scalars().one()

    async def withdraw(self, withdrawal_id: UUID, youtube_channel_id: UUID, amount: int) -> int:
        """
        return new balance
        """
        result = await self.execute(
            update(YoutubeChannelDb)
            .where((YoutubeChannelDb.id == youtube_channel_id) & (YoutubeChannelDb.balance >= amount))
            .values(balance=YoutubeChannelDb.balance - amount)
            .returning(YoutubeChannelDb.balance)
        )
        new_balance = result.scalars().one()
        result = await self.execute(
            update(WithdrawalDb)
            .values(
                paid_at=datetime.utcnow(),
                amount=amount,
            )
            .where(WithdrawalDb.id == withdrawal_id)
        )
        if result.rowcount != 1:
            raise NotFound(f"Withdrawal {withdrawal_id} does not exist")
        return new_balance

    async def save_donator(self, donator: Donator):
        await self.execute(
            insert(DonatorDb)
            .values(dict(
                id=donator.id,
                name=donator.name,
                avatar_url=donator.avatar_url,
                lnauth_pubkey=donator.lnauth_pubkey,
            ))
            .on_conflict_do_update(
                index_elements=[DonatorDb.id],
                set_={DonatorDb.name: donator.name, DonatorDb.avatar_url: donator.avatar_url},
                where=(DonatorDb.name != donator.name) | (DonatorDb.avatar_url != donator.avatar_url),
            )
        )

    async def query_donator(self, donator_id: UUID) -> Donator:
        result = await self.execute(
            select(DonatorDb)
            .where(DonatorDb.id == donator_id)
        )
        scalar = result.scalars().one()
        return Donator.from_orm(scalar)

    async def query_donator_youtube_channels(self, donator_id: UUID) -> list[YoutubeChannel]:
        result = await self.execute(
            select(YoutubeChannelDb)
            .join(YoutubeChannelLink, YoutubeChannelDb.id == YoutubeChannelLink.youtube_channel_id)
            .where(YoutubeChannelLink.donator_id == donator_id)
        )
        return [YoutubeChannel.from_orm(obj) for obj in result.unique().scalars()]

    async def query_donations(self, where, limit=20):
        result = await self.execute(
            select(DonationDb)
            .where(where)
            .order_by(desc(func.coalesce(DonationDb.paid_at, DonationDb.created_at)))
            .limit(limit)
        )
        return [Donation.from_orm(obj) for obj in result.unique().scalars()]

    async def query_donation(self, *, r_hash: RequestHash | None = None, id: UUID | None = None) -> Donation:
        result = await self.execute(
            select(DonationDb)
            .where(
                (DonationDb.r_hash == r_hash.as_base64) if r_hash else (DonationDb.id == id)
            )
        )
        data = result.scalars().one()
        return Donation.from_orm(data)

    async def save_youtube_channel(self, youtube_channel: YoutubeChannel):
        resp = await self.execute(
            insert(YoutubeChannelDb)
            .values(youtube_channel.dict())
            .on_conflict_do_update(
                index_elements=[YoutubeChannelDb.channel_id],
                set_={
                    YoutubeChannelDb.title: youtube_channel.title,
                    YoutubeChannelDb.thumbnail_url: youtube_channel.thumbnail_url,
                },
                where=(
                    (func.coalesce(YoutubeChannelDb.title, '') != youtube_channel.title)
                    | (func.coalesce(YoutubeChannelDb.thumbnail_url, '') != youtube_channel.thumbnail_url)
                ),
            )
            .returning(YoutubeChannelDb.id)
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(YoutubeChannelDb.id).where(YoutubeChannelDb.channel_id == youtube_channel.channel_id)
            )
            id_ = resp.scalar()
        youtube_channel.id = id_

    async def save_youtube_video(self, youtube_video: YoutubeVideo):
        resp = await self.execute(
            insert(YoutubeVideoDb)
            .values(dict(
                youtube_channel_id=youtube_video.youtube_channel.id,
                **{
                    key: value
                    for key, value in youtube_video.dict().items()
                    if key != 'youtube_channel'
                },
            ))
            .on_conflict_do_update(
                index_elements=[YoutubeVideoDb.video_id],
                set_={
                    YoutubeVideoDb.title: youtube_video.title,
                    YoutubeVideoDb.thumbnail_url: youtube_video.thumbnail_url,
                },
                where=(
                    (func.coalesce(YoutubeVideoDb.title, '') != youtube_video.title)
                    | (func.coalesce(YoutubeVideoDb.thumbnail_url, '') != youtube_video.thumbnail_url)
                ),
            )
            .returning(YoutubeVideoDb.id)
        )
        id_: UUID = resp.scalar()
        if id_ is None:
            resp = await self.execute(
                select(YoutubeVideoDb.id).where(YoutubeVideoDb.video_id == youtube_video.video_id)
            )
            id_ = resp.scalar()
        youtube_video.id = id_

    async def create_donation(self, donation: Donation):
        donation.created_at = datetime.utcnow()
        await self.execute(
            insert(DonationDb)
            .values(
                id=donation.id,
                created_at=donation.created_at,
                youtube_channel_id=donation.youtube_channel and donation.youtube_channel.id,
                youtube_video_id=donation.youtube_video and donation.youtube_video.id,
                receiver_id=donation.receiver and donation.receiver.id,
                donator_id=donation.donator.id,
                amount=donation.amount,
                r_hash=donation.r_hash and donation.r_hash.as_base64,
            )
        )
        return donation

    async def update_donation(self, donation_id: UUID, r_hash: RequestHash):
        await self.execute(
            update(DonationDb)
            .values(r_hash=r_hash.as_base64)
            .where(DonationDb.id == donation_id)
        )

    async def cancel_donation(self, donation_id: UUID) -> RequestHash:
        """
        I'm not sure that this method is needed.
        """
        resp = await self.execute(
            update(DonationDb)
            .values(
                cancelled_at=datetime.utcnow(),
            )
            .where(
                DonationDb.id == donation_id,
            )
            .returning(DonationDb.r_hash)
        )
        return resp.scalar()

    async def donation_paid(self, donation_id: UUID, amount: int, paid_at: datetime):
        resp = await self.execute(
            update(DonationDb)
            .where((DonationDb.id == donation_id) & DonationDb.paid_at.is_(None))
            .values(
                amount=amount,
                paid_at=paid_at,
            )
            .returning(
                DonationDb.id,
                DonationDb.donator_id,
                DonationDb.youtube_channel_id,
                DonationDb.youtube_video_id,
                DonationDb.receiver_id,
                DonationDb.r_hash,
            )
        )
        row = resp.fetchone()
        if row is None:
            # Row could be already updated in another replica
            logger.debug(f"Donation {donation_id} was already handled, skipping")
            return

        donation_id, donator_id, youtube_channel_id, youtube_video_id, receiver_id, r_hash = row
        if youtube_channel_id:
            await self.execute(
                update(YoutubeChannelDb)
                .values(
                    balance=YoutubeChannelDb.balance + amount,
                    total_donated=YoutubeChannelDb.total_donated + amount,
                )
                .where(YoutubeChannelDb.id == youtube_channel_id)
            )
            if youtube_video_id:
                video_update_resp = await self.execute(
                    update(YoutubeVideoDb)
                    .values(total_donated=YoutubeVideoDb.total_donated + amount)
                    .where(YoutubeVideoDb.id == youtube_video_id)
                    .returning(YoutubeVideoDb.video_id)
                )
                (vid,) = video_update_resp.fetchone()
                await self.notify(f'youtube-video:{youtube_video_id}', Notification(id=youtube_video_id, status='OK'))
                await self.notify(f'youtube-video-by-vid:{vid}', Notification(id=vid, status='OK'))
        elif receiver_id:
            await self.execute(
                update(DonatorDb)
                .values(balance=DonatorDb.balance + amount)
                .where(DonatorDb.id == receiver_id)
            )
            await self.notify(f'donator:{receiver_id}', Notification(id=receiver_id, status='OK'))
        else:
            raise ValueError(f"Donation has no youtube_channel_id nor receiver_id: {donation_id}")
        if r_hash is None:
            # donation without invoice, use donator balance
            resp = await self.execute(
                update(DonatorDb)
                .where((DonatorDb.id == donator_id) & (DonatorDb.balance >= amount))
                .values(balance=DonatorDb.balance - amount)
            )
            if resp.rowcount != 1:
                raise NotEnoughBalance(f"Donator {donator_id} hasn't enough money")
        await self.notify(f'donation:{donation_id}', Notification(id=donation_id, status='OK'))

    async def commit(self):
        return await self.session.commit()

    async def rollback(self):
        return await self.session.rollback()

    async def query_status(self):
        response = await self.execute(select(literal('ok')))
        return response.scalars().one()

    async def login_donator(self, donator_id: UUID, key: str | None):
        registered_donator_id = None
        if key is not None:
            resp = await self.execute(
                select(DonatorDb.id).where(DonatorDb.lnauth_pubkey == key)
            )
            registered_donator_id = resp.scalar()
        if registered_donator_id is None:
            # No existing donator with lnauth_pubkey
            resp = await self.execute(
                insert(DonatorDb)
                .values(dict(
                    id=donator_id,
                    lnauth_pubkey=key,
                ))
                .on_conflict_do_update(
                    index_elements=[DonatorDb.id],
                    set_={
                        DonatorDb.lnauth_pubkey: key,
                    },
                    where=(func.coalesce(DonatorDb.lnauth_pubkey, '') != key),
                )
                .returning(DonatorDb.id)
            )
            registered_donator_id: UUID = resp.scalar()
            if registered_donator_id is None:
                registered_donator_id = donator_id
        await self.notify(f'donator:{donator_id}', Notification(
            id=donator_id,
            status='ok',
            message=Credentials(donator_id=registered_donator_id, lnauth_pubkey=key).to_jwt()
        ))

    async def link_youtube_channel(self, youtube_channel: YoutubeChannel, donator: Donator):
        await self.execute(
            insert(YoutubeChannelLink)
            .values(
                youtube_channel_id=youtube_channel.id,
                donator_id=donator.id,
            )
            .on_conflict_do_nothing()
        )

    async def query_youtube_video(self, video_id: str) -> YoutubeVideo:
        resp = await self.execute(
            select(YoutubeVideoDb)
            .where(YoutubeVideoDb.video_id == video_id)
        )
        return YoutubeVideo.from_orm(resp.scalars().one())
