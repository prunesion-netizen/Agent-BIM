"""
agent.py — Pydantic schemas pentru Agent BIM chat endpoint.
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
    conversation_history: list[dict] = Field(
        default_factory=list,
        description=(
            "Istoricul conversației. Fiecare element: "
            '{"role": "user"|"assistant", "content": "..."}'
        ),
    )
