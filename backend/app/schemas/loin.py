"""
loin.py — Scheme Pydantic pentru LOIN (Level of Information Need — BS EN 17412-1).
"""

from __future__ import annotations

from pydantic import BaseModel


class LoinEntryCreate(BaseModel):
    """Intrare LOIN: element × discipline × phase."""
    element_type: str
    discipline: str
    phase: str
    detail_level: str | None = None
    dimensionality: str | None = None
    information_content: str | None = None


class LoinEntryRead(BaseModel):
    """Intrare LOIN returnată de API."""
    id: int
    project_id: int
    element_type: str
    discipline: str
    phase: str
    detail_level: str | None = None
    dimensionality: str | None = None
    information_content: str | None = None
    created_at: str


class LoinMatrixRead(BaseModel):
    """Matrice LOIN completă."""
    project_id: int
    entries: list[LoinEntryRead] = []
    element_types: list[str] = []
    phases: list[str] = []
    total_entries: int = 0
