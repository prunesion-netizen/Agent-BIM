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
    summary_status: str | None = None
    fail_count: int | None = None
    warning_count: int | None = None
    created_at: str


class VerificationHistoryItem(BaseModel):
    """Element din istoricul verificărilor BEP (fără content_markdown)."""
    id: int
    title: str
    created_at: str
    summary_status: str | None = None
    fail_count: int | None = None
    warning_count: int | None = None


# ── Dashboard Overview ────────────────────────────────────────────────────────

class LatestVerificationInfo(BaseModel):
    """Informații despre ultima verificare BEP."""
    summary_status: str | None = None
    fail_count: int | None = None
    warning_count: int | None = None
    created_at: str


class ProjectOverviewItem(BaseModel):
    """Element de overview pentru Dashboard (deprecated, use ProjectOverview)."""
    id: int
    name: str
    code: str
    client_name: str | None = None
    project_type: str | None = None
    status: str = "new"
    created_at: str
    updated_at: str
    has_context: bool = False
    has_bep: bool = False
    bep_version: str | None = None
    verification_count: int = 0
    latest_verification: LatestVerificationInfo | None = None


class ProjectOverview(BaseModel):
    """Overview proiect pentru Dashboard — câmpuri flatten."""
    id: int
    name: str
    code: str
    client_name: str | None = None
    project_type: str | None = None
    status: str = "new"
    has_bep: bool = False
    bep_version: str | None = None
    last_bep_generated_at: str | None = None
    has_verifications: bool = False
    last_verification_at: str | None = None
    last_verification_status: str | None = None
    last_verification_fail_count: int | None = None
    last_verification_warning_count: int | None = None
    updated_at: str


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
