"""
raci.py — Scheme Pydantic pentru matricea RACI.
"""

from __future__ import annotations

from pydantic import BaseModel


class RaciEntryCreate(BaseModel):
    """Intrare RACI: task + rol + assignment."""
    task_name: str
    role_code: str
    assignment: str  # R/A/C/I
    discipline: str | None = None
    phase: str | None = None


class RaciEntryRead(BaseModel):
    """Intrare RACI returnată de API."""
    id: int
    project_id: int
    task_name: str
    role_code: str
    assignment: str
    discipline: str | None = None
    phase: str | None = None
    created_at: str


class RaciMatrixRead(BaseModel):
    """Matrice RACI completă."""
    project_id: int
    entries: list[RaciEntryRead] = []
    tasks: list[str] = []
    roles: list[str] = []
    total_entries: int = 0
