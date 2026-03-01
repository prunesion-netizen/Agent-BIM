"""
project.py — Scheme Pydantic pentru Project, GeneratedDocument, ProjectContextRead.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── ProjectStatus ─────────────────────────────────────────────────────────────

class ProjectStatus(str, Enum):
    NEW = "new"
    CONTEXT_DEFINED = "context_defined"
    BEP_GENERATED = "bep_generated"
    BEP_VERIFIED_PARTIAL = "bep_verified_partial"
    BEP_VERIFIED_OK = "bep_verified_ok"


# ── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    """Date pentru crearea unui proiect nou."""
    name: str = Field(..., min_length=1, description="Numele proiectului")
    code: str = Field(..., min_length=1, description="Cod intern proiect")
    client_name: str | None = Field(None, description="Numele beneficiarului")
    project_type: str | None = Field(None, description="Tipul de proiect")
    description: str | None = Field(None, description="Descriere proiect")


class ProjectUpdate(BaseModel):
    """Date pentru actualizarea parțială a unui proiect."""
    name: str | None = None
    client_name: str | None = None
    project_type: str | None = None
    description: str | None = None


class ProjectRead(BaseModel):
    """Proiect returnat de API."""
    id: int
    name: str
    code: str
    client_name: str | None = None
    project_type: str | None = None
    description: str | None = None
    status: str = "new"
    created_at: str
    updated_at: str


# ── GeneratedDocument ─────────────────────────────────────────────────────────

class GeneratedDocumentRead(BaseModel):
    """Document generat returnat de API."""
    id: int
    project_id: int
    doc_type: Literal[
        "bep", "lod_matrix", "eir", "checklist",
        "minutes", "bep_verification_report"
    ]
    title: str
    content_markdown: str
    version: str | None = None
    created_at: str


# ── ProjectContextRead ───────────────────────────────────────────────────────

class ProjectContextRead(BaseModel):
    """ProjectContext entry returnat de API."""
    id: int
    project_id: int
    context_json: dict
    created_at: str


# ── Răspuns compus pentru GET /api/projects/{id} ──────────────────────────────

class ProjectDetailRead(BaseModel):
    """Detalii complete proiect: project + ultimul context + ultimul BEP."""
    project: ProjectRead
    project_context: ProjectContextRead | None = None
    latest_bep: GeneratedDocumentRead | None = None
