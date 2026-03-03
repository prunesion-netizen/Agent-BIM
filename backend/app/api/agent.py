"""
agent.py — SSE endpoint + conversation CRUD pentru Agent BIM autonom.

Endpoints:
  POST /api/projects/{pid}/agent-chat         — SSE chat cu persistență
  GET  /api/projects/{pid}/conversations      — lista conversații
  POST /api/projects/{pid}/conversations      — creează conversație
  GET  /api/projects/{pid}/conversations/{cid} — detalii + mesaje
  DELETE /api/projects/{pid}/conversations/{cid} — șterge conversație
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.agent import AgentChatRequest, ConversationCreate
from app.repositories.projects_repository import get_project
from app.repositories.conversations_repository import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
    update_conversation_title,
)
from app.schemas.converters import (
    conversation_model_to_detail,
    conversation_model_to_read,
)
from app.services.agent_executor import AgentResult, run_agent, _sse_event

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Conversation CRUD ─────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/conversations")
def api_list_conversations(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Returnează lista conversațiilor unui proiect."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Proiectul {project_id} nu există.")
    convs = list_conversations(db, project_id)
    return [conversation_model_to_read(c) for c in convs]


@router.post("/projects/{project_id}/conversations")
def api_create_conversation(
    project_id: int,
    body: ConversationCreate,
    db: Session = Depends(get_db),
):
    """Creează o conversație nouă pentru un proiect."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Proiectul {project_id} nu există.")
    conv = create_conversation(db, project_id, body.title)
    return conversation_model_to_read(conv)


@router.get("/projects/{project_id}/conversations/{conversation_id}")
def api_get_conversation(
    project_id: int,
    conversation_id: int,
    db: Session = Depends(get_db),
):
    """Returnează o conversație completă cu mesaje."""
    conv = get_conversation(db, conversation_id)
    if not conv or conv.project_id != project_id:
        raise HTTPException(status_code=404, detail="Conversația nu există.")
    return conversation_model_to_detail(conv)


@router.delete("/projects/{project_id}/conversations/{conversation_id}")
def api_delete_conversation(
    project_id: int,
    conversation_id: int,
    db: Session = Depends(get_db),
):
    """Șterge o conversație."""
    conv = get_conversation(db, conversation_id)
    if not conv or conv.project_id != project_id:
        raise HTTPException(status_code=404, detail="Conversația nu există.")
    delete_conversation(db, conversation_id)
    return {"ok": True}


# ── Agent Chat SSE (cu persistență) ──────────────────────────────────────────

@router.post("/projects/{project_id}/agent-chat")
async def api_agent_chat(
    project_id: int,
    request: AgentChatRequest,
    db: Session = Depends(get_db),
):
    """
    Agent BIM autonom cu tool use + SSE streaming + persistență conversații.

    Dacă conversation_id e null, creează o conversație nouă.
    Salvează mesajele (user + assistant) în DB după finalizare SSE.
    Emite un eveniment suplimentar 'conversation_meta' cu id-ul și titlul.
    """
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Proiectul {project_id} nu există.",
        )

    logger.info(
        f"Agent chat: project_id={project_id} ({project.code}), "
        f"message='{request.message[:100]}...'"
    )

    # Conversație: existentă sau nouă
    conv_id = request.conversation_id
    is_new_conv = conv_id is None

    if conv_id is not None:
        conv = get_conversation(db, conv_id)
        if not conv or conv.project_id != project_id:
            raise HTTPException(status_code=404, detail="Conversația nu există.")
    else:
        # Auto-generează titlu din primele cuvinte
        title = request.message[:80].strip()
        if len(request.message) > 80:
            title += "..."
        conv = create_conversation(db, project_id, title)
        conv_id = conv.id

    # Salvează mesajul user în DB
    add_message(db, conv_id, "user", request.message)

    # Construiește history din DB dacă e conversație existentă
    conversation_history = request.conversation_history
    if not is_new_conv and not conversation_history:
        db_messages = get_messages(db, conv_id)
        # Exclude ultimul mesaj (cel tocmai adăugat)
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in db_messages[:-1]
            if m.role in ("user", "assistant") and m.content
        ]

    # Collector pentru a salva răspunsul asistentului
    collector = AgentResult()

    async def event_stream():
        async for event in run_agent(
            db=db,
            project_id=project_id,
            user_message=request.message,
            conversation_history=conversation_history,
            collector=collector,
        ):
            yield event

        # După stream done: salvează mesajul assistant în DB
        tool_steps_data = collector.tool_steps if collector.tool_steps else None
        if collector.final_text or tool_steps_data:
            add_message(
                db, conv_id, "assistant",
                collector.final_text,
                tool_steps_json=tool_steps_data,
            )

        # Emit conversation_meta pentru frontend
        yield _sse_event("conversation_meta", {
            "type": "conversation_meta",
            "conversation_id": conv_id,
            "title": conv.title,
            "is_new": is_new_conv,
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
