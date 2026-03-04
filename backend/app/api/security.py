"""
security.py — Router securitate informații (ISO 19650-5).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.services.auth import get_current_user
from app.services.security_plan import (
    generate_security_plan,
    get_security_classification,
)

router = APIRouter()


@router.post("/projects/{project_id}/generate-security-plan")
def generate_security(
    project_id: int,
    classification_level: str = Query("standard"),
    sensitive_areas: str | None = Query(None),
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generează plan securitate."""
    result = generate_security_plan(
        db, project_id,
        classification_level=classification_level,
        sensitive_areas=sensitive_areas,
    )
    db.commit()
    return result


@router.get("/projects/{project_id}/security")
def get_security(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează clasificarea securitate curentă."""
    return get_security_classification(db, project_id)
