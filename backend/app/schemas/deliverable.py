"""
deliverable.py — Scheme Pydantic pentru TIDP/MIDP (livrabile BIM).
"""

from __future__ import annotations

from pydantic import BaseModel


class DeliverableCreate(BaseModel):
    """Date pentru crearea unui livrabil."""
    title: str
    discipline: str
    format: str = "ifc4"
    lod: str | None = None
    responsible_role: str | None = None
    due_date: str | None = None
    phase: str | None = None


class DeliverableUpdate(BaseModel):
    """Date pentru actualizarea unui livrabil."""
    title: str | None = None
    status: str | None = None
    responsible_role: str | None = None
    due_date: str | None = None
    lod: str | None = None


class DeliverableRead(BaseModel):
    """Livrabil returnat de API."""
    id: int
    project_id: int
    title: str
    discipline: str
    format: str
    lod: str | None = None
    responsible_role: str | None = None
    due_date: str | None = None
    phase: str | None = None
    status: str
    created_at: str
    updated_at: str


class TidpSummary(BaseModel):
    """Sumar TIDP — rezumat livrabile pe discipline."""
    total_deliverables: int = 0
    by_discipline: dict[str, int] = {}
    by_status: dict[str, int] = {}
    completion_percent: float = 0.0
    overdue_count: int = 0
