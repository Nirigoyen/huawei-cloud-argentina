"""Auto-introspect a PostgreSQL schema and emit a Wren MDL project.

There is no built-in `wren` command for DB→MDL introspection (verified), so we
query information_schema + pg_catalog and write models/<table>/metadata.yml +
relationships.yml + wren_project.yml, then `wren context build` compiles them.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import asyncpg
import yaml

from app.wren.types import pg_type_to_mdl

# Schemas to skip when introspecting (unless explicitly requested).
_SYSTEM_SCHEMAS = {"pg_catalog", "information_schema", "pg_toast"}


@dataclass
class Column:
    name: str
    data_type: str
    is_nullable: bool


@dataclass
class ForeignKey:
    from_table: str
    from_column: str
    to_table: str
    to_column: str


@dataclass
class SchemaInfo:
    schema: str
    tables: list[str]
    columns: dict[str, list[Column]]  # table -> columns
    primary_keys: dict[str, str | None]  # table -> pk column (single-col PK only)
    foreign_keys: list[ForeignKey]


async def fetch_schema_info(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    schema: str = "public",
) -> SchemaInfo:
    conn = await asyncpg.connect(host=host, port=port, database=database, user=user, password=password)
    try:
        # Tables
        tables = [
            r["table_name"]
            for r in await conn.fetch(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema = $1 AND table_type = 'BASE TABLE' ORDER BY table_name""",
                schema,
            )
        ]

        # Columns
        col_rows = await conn.fetch(
            """SELECT table_name, column_name, data_type, is_nullable, ordinal_position
               FROM information_schema.columns
               WHERE table_schema = $1 ORDER BY table_name, ordinal_position""",
            schema,
        )
        columns: dict[str, list[Column]] = {t: [] for t in tables}
        for r in col_rows:
            if r["table_name"] in columns:
                columns[r["table_name"]].append(
                    Column(name=r["column_name"], data_type=r["data_type"], is_nullable=r["is_nullable"] == "YES")
                )

        # Primary keys (single-column only)
        pk_rows = await conn.fetch(
            """SELECT kcu.table_name, kcu.column_name
               FROM information_schema.table_constraints tc
               JOIN information_schema.key_column_usage kcu
                 ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
               WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = $1""",
            schema,
        )
        pk_cols: dict[str, list[str]] = {}
        for r in pk_rows:
            pk_cols.setdefault(r["table_name"], []).append(r["column_name"])
        primary_keys = {t: (cols[0] if len(cols) == 1 else None) for t, cols in pk_cols.items()}

        # Foreign keys
        fk_rows = await conn.fetch(
            """SELECT kcu.table_name AS from_table, kcu.column_name AS from_column,
                      ccu.table_name AS to_table, ccu.column_name AS to_column
               FROM information_schema.table_constraints tc
               JOIN information_schema.key_column_usage kcu
                 ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
               JOIN information_schema.constraint_column_usage ccu
                 ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
               WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = $1""",
            schema,
        )
        foreign_keys = [ForeignKey(r["from_table"], r["from_column"], r["to_table"], r["to_column"]) for r in fk_rows]

        return SchemaInfo(
            schema=schema,
            tables=tables,
            columns=columns,
            primary_keys={t: primary_keys.get(t) for t in tables},
            foreign_keys=foreign_keys,
        )
    finally:
        await conn.close()


def write_project(
    project_path: Path,
    project_name: str,
    info: SchemaInfo,
) -> Path:
    """Write wren_project.yml + models/ + relationships.yml for the given schema info."""
    project_path = Path(project_path)
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "models").mkdir(exist_ok=True)

    # wren_project.yml
    with (project_path / "wren_project.yml").open("w") as f:
        yaml.safe_dump(
            {
                "schema_version": 5,
                "name": project_name,
                "catalog": "wren",
                "schema": info.schema,
                "data_source": "postgres",
            },
            f,
            sort_keys=False,
        )

    # models/<table>/metadata.yml
    for table in info.tables:
        model_dir = project_path / "models" / table
        model_dir.mkdir(parents=True, exist_ok=True)
        model = {
            "name": table,
            "description": f"Auto-generated from table {info.schema}.{table}.",
            "table_reference": {"schema": info.schema, "table": table},
            "columns": [
                {"name": c.name, "type": pg_type_to_mdl(c.data_type)} for c in info.columns.get(table, [])
            ],
        }
        pk = info.primary_keys.get(table)
        if pk:
            model["primary_key"] = pk
        with (model_dir / "metadata.yml").open("w") as f:
            yaml.safe_dump(model, f, sort_keys=False)

    # relationships.yml (from FKs)
    relationships = []
    for fk in info.foreign_keys:
        rel_name = f"{fk.from_table}_{fk.to_table}"
        relationships.append(
            {
                "name": rel_name,
                "models": [fk.from_table, fk.to_table],
                "join_type": "MANY_TO_ONE",
                "condition": f"{fk.from_table}.{fk.from_column} = {fk.to_table}.{fk.to_column}",
            }
        )
    with (project_path / "relationships.yml").open("w") as f:
        yaml.safe_dump({"relationships": relationships}, f, sort_keys=False)

    return project_path


async def introspect_and_write(
    project_path: Path,
    project_name: str,
    *,
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    schema: str = "public",
) -> SchemaInfo:
    """Introspect a Postgres schema and write the Wren project files."""
    info = await fetch_schema_info(host, port, database, user, password, schema)
    write_project(project_path, project_name, info)
    return info
