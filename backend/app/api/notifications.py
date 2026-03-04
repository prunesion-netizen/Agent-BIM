"""
notifications.py — Router notificari in-app.

GET /notifications — lista notificari (opțional ?unread_only=true)
POST /notifications/{id}/read — marcheaza citita
POST /notifications/read-all — marcheaza toate citite
GET /notifications/count — numar necitite
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import NotificationModel, UserModel
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/notifications")
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista notificari pentru utilizatorul curent."""
    q = db.query(NotificationModel).filter(NotificationModel.user_id == user.id)
    if unread_only:
        q = q.filter(NotificationModel.is_read == False)  # noqa: E712
    notifications = q.order_by(desc(NotificationModel.created_at)).limit(limit).all()
    return [
        {
            "id": n.id,
            "project_id": n.project_id,
            "category": n.category,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


@router.get("/notifications/count")
def notification_count(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Numar notificari necitite."""
    count = (
        db.query(func.count(NotificationModel.id))
        .filter(
            NotificationModel.user_id == user.id,
            NotificationModel.is_read == False,  # noqa: E712
        )
        .scalar()
    )
    return {"unread_count": count or 0}


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marcheaza o notificare ca citita."""
    n = (
        db.query(NotificationModel)
        .filter(
            NotificationModel.id == notification_id,
            NotificationModel.user_id == user.id,
        )
        .first()
    )
    if not n:
        raise HTTPException(status_code=404, detail="Notificarea nu exista.")
    n.is_read = True
    db.commit()
    return {"ok": True}


@router.post("/notifications/read-all")
def mark_all_notifications_read(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marcheaza toate notificarile ca citite."""
    db.query(NotificationModel).filter(
        NotificationModel.user_id == user.id,
        NotificationModel.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}
