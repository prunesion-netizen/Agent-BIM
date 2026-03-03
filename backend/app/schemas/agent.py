"""
agent.py — Pydantic schemas pentru Agent BIM chat endpoint și conversații.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Request body pentru agent chat SSE endpoint."""
    message: str = Field(
        ...,
        min_length=1,
        description="Mesajul utilizatorului către agent",
    )
    conversation_id: int | None = Field(
        default=None,
        description="ID-ul conversației existente (None = creează nouă)",
    )
    conversation_history: list[dict] = Field(
        default_factory=list,
        description=(
            "Istoricul conversației. Fiecare element: "
            '{"role": "user"|"assistant", "content": "..."}'
        ),
    )


# ── Conversation schemas ─────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    """Request body pentru crearea unei conversații noi."""
    title: str = Field(default="Conversație nouă", max_length=255)


class ConversationRead(BaseModel):
    """Sumarul unei conversații (pentru lista din sidebar)."""
    id: int
    project_id: int
    title: str
    message_count: int
    created_at: str
    updated_at: str


class MessageRead(BaseModel):
    """Un mesaj din conversație."""
    id: int
    sequence_num: int
    role: str
    content: str
    tool_steps: list[dict] | None = None
    created_at: str


class ConversationDetailRead(BaseModel):
    """Conversație completă cu mesaje."""
    id: int
    project_id: int
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageRead]
