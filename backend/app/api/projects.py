"""
projects.py — Router API pentru managementul proiectelor.

POST /api/projects         — creează proiect nou
GET  /api/projects         — listează toate proiectele
GET  /api/projects/{id}    — detalii proiect + context + BEP
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectRead,
    ProjectDetailRead,
)
from app.schemas.converters import (
    project_model_to_read,
    context_model_to_read,
    document_model_to_read,
)
from app.repositories.projects_repository import (
    create_project, get_project, list_projects, update_project,
    get_latest_project_context, get_latest_generated_document,
)

router = APIRouter()


@router.post("/projects", response_model=ProjectRead, status_code=201)
def api_create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """Creează un proiect BIM nou."""
    project = create_project(db, data)
    return project_model_to_read(project)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
def api_update_project(
    project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)
):
    """Actualizează parțial un proiect (nume, client, tip, descriere)."""
    project = update_project(db, project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail=f"Proiectul {project_id} nu exista.")
    return project_model_to_read(project)


@router.get("/projects", response_model=list[ProjectRead])
def api_list_projects(db: Session = Depends(get_db)):
    """Returnează lista tuturor proiectelor."""
    return [project_model_to_read(p) for p in list_projects(db)]


@router.get("/projects/{project_id}", response_model=ProjectDetailRead)
def api_get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Returnează detalii complete despre un proiect:
    - datele proiectului
    - ultimul ProjectContext (dacă există)
    - ultimul BEP generat (dacă există)
    """
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Proiectul {project_id} nu exista.")

    # Ultimul ProjectContext
    ctx_entry = get_latest_project_context(db, project_id)
    ctx_read = context_model_to_read(ctx_entry) if ctx_entry else None

    # Ultimul BEP
    bep_doc = get_latest_generated_document(db, project_id, "bep")
    bep_read = document_model_to_read(bep_doc) if bep_doc else None

    return ProjectDetailRead(
        project=project_model_to_read(project),
        project_context=ctx_read,
        latest_bep=bep_read,
    )
