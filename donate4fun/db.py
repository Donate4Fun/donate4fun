import asyncio
import logging
from uuid import UUID
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime

from sqlalchemy import select, desc, update, Column, TIMESTAMP, String, BigInteger, ForeignKey, func
from sqlalchemy.dialects.postgresql import insert, UUID as Uuid
from sqlalchemy.orm import sessionmaker, joinedload, selectinload, contains_eager, declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .settings import settings
from .models import Donation

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

    donator = relationship(DonatorDb, back_populates="donations", lazy='joined')
    youtube_channel = relationship(YoutubeChannelDb, back_populates="donations", lazy='joined')


db_session_var = ContextVar('db-session')


class Database:
    def __init__(self):
        self.engine = create_async_engine(settings().db.dsn, echo=settings().db.echo)
        self.session_maker = sessionmaker(self.engine, class_=AsyncSession, future=True)

    async def load_tables(self):
        Base.registry.configure()  # Create backrefs

    async def create_tables(self, metadata):
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    @asynccontextmanager
    async def acquire_session(self) -> 'DbSession':
        try:
            db_session = db_session_var.get()
        except LookupError:
            async with self.session_maker.begin() as session:
                await session.connection()  # Force BEGIN
                token = db_session_var.set(DbSession(self, session))
                db_session = db_session_var.get()
                try:
                    yield db_session
                finally:
                    db_session_var.reset(token)
        else:
            yield db_session

    @asynccontextmanager
    async def rollback(self):
        async with self.acquire_session() as session:
            try:
                yield session
            finally:
                await session.session.rollback()


class DbSession:
    def __init__(self, db, session):
        self.db = db
        self.session = session

    async def execute(self, query):
        return await self.session.execute(query)

    @asynccontextmanager
    async def transaction(self):
        async with self.session.begin_nested() as transaction:
            yield transaction

    async def query_donatee(self, donatee_id: UUID):
        return await self.query_donations(DonationDb.youtube_channel_id == donatee_id)

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

    async def query_donation(self, r_hash: str | None = None, id: UUID | None = None) -> Donation:
        result = await self.execute(
            select(DonationDb)
            .where(
                (DonationDb.r_hash == r_hash) if r_hash else (DonationDb.id == str(id))
            )
        )
        return Donation.from_orm(result.scalar())

    async def get_or_create_youtube_channel(self, channel_id: str, title: str, thumbnail_url: str) -> UUID:
        resp = await self.execute(
            insert(YoutubeChannelDb)
            .values(title=title, thumbnail_url=thumbnail_url, channel_id=channel_id)
            .on_conflict_do_nothing()
            .returning(YoutubeChannelDb.id)
        )
        donatee_id: UUID = resp.scalar()
        if donatee_id is None:
            resp = await self.execute(select(YoutubeChannelDb).where(YoutubeChannelDb.channel_id == channel_id))
            donatee_id = resp.scalar().id
        return donatee_id

    async def create_donation(self, donator_id: UUID, youtube_channel_id: UUID, amount: int, r_hash: str):
        async with self.transaction():
            resp = await self.execute(
                insert(DonationDb)
                .values(
                    amount=amount,
                    r_hash=r_hash,
                    donator_id=str(donator_id),
                    youtube_channel_id=str(youtube_channel_id),
                    created_at=datetime.utcnow(),
                )
                .returning(DonationDb.id)
            )
            donation_id: UUID = resp.scalar()
        return await self.query_donation(id=donation_id)

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
        donation_id: UUID = resp.scalar()
        await self.notify('"donation-paid"', donation_id)

    async def notify(self, channel: str, message: str):
        await self.execute(f"NOTIFY {channel}, '{message}';")

    async def listen(self, channel: str):
        queue = asyncio.Queue()
        connection = await self.session.connection()
        raw_connection = await connection.get_raw_connection()
        asyncpg_connection = raw_connection.connection._connection
        await asyncpg_connection.add_listener(channel, queue.put)
        logger.debug(f"Added listener for '{channel}'")
        yield None
        while True:
            try:
                yield await queue.get()
            except StopIteration:
                break
            finally:
                await asyncpg_connection.remove_listener(channel, queue.put)

    async def listen_for_donations(self):
        async for msg in self.listen('"donation-paid"'):
            if msg is None:
                continue
            breakpoint()
            yield UUID(msg)


@asynccontextmanager
async def load_db():
    db = Database()
    await db.load_tables()
    yield db
