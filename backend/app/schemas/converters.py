"""
converters.py — Funcții de conversie SQLAlchemy Model → Pydantic Schema.

Folosite în endpoint-urile API pentru a transforma obiectele ORM
în scheme Pydantic de răspuns (ProjectRead, ProjectContextRead, etc.).
"""

from __future__ import annotations

from app.models.sql_models import (
    AgentConversationModel,
    AgentMessageModel,
    GeneratedDocumentModel,
    ProjectContextModel,
    ProjectModel,
)
from app.schemas.agent import (
    ConversationDetailRead,
    ConversationRead,
    MessageRead,
)
from app.schemas.project import (
    GeneratedDocumentRead,
    ProjectContextRead,
    ProjectRead,
    VerificationHistoryItem,
)


def project_model_to_read(p: ProjectModel) -> ProjectRead:
    """Convertește un ProjectModel SQLAlchemy în ProjectRead Pydantic."""
    return ProjectRead(
        id=p.id,
        name=p.name,
        code=p.code,
        client_name=p.client_name,
        project_type=p.project_type,
        description=p.description,
        status=p.status,
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
    )


def context_model_to_read(c: ProjectContextModel) -> ProjectContextRead:
    """Convertește un ProjectContextModel SQLAlchemy în ProjectContextRead Pydantic."""
    return ProjectContextRead(
        id=c.id,
        project_id=c.project_id,
        context_json=c.context_json,
        created_at=c.created_at.isoformat() if c.created_at else "",
    )


def document_model_to_read(d: GeneratedDocumentModel) -> GeneratedDocumentRead:
    """Convertește un GeneratedDocumentModel SQLAlchemy în GeneratedDocumentRead Pydantic."""
    return GeneratedDocumentRead(
        id=d.id,
        project_id=d.project_id,
        doc_type=d.doc_type,
        title=d.title,
        content_markdown=d.content_markdown,
        version=d.version,
        summary_status=d.summary_status,
        fail_count=d.fail_count,
        warning_count=d.warning_count,
        created_at=d.created_at.isoformat() if d.created_at else "",
    )


def document_model_to_history_item(d: GeneratedDocumentModel) -> VerificationHistoryItem:
    """Convertește un GeneratedDocumentModel în VerificationHistoryItem (fără content)."""
    return VerificationHistoryItem(
        id=d.id,
        title=d.title,
        created_at=d.created_at.isoformat() if d.created_at else "",
        summary_status=d.summary_status,
        fail_count=d.fail_count,
        warning_count=d.warning_count,
    )


# ── Conversation converters ──────────────────────────────────────────────────

def message_model_to_read(m: AgentMessageModel) -> MessageRead:
    """Convertește un AgentMessageModel în MessageRead."""
    return MessageRead(
        id=m.id,
        sequence_num=m.sequence_num,
        role=m.role,
        content=m.content,
        tool_steps=m.tool_steps_json,
        created_at=m.created_at.isoformat() if m.created_at else "",
    )


def conversation_model_to_read(c: AgentConversationModel) -> ConversationRead:
    """Convertește un AgentConversationModel în ConversationRead (sumar)."""
    return ConversationRead(
        id=c.id,
        project_id=c.project_id,
        title=c.title,
        message_count=len(c.messages) if c.messages else 0,
        created_at=c.created_at.isoformat() if c.created_at else "",
        updated_at=c.updated_at.isoformat() if c.updated_at else "",
    )


def conversation_model_to_detail(c: AgentConversationModel) -> ConversationDetailRead:
    """Convertește un AgentConversationModel în ConversationDetailRead (cu mesaje)."""
    return ConversationDetailRead(
        id=c.id,
        project_id=c.project_id,
        title=c.title,
        created_at=c.created_at.isoformat() if c.created_at else "",
        updated_at=c.updated_at.isoformat() if c.updated_at else "",
        messages=[message_model_to_read(m) for m in (c.messages or [])],
    )
