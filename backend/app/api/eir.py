"""
eir.py — Router EIR/AIR (Exchange/Asset Information Requirements).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import EirModel, UserModel
from app.services.auth import get_current_user
from app.services.eir_generator import generate_eir, get_latest_eir

router = APIRouter()


@router.post("/projects/{project_id}/generate-eir")
def generate_eir_endpoint(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generează EIR din ProjectContext."""
    result = generate_eir(db, project_id)
    db.commit()
    return result


@router.get("/projects/{project_id}/eir")
def get_eir(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează cel mai recent EIR."""
    entry = get_latest_eir(db, project_id)
    if not entry:
        return {"message": "Nu există EIR generat.", "eir": None}
    return {
        "eir": {
            "id": entry.id,
            "eir_type": entry.eir_type,
            "content_json": entry.content_json,
            "version": entry.version,
            "created_at": entry.created_at.isoformat() if entry.created_at else "",
        }
    }


@router.get("/projects/{project_id}/eir/history")
def get_eir_history(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează istoricul EIR-urilor."""
    entries = (
        db.query(EirModel)
        .filter(EirModel.project_id == project_id)
        .order_by(desc(EirModel.created_at))
        .all()
    )
    return [
        {
            "id": e.id,
            "eir_type": e.eir_type,
            "version": e.version,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        }
        for e in entries
    ]
