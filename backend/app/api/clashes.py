"""
clashes.py — Router clash management.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.schemas.clash import ClashRecordCreate, ClashRecordUpdate
from app.services.auth import get_current_user
from app.services.clash_manager import (
    create_clash,
    get_clash_summary,
    resolve_clash,
)

router = APIRouter()


@router.get("/projects/{project_id}/clashes")
def get_clashes(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează sumar clash-uri proiect."""
    return get_clash_summary(db, project_id)


@router.post("/projects/{project_id}/clashes")
def add_clash(
    project_id: int,
    body: ClashRecordCreate,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creează o înregistrare clash."""
    result = create_clash(
        db, project_id,
        discipline_a=body.discipline_a,
        discipline_b=body.discipline_b,
        severity=body.severity,
        description=body.description,
        assigned_to_role=body.assigned_to_role,
    )
    db.commit()
    return result


@router.post("/clashes/{clash_id}/resolve")
def resolve_clash_endpoint(
    clash_id: int,
    body: ClashRecordUpdate,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rezolvă un clash."""
    result = resolve_clash(db, clash_id, resolution_note=body.resolution_note)
    db.commit()
    return result
