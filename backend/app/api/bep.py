"""
bep.py — Router API pentru generarea BEP.
POST /api/generate-bep — primește ProjectContext, returnează BEP Markdown.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.project_context import ProjectContext
from app.services.bep_generator import generate_bep

router = APIRouter()


@router.post("/generate-bep")
def api_generate_bep(project_context: ProjectContext):
    """
    Generează un BIM Execution Plan complet pe baza datelor de proiect.

    Primește un JSON cu ProjectContext complet.
    Returnează BEP în format Markdown, codul proiectului și versiunea BEP.
    """
    try:
        result = generate_bep(project_context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
