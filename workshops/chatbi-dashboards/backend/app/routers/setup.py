"""Organizer setup: connect PG source, run introspection, modeling CRUD."""
from __future__ import annotations

from uuid import UUID

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PgSource, Workshop
from app.db.session import get_session
from app.wren.introspect import introspect_and_write
from app.wren.project import add_profile, build_project, invalidate_toolkit, project_path_for
from app.wren.types import pg_type_to_mdl  # noqa: F401  (re-exported for reference)

router = APIRouter(prefix="/workshops/{workshop_id}/setup", tags=["setup"])


class SourceBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    host: str
    port: int = 5432
    database: str
    user: str
    password: str
    schema_name: str = Field(default="public", alias="schema")


class ColumnOut(BaseModel):
    name: str
    type: str


class ModelOut(BaseModel):
    name: str
    description: str | None = None
    table_reference: dict
    primary_key: str | None = None
    columns: list[ColumnOut]


class RelationshipOut(BaseModel):
    name: str
    models: list[str]
    join_type: str
    condition: str


class IntrospectionResult(BaseModel):
    models: list[ModelOut]
    relationships: list[RelationshipOut]


class ModelUpdate(BaseModel):
    description: str | None = None


class RelationshipCreate(BaseModel):
    name: str
    models: list[str]
    join_type: str = "MANY_TO_ONE"
    condition: str


async def _load_workshop(wid: UUID, session: AsyncSession) -> Workshop:
    w = await session.get(Workshop, wid)
    if not w:
        raise HTTPException(404, "Workshop not found")
    return w


def _project_path(w: Workshop):
    return project_path_for(str(w.id))


def _read_models(p) -> list[ModelOut]:
    out = []
    models_dir = p / "models"
    if not models_dir.exists():
        return out
    for md in sorted(models_dir.iterdir()):
        meta = md / "metadata.yml"
        if not meta.exists():
            continue
        data = yaml.safe_load(meta.read_text()) or {}
        out.append(
            ModelOut(
                name=data.get("name", md.name),
                description=data.get("description"),
                table_reference=data.get("table_reference", {}),
                primary_key=data.get("primary_key"),
                columns=[ColumnOut(**c) for c in data.get("columns", [])],
            )
        )
    return out


def _read_relationships(p) -> list[RelationshipOut]:
    f = p / "relationships.yml"
    if not f.exists():
        return []
    data = yaml.safe_load(f.read_text()) or {}
    return [RelationshipOut(**r) for r in data.get("relationships", [])]


@router.post("/source", response_model=IntrospectionResult)
async def set_source_and_introspect(
    workshop_id: UUID,
    body: SourceBody,
    session: AsyncSession = Depends(get_session),
):
    w = await _load_workshop(workshop_id, session)
    p = _project_path(w)

    # Store / replace the pg source
    src = await session.scalar(select(PgSource).where(PgSource.workshop_id == w.id))
    if src:
        src.host, src.port, src.database, src.user, src.password, src.schema = (
            body.host, body.port, body.database, body.user, body.password, body.schema_name,
        )
    else:
        src = PgSource(workshop_id=w.id, host=body.host, port=body.port, database=body.database, user=body.user, password=body.password, schema=body.schema_name)
        session.add(src)
    await session.commit()

    # Register a wren profile for this workshop and introspect + build
    profile_name = f"workshop_{w.id}"
    add_profile(profile_name, host=body.host, port=body.port, database=body.database, user=body.user, password=body.password)
    await introspect_and_write(
        p, project_name=f"{w.code}_auto",
        host=body.host, port=body.port, database=body.database, user=body.user, password=body.password, schema=body.schema_name,
    )
    build_project(p)

    return IntrospectionResult(models=_read_models(p), relationships=_read_relationships(p))


@router.get("/models", response_model=list[ModelOut])
async def list_models(workshop_id: UUID, session: AsyncSession = Depends(get_session)):
    w = await _load_workshop(workshop_id, session)
    return _read_models(_project_path(w))


@router.put("/models/{model_name}", response_model=ModelOut)
async def update_model(workshop_id: UUID, model_name: str, body: ModelUpdate, session: AsyncSession = Depends(get_session)):
    w = await _load_workshop(workshop_id, session)
    p = _project_path(w)
    meta = p / "models" / model_name / "metadata.yml"
    if not meta.exists():
        raise HTTPException(404, "Model not found")
    data = yaml.safe_load(meta.read_text()) or {}
    if body.description is not None:
        data["description"] = body.description
    meta.write_text(yaml.safe_dump(data, sort_keys=False))
    build_project(p)
    return ModelOut(name=data.get("name", model_name), description=data.get("description"), table_reference=data.get("table_reference", {}), primary_key=data.get("primary_key"), columns=[ColumnOut(**c) for c in data.get("columns", [])])


@router.get("/relationships", response_model=list[RelationshipOut])
async def list_relationships(workshop_id: UUID, session: AsyncSession = Depends(get_session)):
    w = await _load_workshop(workshop_id, session)
    return _read_relationships(_project_path(w))


@router.post("/relationships", response_model=list[RelationshipOut])
async def add_relationship(workshop_id: UUID, body: RelationshipCreate, session: AsyncSession = Depends(get_session)):
    w = await _load_workshop(workshop_id, session)
    p = _project_path(w)
    f = p / "relationships.yml"
    data = yaml.safe_load(f.read_text()) if f.exists() else {}
    rels = (data or {}).get("relationships", [])
    rels.append(body.model_dump())
    f.write_text(yaml.safe_dump({"relationships": rels}, sort_keys=False))
    build_project(p)
    return _read_relationships(p)


@router.delete("/relationships/{name}", response_model=list[RelationshipOut])
async def delete_relationship(workshop_id: UUID, name: str, session: AsyncSession = Depends(get_session)):
    w = await _load_workshop(workshop_id, session)
    p = _project_path(w)
    f = p / "relationships.yml"
    data = yaml.safe_load(f.read_text()) if f.exists() else {}
    rels = [r for r in (data or {}).get("relationships", []) if r.get("name") != name]
    f.write_text(yaml.safe_dump({"relationships": rels}, sort_keys=False))
    build_project(p)
    return _read_relationships(p)
