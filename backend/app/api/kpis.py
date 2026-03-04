"""
kpis.py — Router KPI tracking.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.services.auth import get_current_user
from app.services.kpi_tracker import get_kpi_dashboard

router = APIRouter()


@router.get("/projects/{project_id}/kpis")
def get_kpis(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează dashboard KPI proiect."""
    result = get_kpi_dashboard(db, project_id)
    db.commit()
    return result
