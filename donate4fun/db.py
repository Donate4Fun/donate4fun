from functools import wraps
from uuid import UUID
from contextlib import asynccontextmanager
from contextvars import ContextVar
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.automap import automap_base
from .settings import settings
from .models import Donation, DonationRequest

DonationTable = None


def withconnection(method):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        async with self.engine.begin() as conn:
            return await method(self, conn, *args, **kwargs)
    return wrapper


class Database:
    def __init__(self):
        self.engine = create_async_engine(settings().db.dsn, echo=settings().db.echo)

    async def load_tables(self):
        async with self.engine.begin() as conn:
            metadata = MetaData()
            await conn.run_sync(metadata.reflect)
        self.donation = metadata.tables['donation']
        base = automap_base(metadata=metadata)
        base.prepare()
        self.Donation = base.classes.donation

    @withconnection
    async def query_donations(self, conn, donatee: str | None = None, donator: str | None = None):
        query = self.donation.select().where((self.donation.c.donatee == donatee) | (self.donation.c.donator == donator))
        result = await conn.execute(query)
        return [Donation(**row) for row in result.mappings().fetchall()]

    @withconnection
    async def query_donation(self, conn, r_hash: str | None = None, id: UUID | None = None) -> Donation | None:
        result = await conn.execute(self.donation.select().where(
            (self.donation.c.r_hash == r_hash) | (self.donation.c.id == str(id)))
        )
        row = result.mappings().fetchone()
        return row and Donation(**row)

    @withconnection
    async def create_donation(self, conn, amount: int, req: DonationRequest) -> Donation:
        result = await conn.execute(self.donation.insert().values(
            amount=amount,
            r_hash=req.r_hash,
            donatee=req.donatee,
            donator=req.donator,
            trigger=req.trigger,
            message=req.message,
        ).return_defaults())
        return Donation(amount=amount, **req.to_dict(), **result.returned_defaults)


db_var = ContextVar('db')


def db():
    return db_var.get()


@asynccontextmanager
async def init_db():
    token = db_var.set(Database())
    try:
        await db_var.get().load_tables()
        yield
    except Exception:
        db_var.reset(token)
