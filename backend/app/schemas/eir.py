"""
eir.py — Scheme Pydantic pentru EIR/AIR (Exchange/Asset Information Requirements).
"""

from __future__ import annotations

from pydantic import BaseModel


class InformationRequirement(BaseModel):
    """Cerință individuală de informare."""
    category: str
    requirement: str
    priority: str = "medium"
    acceptance_criteria: str | None = None


class EirCreate(BaseModel):
    """Date pentru generare EIR."""
    eir_type: str = "eir"


class EirRead(BaseModel):
    """EIR returnat de API."""
    id: int
    project_id: int
    eir_type: str
    content_json: dict
    version: str | None = None
    created_at: str
