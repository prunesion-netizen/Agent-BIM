"""
chat.py — Router API pentru Chat Expert BIM.
POST /api/chat-expert — primește o întrebare, returnează răspunsul AI.

Acceptă project_id (int) — citește BEP din repository.
Fallback la project_code (string) din legacy store.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.chat_expert import chat_expert
from app.models.repository import get_project, get_latest_document

router = APIRouter()


class ChatRequest(BaseModel):
    project_id: int | None = None
    message: str


class ChatResponse(BaseModel):
    answer: str


@router.post("/chat-expert", response_model=ChatResponse)
async def api_chat_expert(req: ChatRequest):
    """
    Răspunde la o întrebare BIM folosind contextul proiectului.

    - Dacă project_id (int) este specificat, caută project_code din repo.
    - Backend folosește BEP-ul proiectului ca context.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mesajul nu poate fi gol.")

    # Rezolvă project_code din project_id
    project_code: str | None = None
    if req.project_id is not None:
        project = get_project(req.project_id)
        if project:
            project_code = project.code
            # Dacă BEP-ul e în repository dar nu în legacy store, sincronizăm
            bep_doc = get_latest_document(req.project_id, "bep")
            if bep_doc:
                from app.services.chat_expert import store_bep
                store_bep(project.code, bep_doc.content_markdown)

    try:
        answer = await chat_expert(project_code, req.message.strip())
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
