"""
agent.py — SSE endpoint pentru Agent BIM autonom.

POST /api/projects/{project_id}/agent-chat
  → StreamingResponse cu SSE events (tool_call, tool_result, text_delta, done)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.agent import AgentChatRequest
from app.repositories.projects_repository import get_project
from app.services.agent_executor import run_agent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/projects/{project_id}/agent-chat")
async def api_agent_chat(
    project_id: int,
    request: AgentChatRequest,
    db: Session = Depends(get_db),
):
    """
    Agent BIM autonom cu tool use + SSE streaming.

    Primește un mesaj de la utilizator, rulează agentul care decide ce tool-uri
    să apeleze, și returnează rezultatele în timp real prin SSE.
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

    async def event_stream():
        async for event in run_agent(
            db=db,
            project_id=project_id,
            user_message=request.message,
            conversation_history=request.conversation_history,
        ):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
