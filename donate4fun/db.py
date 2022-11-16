import logging
from uuid import UUID
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from sqlalchemy import select, desc, func, text, literal
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker, join
from sqlalchemy.orm.exc import NoResultFound  # noqa - imported from other modules
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .models import Donator, YoutubeChannel, Notification, Credentials
from .settings import DbSettings
from .db_youtube import YoutubeDbMixin
from .db_twitter import TwitterDbMixin, OAuthTokenDbMixin
from .db_donations import DonationsDbMixin
from .db_withdraw import WithdrawalDbMixin
from .db_models import (
    Base, DonatorDb,  DonationDb, EmailNotificationDb, YoutubeChannelDb,
)

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


class DbSession(YoutubeDbMixin, TwitterDbMixin, DonationsDbMixin, WithdrawalDbMixin, OAuthTokenDbMixin):
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

    async def object_changed(self, object_class: str, object_id: UUID):
        return await self.notify(f'{object_class}:{object_id}', Notification(id=object_id, status='OK'))

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
            registered_donator_id = resp.scalar()
            if registered_donator_id is None:
                registered_donator_id = donator_id

        return Credentials(donator=registered_donator_id, lnauth_pubkey=key)

    async def query_recently_donated_donatees(self, limit=20, limit_days=7) -> list[YoutubeChannel]:
        resp = await self.execute(
            select(
                YoutubeChannelDb.id,
                func.max(YoutubeChannelDb.channel_id).label('channel_id'),
                func.max(YoutubeChannelDb.title).label('title'),
                func.max(YoutubeChannelDb.thumbnail_url).label('thumbnail_url'),
                func.sum(DonationDb.amount).label('balance'),
            ).select_from(
                join(YoutubeChannelDb, DonationDb, DonationDb.youtube_channel)
            ).where(
                DonationDb.paid_at > datetime.utcnow() - timedelta(days=limit_days)
            ).group_by(
                YoutubeChannelDb.id
            ).order_by(
                desc('balance')
            ).limit(limit)
        )
        return [YoutubeChannel.from_orm(item) for item in resp.fetchall()]

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
