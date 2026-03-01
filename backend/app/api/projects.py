"""
projects.py — Router API pentru managementul proiectelor.

POST /api/projects         — creează proiect nou
GET  /api/projects         — listează toate proiectele
GET  /api/projects/{id}    — detalii proiect + context + BEP
"""

from fastapi import APIRouter, HTTPException

from app.schemas.project import (
    ProjectCreate, ProjectRead,
    ProjectDetailRead, ProjectContextRead,
    GeneratedDocumentRead,
)
from app.models.repository import (
    create_project, get_project, list_projects,
    get_latest_project_context, get_latest_document,
)

router = APIRouter()


@router.post("/projects", response_model=ProjectRead, status_code=201)
def api_create_project(data: ProjectCreate):
    """Creează un proiect BIM nou."""
    project = create_project(
        name=data.name,
        code=data.code,
        client_name=data.client_name,
        project_type=data.project_type,
    )
    return ProjectRead(**project.to_dict())


@router.get("/projects", response_model=list[ProjectRead])
def api_list_projects():
    """Returnează lista tuturor proiectelor."""
    return [ProjectRead(**p.to_dict()) for p in list_projects()]


@router.get("/projects/{project_id}", response_model=ProjectDetailRead)
def api_get_project(project_id: int):
    """
    Returnează detalii complete despre un proiect:
    - datele proiectului
    - ultimul ProjectContext (dacă există)
    - ultimul BEP generat (dacă există)
    """
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Proiectul {project_id} nu exista.")

    # Ultimul ProjectContext
    ctx_entry = get_latest_project_context(project_id)
    ctx_read = ProjectContextRead(**ctx_entry.to_dict()) if ctx_entry else None

    # Ultimul BEP
    bep_doc = get_latest_document(project_id, "bep")
    bep_read = GeneratedDocumentRead(**bep_doc.to_dict()) if bep_doc else None

    return ProjectDetailRead(
        project=ProjectRead(**project.to_dict()),
        project_context=ctx_read,
        latest_bep=bep_read,
    )
