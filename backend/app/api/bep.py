"""
bep.py — Router API pentru generarea BEP.
POST /api/generate-bep — primește ProjectContext, returnează BEP Markdown.
POST /api/store-bep — stochează un BEP pentru context Chat Expert.
GET  /api/export-bep-docx/{project_code} — exportă BEP ca fișier DOCX.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.schemas.project_context import ProjectContext
from app.services.bep_generator import generate_bep
from app.services.bep_docx_exporter import markdown_to_docx
from app.services.chat_expert import store_bep, get_bep_content, get_stored_projects
from app.api.bep_verification import store_project_context

router = APIRouter()


@router.post("/generate-bep")
def api_generate_bep(project_context: ProjectContext):
    """
    Generează un BIM Execution Plan complet pe baza datelor de proiect.

    Primește un JSON cu ProjectContext complet.
    Returnează BEP în format Markdown, codul proiectului și versiunea BEP.
    Auto-stochează BEP-ul pentru a fi disponibil în Chat Expert.
    """
    try:
        result = generate_bep(project_context)
        # Auto-store BEP for Chat Expert context
        store_bep(result["project_code"], result["bep_markdown"])
        # Auto-store ProjectContext for BEP Verifier
        store_project_context(
            result["project_code"],
            project_context.model_dump(mode="json"),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StoreBepRequest(BaseModel):
    project_code: str
    bep_markdown: str


@router.post("/store-bep")
def api_store_bep(req: StoreBepRequest):
    """Stochează manual un BEP pentru a fi folosit ca context în Chat Expert."""
    if not req.project_code.strip():
        raise HTTPException(status_code=400, detail="project_code nu poate fi gol.")
    store_bep(req.project_code.strip(), req.bep_markdown)
    return {"status": "ok", "project_code": req.project_code.strip()}


@router.get("/export-bep-docx/{project_code}")
def api_export_bep_docx(project_code: str):
    """Exportă BEP-ul unui proiect ca document DOCX formatat profesional."""
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
