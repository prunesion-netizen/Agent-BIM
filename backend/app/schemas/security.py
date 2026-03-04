"""
security.py — Scheme Pydantic pentru clasificare securitate (ISO 19650-5).
"""

from __future__ import annotations

from pydantic import BaseModel


class SecurityClassificationCreate(BaseModel):
    """Date pentru clasificare securitate."""
    classification_level: str = "standard"
    sensitive_areas: str | None = None


class SecurityClassificationRead(BaseModel):
    """Clasificare securitate returnată de API."""
    id: int
    project_id: int
    classification_level: str
    security_plan_json: dict | None = None
    sensitive_areas: str | None = None
    created_at: str
    updated_at: str
