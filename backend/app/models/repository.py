"""
repository.py — Repository in-memory pentru Project, ProjectContextEntry, GeneratedDocument.

TODO: Înlocuiește cu SQLAlchemy + PostgreSQL când adăugăm persistență.
"""

from __future__ import annotations

import datetime
from typing import Literal

# ── Tipuri interne ────────────────────────────────────────────────────────────

DocType = Literal[
    "bep", "lod_matrix", "eir", "checklist", "minutes", "bep_verification_report"
]


# ── Structuri de date ─────────────────────────────────────────────────────────

class ProjectRecord:
    """Proiect BIM."""
    def __init__(
        self, id: int, name: str, code: str,
        client_name: str | None = None,
        project_type: str | None = None,
    ):
        self.id = id
        self.name = name
        self.code = code
        self.client_name = client_name
        self.project_type = project_type
        self.status = "new"
        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "client_name": self.client_name,
            "project_type": self.project_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ProjectContextEntry:
    """Snapshot al ProjectContext pentru un proiect."""
    def __init__(self, id: int, project_id: int, context_json: dict):
        self.id = id
        self.project_id = project_id
        self.context_json = context_json
        self.created_at = datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "context_json": self.context_json,
            "created_at": self.created_at.isoformat(),
        }


class GeneratedDocument:
    """Document generat (BEP, raport verificare, etc.)."""
    def __init__(
        self, id: int, project_id: int,
        doc_type: DocType,
        title: str,
        content_markdown: str,
        version: str | None = None,
    ):
        self.id = id
        self.project_id = project_id
        self.doc_type = doc_type
        self.title = title
        self.content_markdown = content_markdown
        self.version = version
        self.created_at = datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "doc_type": self.doc_type,
            "title": self.title,
            "content_markdown": self.content_markdown,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }


# ── Store in-memory ──────────────────────────────────────────────────────────
# TODO: Înlocuiește cu sesiuni SQLAlchemy + PostgreSQL

_projects: dict[int, ProjectRecord] = {}
_next_project_id: int = 1

_context_entries: list[ProjectContextEntry] = []
_next_context_id: int = 1

_documents: list[GeneratedDocument] = []
_next_document_id: int = 1


# ── CRUD Projects ─────────────────────────────────────────────────────────────

def create_project(
    name: str, code: str,
    client_name: str | None = None,
    project_type: str | None = None,
) -> ProjectRecord:
    """Creează un proiect nou."""
    global _next_project_id
    project = ProjectRecord(
        id=_next_project_id, name=name, code=code,
        client_name=client_name, project_type=project_type,
    )
    _projects[project.id] = project
    _next_project_id += 1
    return project


def get_project(project_id: int) -> ProjectRecord | None:
    """Returnează un proiect după ID."""
    return _projects.get(project_id)


def list_projects() -> list[ProjectRecord]:
    """Returnează toate proiectele, ordonate după created_at desc."""
    return sorted(_projects.values(), key=lambda p: p.created_at, reverse=True)


def update_project_status(project_id: int, new_status: str) -> ProjectRecord | None:
    """Actualizează statusul unui proiect și bumps updated_at."""
    project = _projects.get(project_id)
    if project:
        project.status = new_status
        project.updated_at = datetime.datetime.now(datetime.timezone.utc)
    return project


# ── CRUD ProjectContextEntry ─────────────────────────────────────────────────

def save_project_context(project_id: int, context_json: dict) -> ProjectContextEntry:
    """Salvează un snapshot al ProjectContext pentru un proiect."""
    global _next_context_id
    entry = ProjectContextEntry(
        id=_next_context_id, project_id=project_id,
        context_json=context_json,
    )
    _context_entries.append(entry)
    _next_context_id += 1
    return entry


def get_latest_project_context(project_id: int) -> ProjectContextEntry | None:
    """Returnează cel mai recent ProjectContext pentru un proiect."""
    entries = [e for e in _context_entries if e.project_id == project_id]
    if not entries:
        return None
    return max(entries, key=lambda e: e.created_at)


# ── CRUD GeneratedDocument ────────────────────────────────────────────────────

def save_document(
    project_id: int,
    doc_type: DocType,
    title: str,
    content_markdown: str,
    version: str | None = None,
) -> GeneratedDocument:
    """Salvează un document generat."""
    global _next_document_id
    doc = GeneratedDocument(
        id=_next_document_id, project_id=project_id,
        doc_type=doc_type, title=title,
        content_markdown=content_markdown, version=version,
    )
    _documents.append(doc)
    _next_document_id += 1
    return doc


def get_latest_document(
    project_id: int, doc_type: DocType
) -> GeneratedDocument | None:
    """Returnează cel mai recent document de un anumit tip pentru un proiect."""
    docs = [
        d for d in _documents
        if d.project_id == project_id and d.doc_type == doc_type
    ]
    if not docs:
        return None
    return max(docs, key=lambda d: d.created_at)


def list_documents(project_id: int) -> list[GeneratedDocument]:
    """Returnează toate documentele unui proiect."""
    return [d for d in _documents if d.project_id == project_id]
