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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.model_summary import ModelSummary
from app.ai_client import call_llm_bep_verifier
from app.repositories.projects_repository import (
    get_project, get_latest_generated_document, get_latest_project_context,
    save_generated_document, list_verification_reports,
)
from app.schemas.converters import document_model_to_history_item
from app.schemas.project import VerificationHistoryItem
from app.services.project_status import on_bep_verified
# Legacy bridge
from app.services.chat_expert import get_bep_content

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/projects/{project_id}/verify-bep-model")
def api_verify_bep_model(
    project_id: int,
    model_summary: ModelSummary,
    db: Session = Depends(get_db),
):
    """
    Verifică conformitatea BEP vs Model BIM pentru un proiect.

    - Citește BEP-ul generat din repository (sau legacy store ca fallback)
    - Citește ProjectContext din repository
    - Apelează Claude cu verification_context
    - Salvează raportul ca GeneratedDocument (doc_type="bep_verification_report")
    """
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=404, detail=f"Proiectul {project_id} nu exista."
        )

    # 1) Citește BEP-ul — din repository sau legacy store
    bep_content = None
    bep_doc = get_latest_generated_document(db, project_id, "bep")
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
    ctx_entry = get_latest_project_context(db, project_id)
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

    # 5) Salvează raportul ca GeneratedDocument (cu summary data)
    report_md = result.get("report_markdown", "")
    checks = result.get("checks", [])
    summary = result.get("summary", {})
    summary_status = summary.get("overall_status")
    fail_count = summary.get("fail_count", 0)
    warning_count = summary.get("warning_count", 0)

    doc = save_generated_document(
        db,
        project_id=project_id,
        doc_type="bep_verification_report",
        title=f"Raport verificare BEP vs Model - {project.code}",
        content_markdown=report_md,
        summary_status=summary_status,
        fail_count=fail_count,
        warning_count=warning_count,
    )

    # 6) Actualizează status proiect
    on_bep_verified(db, project_id, checks)

    logger.info(f"Raport verificare salvat: document_id={doc.id}")

    # 7) Returnează rezultatul
    return {
        "report_markdown": report_md,
        "checks": checks,
        "summary": summary,
        "document_id": doc.id,
    }


@router.get(
    "/projects/{project_id}/verification-history",
    response_model=list[VerificationHistoryItem],
)
def api_verification_history(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Returnează istoricul verificărilor BEP vs Model pentru un proiect."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=404, detail=f"Proiectul {project_id} nu exista."
        )
    docs = list_verification_reports(db, project_id)
    return [document_model_to_history_item(d) for d in docs]
