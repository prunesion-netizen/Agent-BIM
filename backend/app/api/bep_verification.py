"""
bep_verification.py — Router API pentru verificarea conformității BEP vs Model BIM.

POST /api/projects/{project_id}/verify-bep-model
  - Primește ModelSummary ca body JSON
  - Preia ProjectContext + BEP-ul stocat pentru project_id
  - Apelează call_llm_bep_verifier
  - Returnează raport structurat (checks + report_markdown)
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.model_summary import ModelSummary
from app.ai_client import call_llm_bep_verifier
from app.services.chat_expert import get_bep_content, get_stored_projects

logger = logging.getLogger(__name__)
router = APIRouter()


# TODO: Când vom avea DB, înlocuim cu query real.
# Deocamdată stocăm ProjectContext în memorie (populat la generarea BEP).
_PROJECT_CONTEXT_STORE: dict[str, dict] = {}


def store_project_context(project_id: str, ctx: dict) -> None:
    """Stochează ProjectContext (apelat din bep generator)."""
    _PROJECT_CONTEXT_STORE[project_id] = ctx


def _get_project_context(project_id: str) -> dict:
    """Returnează ProjectContext stocat sau un stub minimal."""
    if project_id in _PROJECT_CONTEXT_STORE:
        return _PROJECT_CONTEXT_STORE[project_id]
    # Stub — marcăm ca TODO pentru când avem persistență
    return {"project_code": project_id, "_stub": True}


@router.post("/projects/{project_id}/verify-bep-model")
def api_verify_bep_model(project_id: str, model_summary: ModelSummary):
    """
    Verifică conformitatea BEP vs Model BIM pentru un proiect.

    - Path: project_id (codul proiectului)
    - Body: ModelSummary (rezumat tehnic al modelului)
    - Returnează: { report_markdown, checks }
    """
    # 1) Preia BEP-ul stocat
    bep_content = get_bep_content(project_id)
    if not bep_content:
        stored = get_stored_projects()
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nu exista BEP stocat pentru proiectul '{project_id}'. "
                f"Proiecte disponibile: {stored or 'niciunul'}. "
                "Genereaza mai intai un BEP din fisa de proiect."
            ),
        )

    # 2) Preia ProjectContext
    project_context = _get_project_context(project_id)

    # 3) Construiește verification_context
    verification_context = {
        "project_context": project_context,
        "bep_excerpt": bep_content,
        "model_summary": model_summary.model_dump(mode="json"),
    }

    logger.info(
        f"Verificare BEP vs Model: project_id={project_id}, "
        f"disciplines={model_summary.disciplines_present}, "
        f"formats={model_summary.exchange_formats_available}"
    )

    # 4) Apelează LLM
    try:
        result = call_llm_bep_verifier(verification_context)
    except Exception as e:
        logger.error(f"Eroare la verificare BEP vs Model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Eroare la verificarea BEP: {str(e)}"
        )

    # 5) Returnează raportul structurat
    return {
        "report_markdown": result.get("report_markdown", ""),
        "checks": result.get("checks", []),
        "summary": result.get("summary", {}),
    }
