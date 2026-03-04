"""
clash.py — Scheme Pydantic pentru clash management.
"""

from __future__ import annotations

from pydantic import BaseModel


class ClashRecordCreate(BaseModel):
    """Înregistrare clash de creat."""
    discipline_a: str
    discipline_b: str
    severity: str = "medium"
    description: str | None = None
    assigned_to_role: str | None = None


class ClashRecordUpdate(BaseModel):
    """Actualizare clash."""
    status: str | None = None
    assigned_to_role: str | None = None
    resolution_note: str | None = None


class ClashRecordRead(BaseModel):
    """Clash returnat de API."""
    id: int
    project_id: int
    discipline_a: str
    discipline_b: str
    severity: str
    description: str | None = None
    status: str
    assigned_to_role: str | None = None
    resolution_note: str | None = None
    created_at: str
    resolved_at: str | None = None


class ClashSummary(BaseModel):
    """Sumar clash-uri proiect."""
    total: int = 0
    open: int = 0
    resolved: int = 0
    by_severity: dict[str, int] = {}
    by_discipline_pair: list[dict] = []
