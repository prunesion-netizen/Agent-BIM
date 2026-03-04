"""
deliverables.py — Router TIDP/MIDP (livrabile BIM).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import DeliverableModel, UserModel
from app.schemas.deliverable import DeliverableCreate, DeliverableUpdate
from app.services.auth import get_current_user
from app.services.delivery_plan import (
    generate_tidp,
    get_delivery_plan,
    update_deliverable_status,
)

router = APIRouter()


@router.post("/projects/{project_id}/generate-tidp")
def generate_tidp_endpoint(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generează TIDP din ProjectContext."""
    result = generate_tidp(db, project_id)
    db.commit()
    return result


@router.get("/projects/{project_id}/delivery-plan")
def get_delivery_plan_endpoint(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează planul de livrare curent."""
    return get_delivery_plan(db, project_id)


@router.post("/projects/{project_id}/deliverables")
def create_deliverable(
    project_id: int,
    body: DeliverableCreate,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creează un livrabil manual."""
    import datetime
    due = None
    if body.due_date:
        try:
            due = datetime.date.fromisoformat(body.due_date)
        except ValueError:
            pass

    entry = DeliverableModel(
        project_id=project_id,
        title=body.title,
        discipline=body.discipline,
        format=body.format,
        lod=body.lod,
        responsible_role=body.responsible_role,
        due_date=due,
        phase=body.phase,
        status="planned",
    )
    db.add(entry)
    db.commit()
    return {"success": True, "deliverable_id": entry.id}


@router.patch("/deliverables/{deliverable_id}")
def update_deliverable(
    deliverable_id: int,
    body: DeliverableUpdate,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizează un livrabil."""
    entry = db.get(DeliverableModel, deliverable_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Livrabil negăsit.")

    if body.title is not None:
        entry.title = body.title
    if body.status is not None:
        entry.status = body.status
    if body.responsible_role is not None:
        entry.responsible_role = body.responsible_role
    if body.lod is not None:
        entry.lod = body.lod
    if body.due_date is not None:
        import datetime
        try:
            entry.due_date = datetime.date.fromisoformat(body.due_date)
        except ValueError:
            pass

    db.commit()
    return {"success": True}
