import asyncio
import logging
import uuid
from uuid import UUID
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import select, desc, update, Column, TIMESTAMP, String, BigInteger, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import insert, UUID as Uuid
from sqlalchemy.orm import sessionmaker, joinedload, selectinload, contains_eager, declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .models import Donation
from .types import RequestHash
from .settings import DbSettings

logger = logging.getLogger(__name__)


Base = declarative_base()


class YoutubeChannelDb(Base):
    __tablename__ = 'youtube_channel'

    id = Column(Uuid, primary_key=True, server_default=func.uuid_generate_v4())
    channel_id = Column(String, unique=True, nullable=False)
    title = Column(String)
    thumbnail_url = Column(String)

    donations = relationship("DonationDb", back_populates="youtube_channel")


class DonatorDb(Base):
    __tablename__ = 'donator'

    id = Column(Uuid, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String)
    avatar_url = Column(String)

    donations = relationship("DonationDb", back_populates="donator")


class DonationDb(Base):
    __tablename__ = 'donation'

    id = Column(Uuid, primary_key=True, server_default=func.uuid_generate_v4())
    r_hash = Column(String, unique=True, nullable=False)
    amount = Column(BigInteger, nullable=False)
    donator_id = Column(Uuid, ForeignKey(DonatorDb.id), nullable=False)
    youtube_channel_id = Column(Uuid, ForeignKey(YoutubeChannelDb.id), nullable=False)
    claimed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    paid_at = Column(TIMESTAMP)
    cancelled_at = Column(TIMESTAMP)

    donator = relationship(DonatorDb, back_populates="donations", lazy='joined')
    youtube_channel = relationship(YoutubeChannelDb, back_populates="donations", lazy='joined')


Base.registry.configure()  # Create backrefs


class Database:
    def __init__(self, db_settings: DbSettings):
        self.engine = create_async_engine(db_settings.dsn, echo=db_settings.echo, isolation_level=db_settings.isolation_level)
        self.session_maker = sessionmaker(self.engine, class_=AsyncSession, future=True)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION "uuid-ossp"'))
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text(f'ALTER TABLE {DonationDb.__table__} DROP CONSTRAINT donation_donator_id_fkey'))

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
        async with self.session_maker() as session, session.begin():
            db_session = DbSession(self, session)
            await session.connection(execution_options=dict(logging_token=id(db_session)))
            yield db_session

    @asynccontextmanager
    async def pubsub(self) -> 'PubSubSession':
        async with self.session_maker() as session, session.begin():
            pubsub = PubSubSession(self, session)
            await session.connection(execution_options=dict(logging_token=id(pubsub)))
            yield pubsub

    @asynccontextmanager
    async def transaction(self):
        async with self.session() as session, session.transaction():
            yield session


class BaseDbSession:
    def __init__(self, db, session):
        self.db = db
        self.session = session

    async def execute(self, query):
        return await self.session.execute(query)


class DbSession(BaseDbSession):
    @asynccontextmanager
    async def transaction(self):
        if self.session.in_transaction():
            async with self.savepoint():
                yield self
        else:
            async with self.session.begin():
                yield self

    @asynccontextmanager
    async def savepoint(self):
        async with self.session.begin_nested():
            yield self

    async def query_donatee(self, donatee_id: UUID):
        return await self.query_donations(DonationDb.youtube_channel_id == str(donatee_id))

    async def query_donator(self, donator_id: UUID):
        result = await self.execute(
            select(DonatorDb)
            .options(
                joinedload(DonatorDb.donations).options(
                    selectinload(DonationDb.youtube_channel),
                ),
                contains_eager('donations.donator'),  # Backref to donator
            )
            .where(DonatorDb.id == donator_id)
        )
        return result.scalar()

    async def query_donations(self, where):
        result = await self.execute(
            select(DonationDb)
            .where(where)
            .order_by(desc(DonationDb.paid_at))
        )
        return [Donation.from_orm(obj) for obj in result.unique().scalars()]

    async def query_recent_donations(self):
        return await self.query_donations(DonationDb.paid_at.isnot(None))

    async def query_donation(self, *, r_hash: str | None = None, id: UUID | None = None) -> Donation:
        result = await self.execute(
            select(DonationDb)
            .where(
                (DonationDb.r_hash == r_hash) if r_hash else (DonationDb.id == str(id))
            )
        )
        return Donation.from_orm(result.scalars().one())

    async def get_or_create_youtube_channel(self, channel_id: str, title: str, thumbnail_url: str) -> UUID:
        resp = await self.execute(
            insert(YoutubeChannelDb)
            .values(title=title, thumbnail_url=thumbnail_url, channel_id=channel_id, id=str(uuid.uuid4()))
            .on_conflict_do_nothing()
            .returning(YoutubeChannelDb.id)
        )
        donatee_id: UUID = resp.scalar()
        if donatee_id is None:
            resp = await self.execute(select(YoutubeChannelDb).where(YoutubeChannelDb.channel_id == channel_id))
            donatee_id = resp.scalars().one().id
        return donatee_id

    async def create_donation(self, donator_id: UUID, youtube_channel_id: UUID, amount: int, r_hash: str):
        resp = await self.execute(
            insert(DonationDb)
            .values(
                amount=amount,
                r_hash=r_hash,
                donator_id=str(donator_id),
                youtube_channel_id=str(youtube_channel_id),
                created_at=datetime.utcnow(),
                id=str(uuid.uuid4()),  # We do not use pg default value to be able to monkeypatch uuid4 in tests
            )
            .returning(DonationDb.id)
        )
        donation_id: UUID = resp.scalar()
        return await self.query_donation(id=donation_id)

    async def cancel_donation(self, donation_id: UUID) -> RequestHash:
        resp = await self.execute(
            update(DonationDb)
            .values(
                cancelled_at=datetime.utcnow(),
            )
            .where(
                DonationDb.id == str(donation_id),
            )
            .returning(DonationDb.r_hash)
        )
        return resp.scalar()

    async def donation_paid(self, r_hash: str, amount: int, paid_at: datetime):
        resp = await self.execute(
            update(DonationDb)
            .where((DonationDb.r_hash == r_hash) & DonationDb.paid_at.is_(None))
            .values(
                amount=amount,
                paid_at=paid_at,
            )
            .returning(DonationDb.id)
        )
        donation_id: UUID = resp.scalars().one()
        async with self.db.pubsub() as pub:
            await pub.notify_donation_paid(donation_id)

    async def commit(self):
        return await self.session.commit()

    async def rollback(self):
        return await self.session.rollback()


class PubSubSession(BaseDbSession):
    async def notify_donation_paid(self, donation_id: UUID):
        await self.notify('donation_paid', str(donation_id))

    async def notify(self, channel: str, message: str):
        await self.execute(select(func.pg_notify(channel, message)))

    async def listen(self, channel: str):
        connection = await self.session.connection()
        raw_connection = await connection.get_raw_connection()
        asyncpg_connection = raw_connection.connection._connection
        queue = asyncio.Queue()

        async def listener(con_ref, pid, channel, payload):
            await queue.put(payload)

        await asyncpg_connection.add_listener(channel, listener)
        logger.debug(f"[{id(self)}] Added listener for '{channel}'")
        try:
            yield None
            while True:
                msg = await queue.get()
                logger.debug(f"[{id(self)}] Notification from '{channel}': {msg}")
                yield msg
        finally:
            await asyncpg_connection.remove_listener(channel, listener)

    async def listen_for_donations(self):
        async for msg in self.listen('donation_paid'):
            yield msg and UUID(msg)


@asynccontextmanager
async def load_db(db_settings):
    db = Database(db_settings)
    yield db
