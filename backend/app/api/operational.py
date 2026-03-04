"""
operational.py — Router handover checklist (ISO 19650-3).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.services.auth import get_current_user
from app.services.handover import (
    generate_handover_checklist,
    get_handover_status,
    toggle_handover_item,
)

router = APIRouter()


@router.post("/projects/{project_id}/generate-handover")
def generate_handover(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generează handover checklist."""
    result = generate_handover_checklist(db, project_id)
    db.commit()
    return result


@router.get("/projects/{project_id}/handover")
def get_handover(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează statusul handover checklist."""
    return get_handover_status(db, project_id)


@router.post("/handover-items/{item_id}/toggle")
def toggle_item(
    item_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle completare element handover."""
    result = toggle_handover_item(db, item_id, completed_by=user.username)
    db.commit()
    return result
