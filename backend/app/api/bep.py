"""
bep.py — Router API pentru generarea BEP.

Endpointuri legacy (backward-compat):
  POST /api/generate-bep
  POST /api/store-bep
  GET  /api/export-bep-docx/{project_code}
  GET  /api/bep-projects

Endpoint nou (project-scoped):
  POST /api/projects/{project_id}/generate-bep
  GET  /api/projects/{project_id}/export-bep-docx
"""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.schemas.project_context import ProjectContext
from app.schemas.project import ProjectRead, GeneratedDocumentRead
from app.services.bep_generator import generate_bep
from app.services.bep_docx_exporter import markdown_to_docx
from app.services.chat_expert import store_bep, get_bep_content, get_stored_projects
from app.models.repository import (
    get_project, save_project_context, save_document,
    get_latest_document,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# Endpoint NOU — project-scoped
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/projects/{project_id}/generate-bep")
def api_generate_bep_for_project(project_id: int, project_context: ProjectContext):
    """
    Generează un BEP pentru un proiect specific.

    - Salvează ProjectContext ca ProjectContextEntry
    - Generează BEP via Claude
    - Salvează BEP ca GeneratedDocument (doc_type="bep")
    - Sincronizează cu store-ul legacy pentru Chat Expert
    """
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Proiectul {project_id} nu exista.")

    try:
        # Salvează ProjectContext
        save_project_context(project_id, project_context.model_dump(mode="json"))

        # Generează BEP
        result = generate_bep(project_context)
        bep_markdown = result["bep_markdown"]

        # Salvează ca GeneratedDocument
        doc = save_document(
            project_id=project_id,
            doc_type="bep",
            title=f"BEP {project.code} {project_context.bep_version}",
            content_markdown=bep_markdown,
            version=project_context.bep_version,
        )

        # Sincronizează cu store-ul legacy (pentru Chat Expert)
        store_bep(project.code, bep_markdown)

        logger.info(
            f"BEP generat pentru proiectul {project_id} ({project.code}), "
            f"document_id={doc.id}"
        )

        return {
            "project": ProjectRead(**project.to_dict()),
            "project_context": project_context.model_dump(mode="json"),
            "bep_document": GeneratedDocumentRead(**doc.to_dict()),
        }

    except Exception as e:
        logger.error(f"Eroare generare BEP pentru proiectul {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/export-bep-docx")
def api_export_bep_docx_for_project(project_id: int):
    """Exportă BEP-ul unui proiect ca DOCX (din repository)."""
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Proiectul {project_id} nu exista.")

    bep_doc = get_latest_document(project_id, "bep")
    if not bep_doc:
        raise HTTPException(status_code=404, detail="Nu exista BEP generat pentru acest proiect.")

    docx_buffer = markdown_to_docx(bep_doc.content_markdown, project.code)
    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="BEP_{project.code}.docx"'
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# Endpointuri LEGACY (backward-compat)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/generate-bep")
def api_generate_bep(project_context: ProjectContext):
    """Legacy: generează BEP fără project_id."""
    try:
        result = generate_bep(project_context)
        store_bep(result["project_code"], result["bep_markdown"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StoreBepRequest(BaseModel):
    project_code: str
    bep_markdown: str


@router.post("/store-bep")
def api_store_bep(req: StoreBepRequest):
    """Stochează manual un BEP pentru Chat Expert."""
    if not req.project_code.strip():
        raise HTTPException(status_code=400, detail="project_code nu poate fi gol.")
    store_bep(req.project_code.strip(), req.bep_markdown)
    return {"status": "ok", "project_code": req.project_code.strip()}


@router.get("/export-bep-docx/{project_code}")
def api_export_bep_docx(project_code: str):
    """Legacy: exportă BEP ca DOCX după project_code."""
    content = get_bep_content(project_code)
    if not content:
        raise HTTPException(status_code=404, detail="BEP not found for this project")
    docx_buffer = markdown_to_docx(content, project_code)
    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="BEP_{project_code}.docx"'
        },
    )


@router.get("/bep-projects")
def api_bep_projects():
    """Returnează lista de proiecte cu BEP stocat."""
    return {"projects": get_stored_projects()}
