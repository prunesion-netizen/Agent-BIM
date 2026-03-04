"""
raci.py — Router RACI Matrix.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import RaciEntryModel, UserModel
from app.schemas.raci import RaciEntryCreate
from app.services.auth import get_current_user
from app.services.raci_generator import generate_raci_matrix, get_raci_matrix

router = APIRouter()


@router.post("/projects/{project_id}/generate-raci")
def generate_raci_endpoint(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generează matrice RACI din ProjectContext."""
    result = generate_raci_matrix(db, project_id)
    db.commit()
    return result


@router.get("/projects/{project_id}/raci")
def get_raci_endpoint(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează matricea RACI curentă."""
    return get_raci_matrix(db, project_id)


@router.post("/projects/{project_id}/raci/entries")
def add_raci_entry(
    project_id: int,
    body: RaciEntryCreate,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Adaugă o intrare RACI manuală."""
    entry = RaciEntryModel(
        project_id=project_id,
        task_name=body.task_name,
        role_code=body.role_code,
        assignment=body.assignment.upper(),
        discipline=body.discipline,
        phase=body.phase,
    )
    db.add(entry)
    db.commit()
    return {"success": True, "entry_id": entry.id}
