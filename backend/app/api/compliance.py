"""
compliance.py — Router conformitate ISO 19650 completă.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.services.auth import get_current_user
from app.services.iso_compliance_checker import check_full_compliance

router = APIRouter()


@router.get("/projects/{project_id}/iso-compliance")
def get_iso_compliance(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verifică conformitatea completă ISO 19650 pentru un proiect."""
    return check_full_compliance(db, project_id)
