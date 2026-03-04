"""
chat.py — Router API pentru Chat Expert BIM.
POST /api/chat-expert — endpoint legacy (BEP + standarde).
POST /api/projects/{project_id}/chat-expert — endpoint copilot (context complet).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.services.auth import get_current_user
from app.services.chat_expert import chat_expert, chat_expert_copilot, store_bep
from app.repositories.projects_repository import (
    get_project,
    get_latest_generated_document,
    get_latest_project_context,
    list_verification_reports,
)

router = APIRouter()


class ChatRequest(BaseModel):
    project_id: int | None = None
    message: str


class CopilotChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@router.post("/chat-expert", response_model=ChatResponse)
async def api_chat_expert(req: ChatRequest, db: Session = Depends(get_db), _user: UserModel = Depends(get_current_user)):
    """
    Răspunde la o întrebare BIM folosind contextul proiectului (legacy).

    - Dacă project_id (int) este specificat, caută project_code din repo.
    - Backend folosește BEP-ul proiectului ca context.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mesajul nu poate fi gol.")

    # Rezolvă project_code din project_id
    project_code: str | None = None
    if req.project_id is not None:
        project = get_project(db, req.project_id)
        if project:
            project_code = project.code
            # Dacă BEP-ul e în repository dar nu în legacy store, sincronizăm
            bep_doc = get_latest_generated_document(db, req.project_id, "bep")
            if bep_doc:
                store_bep(project.code, bep_doc.content_markdown)

    try:
        answer = await chat_expert(project_code, req.message.strip())
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/chat-expert", response_model=ChatResponse)
async def api_chat_copilot(
    project_id: int,
    req: CopilotChatRequest,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """
    Copilot BIM — răspunde folosind contextul complet al proiectului:
    project info, ProjectContext, BEP, rapoarte de verificare.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mesajul nu poate fi gol.")

    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proiectul nu a fost gasit.")

    # Încarcă ProjectContext
    ctx_model = get_latest_project_context(db, project_id)
    project_context = ctx_model.context_json if ctx_model else None

    # Încarcă BEP
    bep_doc = get_latest_generated_document(db, project_id, "bep")
    bep_data = None
    if bep_doc:
        bep_data = {
            "version": bep_doc.version,
            "created_at": str(bep_doc.created_at) if bep_doc.created_at else None,
            "content_markdown": bep_doc.content_markdown,
        }

    # Încarcă rapoarte de verificare
    verif_reports = list_verification_reports(db, project_id)
    verifications = None
    if verif_reports:
        latest = verif_reports[0]
        verifications = {
            "total_count": len(verif_reports),
            "latest": {
                "summary_status": latest.summary_status,
                "fail_count": latest.fail_count or 0,
                "warning_count": latest.warning_count or 0,
                "created_at": str(latest.created_at) if latest.created_at else None,
                "report_markdown": latest.content_markdown,
            },
            "history": [
                {
                    "summary_status": r.summary_status,
                    "fail_count": r.fail_count or 0,
                    "warning_count": r.warning_count or 0,
                    "created_at": str(r.created_at) if r.created_at else None,
                }
                for r in verif_reports
            ],
        }

    chat_context = {
        "project": {
            "id": project.id,
            "name": project.name,
            "code": project.code,
            "client_name": project.client_name,
            "project_type": project.project_type,
            "status": project.status,
        },
        "project_context": project_context,
        "bep": bep_data,
        "verifications": verifications,
    }

    try:
        answer = await chat_expert_copilot(chat_context, req.message.strip())
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
