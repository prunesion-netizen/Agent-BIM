"""
bep_verification.py — Router API pentru verificarea conformității BEP vs Model BIM.

POST /api/projects/{project_id}/verify-bep-model
  - Primește ModelSummary ca body
  - Citește BEP + ProjectContext din repository
  - Apelează call_llm_bep_verifier
  - Salvează raportul ca GeneratedDocument
  - Returnează raport structurat
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.model_summary import ModelSummary
from app.schemas.project import GeneratedDocumentRead
from app.ai_client import call_llm_bep_verifier
from app.models.repository import (
    get_project, get_latest_document, get_latest_project_context,
    save_document,
)
from app.services.project_status import on_bep_verified
# Legacy bridge
from app.services.chat_expert import get_bep_content

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/projects/{project_id}/verify-bep-model")
def api_verify_bep_model(project_id: int, model_summary: ModelSummary):
    """
    Verifică conformitatea BEP vs Model BIM pentru un proiect.

    - Citește BEP-ul generat din repository (sau legacy store ca fallback)
    - Citește ProjectContext din repository
    - Apelează Claude cu verification_context
    - Salvează raportul ca GeneratedDocument (doc_type="bep_verification_report")
    """
    project = get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=404, detail=f"Proiectul {project_id} nu exista."
        )

    # 1) Citește BEP-ul — din repository sau legacy store
    bep_content = None
    bep_doc = get_latest_document(project_id, "bep")
    if bep_doc:
        bep_content = bep_doc.content_markdown
    else:
        # Fallback la legacy store
        bep_content = get_bep_content(project.code)

    if not bep_content:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nu exista BEP generat pentru proiectul '{project.name}' "
                f"({project.code}). Genereaza mai intai un BEP."
            ),
        )

    # 2) Citește ProjectContext
    ctx_entry = get_latest_project_context(project_id)
    project_context = ctx_entry.context_json if ctx_entry else {}

    # 3) Construiește verification_context
    verification_context = {
        "project_context": project_context,
        "bep_excerpt": bep_content,
        "model_summary": model_summary.model_dump(mode="json"),
    }

    logger.info(
        f"Verificare BEP vs Model: project_id={project_id} ({project.code}), "
        f"disciplines={model_summary.disciplines_present}"
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

    # 5) Salvează raportul ca GeneratedDocument
    report_md = result.get("report_markdown", "")
    doc = save_document(
        project_id=project_id,
        doc_type="bep_verification_report",
        title=f"Raport verificare BEP vs Model - {project.code}",
        content_markdown=report_md,
    )

    # 6) Actualizează status proiect
    checks = result.get("checks", [])
    on_bep_verified(project_id, checks)

    logger.info(f"Raport verificare salvat: document_id={doc.id}")

    # 7) Returnează rezultatul
    return {
        "report_markdown": report_md,
        "checks": checks,
        "summary": result.get("summary", {}),
        "document_id": doc.id,
    }
