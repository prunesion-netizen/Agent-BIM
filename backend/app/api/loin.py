"""
loin.py — Router LOIN Matrix (BS EN 17412-1).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import LoinEntryModel, UserModel
from app.schemas.loin import LoinEntryCreate
from app.services.auth import get_current_user
from app.services.loin_generator import generate_loin_matrix, get_loin_matrix

router = APIRouter()


@router.post("/projects/{project_id}/generate-loin")
def generate_loin_endpoint(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generează matrice LOIN din ProjectContext."""
    result = generate_loin_matrix(db, project_id)
    db.commit()
    return result


@router.get("/projects/{project_id}/loin")
def get_loin_endpoint(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează matricea LOIN curentă."""
    return get_loin_matrix(db, project_id)


@router.post("/projects/{project_id}/loin/entries")
def add_loin_entry(
    project_id: int,
    body: LoinEntryCreate,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Adaugă o intrare LOIN manuală."""
    entry = LoinEntryModel(
        project_id=project_id,
        element_type=body.element_type,
        discipline=body.discipline,
        phase=body.phase,
        detail_level=body.detail_level,
        dimensionality=body.dimensionality,
        information_content=body.information_content,
    )
    db.add(entry)
    db.commit()
    return {"success": True, "entry_id": entry.id}
