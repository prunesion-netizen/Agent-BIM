"""
projects_dashboard.py — Endpoint agregat pentru Dashboard Proiecte BIM.

GET /api/projects/overview — returnează ProjectOverview per proiect.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import GeneratedDocumentModel, ProjectModel
from app.schemas.project import ProjectOverview
from app.services.project_health import compute_project_health

router = APIRouter()


def _get_latest_doc(
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


def _build_overview(db: Session, project: ProjectModel) -> ProjectOverview:
    """Construiește ProjectOverview din ProjectModel + documente agregate."""
    # Ultimul BEP
    bep_doc = _get_latest_doc(db, project.id, "bep")
    has_bep = bep_doc is not None
    bep_version = bep_doc.version if bep_doc else None
    last_bep_at = (
        bep_doc.created_at.isoformat() if bep_doc and bep_doc.created_at else None
    )

    # Ultimul raport de verificare
    verif_doc = _get_latest_doc(db, project.id, "bep_verification_report")
    has_verifications = verif_doc is not None
    last_verif_at = (
        verif_doc.created_at.isoformat()
        if verif_doc and verif_doc.created_at
        else None
    )
    last_verif_status = verif_doc.summary_status if verif_doc else None
    last_verif_fail = verif_doc.fail_count if verif_doc else None
    last_verif_warn = verif_doc.warning_count if verif_doc else None

    # Health score
    health = compute_project_health(db, project.id)
    health_score = health.get("score", 0) if "error" not in health else 0
    has_ifc = health.get("has_ifc", False)
    health_alerts = health.get("alerts", [])

    return ProjectOverview(
        id=project.id,
        name=project.name,
        code=project.code,
        client_name=project.client_name,
        project_type=project.project_type,
        status=project.status,
        has_bep=has_bep,
        bep_version=bep_version,
        last_bep_generated_at=last_bep_at,
        has_verifications=has_verifications,
        last_verification_at=last_verif_at,
        last_verification_status=last_verif_status,
        last_verification_fail_count=last_verif_fail,
        last_verification_warning_count=last_verif_warn,
        health_score=health_score,
        has_ifc=has_ifc,
        health_alerts=health_alerts,
        updated_at=project.updated_at.isoformat() if project.updated_at else "",
    )


@router.get("/projects/overview", response_model=list[ProjectOverview])
def api_projects_overview(db: Session = Depends(get_db)):
    """Dashboard overview — toate proiectele cu date agregate BEP + verificări."""
    projects = (
        db.query(ProjectModel)
        .order_by(desc(ProjectModel.updated_at))
        .all()
    )
    return [_build_overview(db, p) for p in projects]
