"""Map PostgreSQL data types to Wren MDL types."""
from __future__ import annotations

# MDL accepts: integer, bigint, double, varchar, boolean, date, timestamp (others fall back to varchar).
_MAP = {
    # integers
    "smallint": "integer",
    "integer": "integer",
    "int": "integer",
    "int2": "integer",
    "int4": "integer",
    "bigint": "bigint",
    "int8": "bigint",
    # floats
    "real": "double",
    "float4": "double",
    "double precision": "double",
    "float8": "double",
    "numeric": "double",
    "decimal": "double",
    # bool
    "boolean": "boolean",
    "bool": "boolean",
    # text
    "character varying": "varchar",
    "varchar": "varchar",
    "character": "varchar",
    "char": "varchar",
    "text": "varchar",
    "name": "varchar",
    # time
    "date": "date",
    "timestamp without time zone": "timestamp",
    "timestamp with time zone": "timestamp",
    "timestamp": "timestamp",
    "timestamptz": "timestamp",
    "time without time zone": "varchar",
    "time with time zone": "varchar",
    # json / uuid / others -> varchar
    "json": "varchar",
    "jsonb": "varchar",
    "uuid": "varchar",
    "bytea": "varchar",
    "money": "double",
}


def pg_type_to_mdl(pg_type: str) -> str:
    """Map a Postgres data_type (from information_schema.columns) to an MDL type."""
    if not pg_type:
        return "varchar"
    key = pg_type.lower().strip()
    # Handle "character varying(n)" style if the catalog returns it with length.
    key_bare = key.split("(", 1)[0].strip()
    return _MAP.get(key) or _MAP.get(key_bare) or "varchar"
