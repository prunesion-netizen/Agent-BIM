"""
bep.py — Router API pentru generarea BEP.
POST /api/generate-bep — primește ProjectContext, returnează BEP Markdown.
POST /api/store-bep — stochează un BEP pentru context Chat Expert.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.project_context import ProjectContext
from app.services.bep_generator import generate_bep
from app.services.chat_expert import store_bep, get_stored_projects

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


@router.get("/bep-projects")
def api_bep_projects():
    """Returnează lista de proiecte cu BEP stocat."""
    return {"projects": get_stored_projects()}
