"""
projects_repository.py — CRUD PostgreSQL pentru proiecte, context-uri și documente.

Toate funcțiile primesc `db: Session` ca prim parametru.
"""

from __future__ import annotations

import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.sql_models import (
    GeneratedDocumentModel,
    ProjectContextModel,
    ProjectModel,
)
from app.schemas.project import ProjectCreate
from app.schemas.project_context import ProjectContext


# ── CRUD Projects ─────────────────────────────────────────────────────────────

def create_project(db: Session, data: ProjectCreate) -> ProjectModel:
    """Creează un proiect nou din schema Pydantic ProjectCreate."""
    project = ProjectModel(
        name=data.name,
        code=data.code,
        client_name=data.client_name,
        project_type=data.project_type,
    )
    db.add(project)
    db.flush()
    return project


def get_project(db: Session, project_id: int) -> ProjectModel | None:
    """Returnează un proiect după ID."""
    return db.get(ProjectModel, project_id)


def list_projects(db: Session) -> list[ProjectModel]:
    """Returnează toate proiectele, ordonate după created_at desc."""
    return (
        db.query(ProjectModel)
        .order_by(desc(ProjectModel.created_at))
        .all()
    )


def update_project_status(
    db: Session, project_id: int, new_status: str
) -> ProjectModel | None:
    """Actualizează statusul unui proiect."""
    project = db.get(ProjectModel, project_id)
    if project:
        project.status = new_status
        project.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.flush()
    return project


# ── CRUD ProjectContext ──────────────────────────────────────────────────────

def save_project_context(
    db: Session, project_id: int, context: ProjectContext
) -> ProjectContextModel:
    """Salvează un snapshot al ProjectContext (Pydantic) ca JSONB."""
    entry = ProjectContextModel(
        project_id=project_id,
        context_json=context.model_dump(mode="json"),
    )
    db.add(entry)
    db.flush()
    return entry


def get_latest_project_context(
    db: Session, project_id: int
) -> ProjectContextModel | None:
    """Returnează cel mai recent ProjectContext pentru un proiect."""
    return (
        db.query(ProjectContextModel)
        .filter(ProjectContextModel.project_id == project_id)
        .order_by(desc(ProjectContextModel.created_at))
        .first()
    )


# ── CRUD GeneratedDocument ───────────────────────────────────────────────────

def save_generated_document(
    db: Session,
    project_id: int,
    doc_type: str,
    title: str,
    content_markdown: str,
    version: str | None = None,
) -> GeneratedDocumentModel:
    """Salvează un document generat (BEP, raport verificare, etc.)."""
    doc = GeneratedDocumentModel(
        project_id=project_id,
        doc_type=doc_type,
        title=title,
        content_markdown=content_markdown,
        version=version,
    )
    db.add(doc)
    db.flush()
    return doc


def get_latest_generated_document(
    db: Session, project_id: int, doc_type: str
) -> GeneratedDocumentModel | None:
    """Returnează cel mai recent document de un anumit tip pentru un proiect."""
    return (
        db.query(GeneratedDocumentModel)
        .filter(
            GeneratedDocumentModel.project_id == project_id,
            GeneratedDocumentModel.doc_type == doc_type,
        )
        .order_by(desc(GeneratedDocumentModel.created_at))
        .first()
    )


def list_generated_documents(
    db: Session, project_id: int
) -> list[GeneratedDocumentModel]:
    """Returnează toate documentele unui proiect."""
    return (
        db.query(GeneratedDocumentModel)
        .filter(GeneratedDocumentModel.project_id == project_id)
        .order_by(desc(GeneratedDocumentModel.created_at))
        .all()
    )
