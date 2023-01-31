from datetime import datetime
from uuid import UUID

from sqlalchemy import select, desc, union, literal_column
from sqlalchemy.dialects.postgresql import insert

from .models import Donatee
from .db import DbSessionWrapper
from .db_models import EmailNotificationDb
from .db_libs import YoutubeDbLib, TwitterDbLib, GithubDbLib


class OtherDbLib(DbSessionWrapper):
    def donatees_subquery(self):
        return union(*[
            select(
                db_lib.db_model.id,
                db_lib.db_model.balance,
                db_lib.db_model.total_donated,
                getattr(db_lib.db_model, db_lib.db_model_name_column).label('title'),
                getattr(db_lib.db_model, db_lib.db_model_thumbnail_url_column).label('thumbnail_url'),
                literal_column(f"'{db_lib.name}'").label('type'),
            )
            for db_lib in [YoutubeDbLib, TwitterDbLib, GithubDbLib]
        ]).subquery()

    async def query_recently_donated_donatees(self, limit=20, limit_days=180) -> list[Donatee]:
        donatees = self.donatees_subquery()
        resp = await self.execute(
            select(donatees)
            .order_by(desc(donatees.c.total_donated))
            .limit(limit)
        )
        return [Donatee.from_orm(item) for item in resp.fetchall()]

    async def query_top_unclaimed_donatees(self, limit=20, offset=0) -> list[Donatee]:
        donatees = self.donatees_subquery()
        resp = await self.execute(
            select(donatees)
            .where(donatees.c.balance > 0)
            .order_by(desc(donatees.c.balance))
        )
        return [Donatee.from_orm(item) for item in resp.fetchall()]

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
