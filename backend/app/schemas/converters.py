"""
converters.py — Funcții de conversie SQLAlchemy Model → Pydantic Schema.

Folosite în endpoint-urile API pentru a transforma obiectele ORM
în scheme Pydantic de răspuns (ProjectRead, ProjectContextRead, etc.).
"""

from __future__ import annotations

from app.models.sql_models import (
    GeneratedDocumentModel,
    ProjectContextModel,
    ProjectModel,
)
from app.schemas.project import (
    GeneratedDocumentRead,
    LatestVerificationInfo,
    ProjectContextRead,
    ProjectOverviewItem,
    ProjectRead,
    VerificationHistoryItem,
)


def project_model_to_read(p: ProjectModel) -> ProjectRead:
    """Convertește un ProjectModel SQLAlchemy în ProjectRead Pydantic."""
    return ProjectRead(
        id=p.id,
        name=p.name,
        code=p.code,
        client_name=p.client_name,
        project_type=p.project_type,
        description=p.description,
        status=p.status,
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
    )


def context_model_to_read(c: ProjectContextModel) -> ProjectContextRead:
    """Convertește un ProjectContextModel SQLAlchemy în ProjectContextRead Pydantic."""
    return ProjectContextRead(
        id=c.id,
        project_id=c.project_id,
        context_json=c.context_json,
        created_at=c.created_at.isoformat() if c.created_at else "",
    )


def document_model_to_read(d: GeneratedDocumentModel) -> GeneratedDocumentRead:
    """Convertește un GeneratedDocumentModel SQLAlchemy în GeneratedDocumentRead Pydantic."""
    return GeneratedDocumentRead(
        id=d.id,
        project_id=d.project_id,
        doc_type=d.doc_type,
        title=d.title,
        content_markdown=d.content_markdown,
        version=d.version,
        summary_status=d.summary_status,
        fail_count=d.fail_count,
        warning_count=d.warning_count,
        created_at=d.created_at.isoformat() if d.created_at else "",
    )


def document_model_to_history_item(d: GeneratedDocumentModel) -> VerificationHistoryItem:
    """Convertește un GeneratedDocumentModel în VerificationHistoryItem (fără content)."""
    return VerificationHistoryItem(
        id=d.id,
        title=d.title,
        created_at=d.created_at.isoformat() if d.created_at else "",
        summary_status=d.summary_status,
        fail_count=d.fail_count,
        warning_count=d.warning_count,
    )


def project_to_overview_item(
    p: ProjectModel,
    has_context: bool,
    has_bep: bool,
    bep_version: str | None,
    verification_count: int,
    latest_verification: GeneratedDocumentModel | None,
) -> ProjectOverviewItem:
    """Convertește ProjectModel + date agregate → ProjectOverviewItem pentru Dashboard."""
    latest_verif_info = None
    if latest_verification:
        latest_verif_info = LatestVerificationInfo(
            summary_status=latest_verification.summary_status,
            fail_count=latest_verification.fail_count,
            warning_count=latest_verification.warning_count,
            created_at=latest_verification.created_at.isoformat()
            if latest_verification.created_at
            else "",
        )

    return ProjectOverviewItem(
        id=p.id,
        name=p.name,
        code=p.code,
        client_name=p.client_name,
        project_type=p.project_type,
        status=p.status,
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
        has_context=has_context,
        has_bep=has_bep,
        bep_version=bep_version,
        verification_count=verification_count,
        latest_verification=latest_verif_info,
    )
