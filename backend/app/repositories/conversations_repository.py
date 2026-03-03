"""
conversations_repository.py — CRUD PostgreSQL pentru conversații agent și mesaje.

Toate funcțiile primesc `db: Session` ca prim parametru.
"""

from __future__ import annotations

import datetime

from sqlalchemy import desc, func as sa_func
from sqlalchemy.orm import Session

from app.models.sql_models import AgentConversationModel, AgentMessageModel


# ── CRUD Conversations ───────────────────────────────────────────────────────

def create_conversation(
    db: Session, project_id: int, title: str = "Conversație nouă"
) -> AgentConversationModel:
    """Creează o conversație nouă pentru un proiect."""
    conv = AgentConversationModel(
        project_id=project_id,
        title=title,
    )
    db.add(conv)
    db.flush()
    return conv


def get_conversation(
    db: Session, conversation_id: int
) -> AgentConversationModel | None:
    """Returnează o conversație cu mesajele ei (eager via relationship)."""
    return db.get(AgentConversationModel, conversation_id)


def list_conversations(
    db: Session, project_id: int
) -> list[AgentConversationModel]:
    """Returnează conversațiile unui proiect, desc by updated_at."""
    return (
        db.query(AgentConversationModel)
        .filter(AgentConversationModel.project_id == project_id)
        .order_by(desc(AgentConversationModel.updated_at))
        .all()
    )


def delete_conversation(db: Session, conversation_id: int) -> bool:
    """Șterge o conversație (CASCADE șterge mesajele automat)."""
    conv = db.get(AgentConversationModel, conversation_id)
    if not conv:
        return False
    db.delete(conv)
    db.flush()
    return True


def update_conversation_title(
    db: Session, conversation_id: int, title: str
) -> AgentConversationModel | None:
    """Actualizează titlul unei conversații."""
    conv = db.get(AgentConversationModel, conversation_id)
    if not conv:
        return None
    conv.title = title
    conv.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.flush()
    return conv


def touch_conversation(db: Session, conversation_id: int) -> None:
    """Actualizează updated_at pe conversație (după adăugare mesaj)."""
    conv = db.get(AgentConversationModel, conversation_id)
    if conv:
        conv.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.flush()


# ── CRUD Messages ────────────────────────────────────────────────────────────

def _next_sequence_num(db: Session, conversation_id: int) -> int:
    """Returnează următorul sequence_num pentru o conversație."""
    result = (
        db.query(sa_func.coalesce(sa_func.max(AgentMessageModel.sequence_num), 0))
        .filter(AgentMessageModel.conversation_id == conversation_id)
        .scalar()
    )
    return result + 1


def add_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    tool_steps_json: list[dict] | None = None,
) -> AgentMessageModel:
    """Adaugă un mesaj într-o conversație."""
    seq = _next_sequence_num(db, conversation_id)
    msg = AgentMessageModel(
        conversation_id=conversation_id,
        sequence_num=seq,
        role=role,
        content=content,
        tool_steps_json=tool_steps_json,
    )
    db.add(msg)
    db.flush()
    touch_conversation(db, conversation_id)
    return msg


def get_messages(
    db: Session, conversation_id: int
) -> list[AgentMessageModel]:
    """Returnează mesajele unei conversații, asc by sequence_num."""
    return (
        db.query(AgentMessageModel)
        .filter(AgentMessageModel.conversation_id == conversation_id)
        .order_by(AgentMessageModel.sequence_num)
        .all()
    )
