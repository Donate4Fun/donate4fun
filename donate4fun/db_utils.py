from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect

from .models import BaseModel


def insert_on_conflict_update(table, obj: BaseModel, *index_fields):
    """
    Returns INSERT ... ON CONFLICT (*index_fields) DO UPDATE SET ...; query.
    If index_fields are empty then uses primary key.
    """
    # FIXME: move default_persisten_fields to model declaration
    default_persisten_fields = ['id', 'total_donated', 'balance']
    persistent_fields = {
        field.name for field in table.__table__.c
        if field.name in default_persisten_fields or field in index_fields
    }
    values = [(field, getattr(obj, field.name)) for field in table.__table__.c if field.name not in persistent_fields]
    return (
        insert(table)
        .values({field.name: getattr(obj, field.name) for field in table.__table__.c})
        .on_conflict_do_update(
            index_elements=index_fields or inspect(table).primary_key,
            set_={field: value for field, value in values},
            where=or_(*[
                (field.is_(None) != (value is None))
                | (field != value) for field, value in values
            ]),
        )
        .returning(table.id)
    )
