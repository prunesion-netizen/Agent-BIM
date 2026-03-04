"""
notification_service.py — Helper pentru crearea notificărilor in-app.

Apelat din diverse endpoint-uri pentru a genera notificari automate.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.sql_models import NotificationModel, UserModel

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    category: str = "info",
    project_id: int | None = None,
) -> NotificationModel:
    """Creaza o notificare pentru un utilizator."""
    n = NotificationModel(
        user_id=user_id,
        project_id=project_id,
        category=category,
        title=title,
        message=message,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def notify_all_users(
    db: Session,
    title: str,
    message: str,
    category: str = "info",
    project_id: int | None = None,
) -> int:
    """Creaza o notificare pentru toti utilizatorii. Returns count."""
    users = db.query(UserModel).all()
    count = 0
    for user in users:
        n = NotificationModel(
            user_id=user.id,
            project_id=project_id,
            category=category,
            title=title,
            message=message,
        )
        db.add(n)
        count += 1
    db.commit()
    return count


def notify_bep_generated(db: Session, user_id: int, project_id: int, project_name: str):
    """Notificare: BEP generat."""
    create_notification(
        db, user_id,
        title="BEP generat",
        message=f'BEP-ul proiectului "{project_name}" a fost generat cu succes.',
        category="bep",
        project_id=project_id,
    )


def notify_verification_complete(
    db: Session, user_id: int, project_id: int, project_name: str, status: str
):
    """Notificare: Verificare BEP finalizata."""
    create_notification(
        db, user_id,
        title=f"Verificare BEP: {status.upper()}",
        message=f'Verificarea BEP pentru "{project_name}" s-a finalizat cu status: {status}.',
        category="verification",
        project_id=project_id,
    )


def notify_cde_state_change(
    db: Session, user_id: int, project_id: int, doc_title: str, new_state: str
):
    """Notificare: Schimbare stare CDE."""
    state_labels = {
        "wip": "Work in Progress",
        "shared": "Shared",
        "published": "Published",
        "archived": "Archived",
    }
    create_notification(
        db, user_id,
        title="Stare CDE modificata",
        message=f'Documentul "{doc_title}" a trecut in starea: {state_labels.get(new_state, new_state)}.',
        category="cde_change",
        project_id=project_id,
    )


def notify_new_clash(
    db: Session, user_id: int, project_id: int, clash_count: int
):
    """Notificare: Clash-uri noi detectate."""
    create_notification(
        db, user_id,
        title=f"{clash_count} clash-uri noi",
        message=f"Au fost detectate {clash_count} clash-uri noi care necesita atentie.",
        category="clash",
        project_id=project_id,
    )
