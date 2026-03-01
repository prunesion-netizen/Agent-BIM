"""
project_status.py — Serviciu pentru tranzitiile de status ale proiectelor BIM.

Reguli de tranzitie:
  - on_context_saved: NEW -> CONTEXT_DEFINED (restul raman neschimbate)
  - on_bep_generated: Orice -> BEP_GENERATED
  - on_bep_verified:  Daca orice check are "fail" -> BEP_VERIFIED_PARTIAL
                      Altfel -> BEP_VERIFIED_OK
"""

from sqlalchemy.orm import Session

from app.schemas.project import ProjectStatus
from app.repositories.projects_repository import get_project, update_project_status


def on_context_saved(db: Session, project_id: int) -> None:
    """Apelat dupa salvarea ProjectContext. NEW -> CONTEXT_DEFINED."""
    project = get_project(db, project_id)
    if project and project.status == ProjectStatus.NEW:
        update_project_status(db, project_id, ProjectStatus.CONTEXT_DEFINED)


def on_bep_generated(db: Session, project_id: int) -> None:
    """Apelat dupa generarea BEP. Orice status -> BEP_GENERATED."""
    update_project_status(db, project_id, ProjectStatus.BEP_GENERATED)


def on_bep_verified(db: Session, project_id: int, checks: list[dict]) -> None:
    """Apelat dupa verificarea BEP vs Model.

    Daca orice check are status "fail" -> BEP_VERIFIED_PARTIAL
    Altfel -> BEP_VERIFIED_OK
    """
    has_fail = any(c.get("status") == "fail" for c in checks)
    new_status = (
        ProjectStatus.BEP_VERIFIED_PARTIAL if has_fail
        else ProjectStatus.BEP_VERIFIED_OK
    )
    update_project_status(db, project_id, new_status)
