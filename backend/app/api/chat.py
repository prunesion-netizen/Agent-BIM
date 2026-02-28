"""
chat.py — Router API pentru Chat Expert BIM.
POST /api/chat-expert — primește o întrebare, returnează răspunsul AI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.chat_expert import chat_expert

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

    - Dacă project_id este specificat, folosește BEP-ul proiectului ca context.
    - Dacă nu, răspunde pe baza standardelor generale BIM/ISO 19650.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mesajul nu poate fi gol.")

    try:
        answer = await chat_expert(req.project_id, req.message.strip())
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
