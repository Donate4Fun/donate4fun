from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import insert


def insert_on_conflict_update(table, obj, index_field):
    fields = [(key, value) for key, value in obj.dict().items() if key not in (index_field.name, 'id')]
    return (
        insert(table)
        .values(obj.dict())
        .on_conflict_do_update(
            index_elements=[index_field],
            set_={getattr(table, key): value for key, value in fields},
            where=or_(*[
                (getattr(table, key).is_(None) != (value is None))
                | (getattr(table, key) != value) for key, value in fields
            ]),
        )
        .returning(table.id)
    )
