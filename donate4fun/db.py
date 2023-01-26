import logging
from uuid import UUID
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import select, desc, func, text, literal, union, literal_column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound  # noqa - imported from other modules
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .core import ContextualObject
from .models import Donator, Notification, Credentials, Donatee
from .settings import DbSettings
from .db_models import (
    Base, DonatorDb, EmailNotificationDb, YoutubeChannelDb, TwitterAuthorDb, YoutubeChannelLink, TwitterAuthorLink,
    GithubUserLink,
)
from .db_utils import insert_on_conflict_update

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_settings: DbSettings):
        self.engine = create_async_engine(**db_settings.dict())
        self.session_maker = sessionmaker(self.engine, class_=AsyncSession, future=True)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            await conn.run_sync(Base.metadata.create_all)

    async def create_table(self, tablename: str):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[Base.metadata.tables[tablename]])

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


db = ContextualObject("db")


class DbSession:
    def __init__(self, db, session):
        self.db = db
        self.session = session

    def __str__(self):
        return f'{type(self).__name__}<{hex(id(self))}>'

    async def execute(self, query):
        return await self.session.execute(query)

    async def notify(self, channel: str, notification: Notification):
        logger.trace("notify %s %s", channel, notification)
        await self.execute(select(func.pg_notify(channel, notification.json())))

    async def object_changed(self, object_class: str, object_id: UUID, notification: Notification | None = None):
        return await self.notify(f'{object_class}:{object_id}', notification or Notification(id=object_id, status='OK'))

    async def query_donator(self, id: UUID) -> Donator:
        return await self.find_donator(DonatorDb.id == id)

    async def find_donator(self, *where) -> Donator:
        result = await self.execute(
            select(
                *DonatorDb.__table__.columns,
                (
                    func.coalesce(func.bool_or(YoutubeChannelLink.via_oauth), False)
                    | func.coalesce(func.bool_or(TwitterAuthorLink.via_oauth), False)
                    | func.coalesce(func.bool_or(GithubUserLink.via_oauth), False)
                    | DonatorDb.lnauth_pubkey.isnot(None)
                ).label('connected'),
            )
            .outerjoin(YoutubeChannelLink, YoutubeChannelLink.donator_id == DonatorDb.id)
            .outerjoin(TwitterAuthorLink, TwitterAuthorLink.donator_id == DonatorDb.id)
            .outerjoin(GithubUserLink, GithubUserLink.donator_id == DonatorDb.id)
            .where(*where)
            .group_by(DonatorDb.id)
        )
        return Donator(**result.one())

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
            registered_donator_id = await self.save_donator(Donator(id=donator_id, lnauth_pubkey=key))
            if registered_donator_id is None:
                registered_donator_id = donator_id

        return Credentials(donator=registered_donator_id, lnauth_pubkey=key)

    async def save_donator(self, donator: Donator) -> UUID:
        resp = await self.execute(
            insert_on_conflict_update(DonatorDb, donator)
        )
        await self.object_changed('donator', donator.id)
        return resp.scalar()

    async def query_recently_donated_donatees(self, limit=20, limit_days=180) -> list[Donatee]:
        youtube_sq = select(
            YoutubeChannelDb.id,
            literal_column("'youtube'").label('type'),
            YoutubeChannelDb.title.label('title'),
            YoutubeChannelDb.thumbnail_url.label('thumbnail_url'),
            YoutubeChannelDb.total_donated.label('total_donated'),
        )
        twitter_sq = select(
            TwitterAuthorDb.id,
            literal_column("'twitter'").label('type'),
            TwitterAuthorDb.name.label('title'),
            TwitterAuthorDb.profile_image_url.label('thumbnail_url'),
            TwitterAuthorDb.total_donated.label('total_donated'),
        )
        resp = await self.execute(
            union(youtube_sq, twitter_sq)
            .order_by(desc('total_donated'))
            .limit(limit)
        )
        return resp.fetchall()

    async def save_email(self, email: str) -> UUID | None:
        resp = await self.execute(
            insert(EmailNotificationDb)
            .values(
                email=email,
                created_at=datetime.utcnow(),
            )
            .on_conflict_do_nothing()
            .returning(EmailNotificationDb.id)
        )
        return resp.scalar()


class DbSessionWrapper:
    def __init__(self, session: DbSession):
        self.session = session
        self.execute = session.execute
        self.object_changed = session.object_changed
