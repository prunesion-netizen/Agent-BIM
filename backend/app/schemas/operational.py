"""
operational.py — Scheme Pydantic pentru handover checklist (ISO 19650-3).
"""

from __future__ import annotations

from pydantic import BaseModel


class HandoverItemCreate(BaseModel):
    """Element checklist de creat."""
    item_name: str
    category: str


class HandoverItemUpdate(BaseModel):
    """Actualizare element checklist."""
    is_completed: bool | None = None
    completed_by: str | None = None


class HandoverItemRead(BaseModel):
    """Element checklist returnat de API."""
    id: int
    project_id: int
    item_name: str
    category: str
    is_completed: bool
    completed_by: str | None = None
    completed_at: str | None = None
    created_at: str


class HandoverSummary(BaseModel):
    """Sumar handover checklist."""
    total_items: int = 0
    completed_items: int = 0
    completion_percent: float = 0.0
    by_category: dict[str, dict] = {}
