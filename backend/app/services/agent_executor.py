"""
agent_executor.py — Agent loop cu Claude tool_use API + SSE streaming.

Flux:
  mesaj user → Claude API cu tools → execuție tool-uri → loop
  → SSE events yield până la stop_reason="end_turn"
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.ai_client import _get_client, MODEL
from app.services.agent_prompts import build_system_prompt
from app.services.agent_tools import AGENT_TOOLS, execute_tool
from app.repositories.projects_repository import get_project
from app.schemas.converters import project_model_to_read

logger = logging.getLogger(__name__)

MAX_AGENT_TURNS = 10  # limită de siguranță pentru loop-ul agentului


def _sse_event(event_type: str, data: dict) -> str:
    """Formatează un SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _build_messages(
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> list[dict]:
    """Construiește lista de mesaje pentru Claude API."""
    messages = []

    if conversation_history:
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})
    return messages


async def run_agent(
    db: Session,
    project_id: int,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Rulează agentul BIM și yield-uiește SSE events.

    SSE event types:
    - tool_call: agentul a decis să apeleze un tool
    - tool_result: rezultatul execuției tool-ului
    - text_delta: text de răspuns de la agent
    - error: eroare
    - done: agentul a terminat

    Args:
        db: Sesiune SQLAlchemy
        project_id: ID-ul proiectului curent
        user_message: Mesajul utilizatorului
        conversation_history: Istoricul conversației (opțional)

    Yields:
        SSE events ca string-uri formatate
    """
    # 1) Încarcă info proiect pentru system prompt
    project = get_project(db, project_id)
    project_info = None
    if project:
        project_info = project_model_to_read(project).model_dump()

    system_prompt = build_system_prompt(project_info)

    # 2) Construiește mesajele inițiale
    messages = _build_messages(user_message, conversation_history)

    # 3) Agent loop
    client = _get_client()
    turns = 0

    while turns < MAX_AGENT_TURNS:
        turns += 1

        try:
            # Apelul Claude este sincron → rulăm în thread separat
            response = await asyncio.to_thread(
                client.messages.create,
                model=MODEL,
                max_tokens=4096,
                system=system_prompt,
                tools=AGENT_TOOLS,
                messages=messages,
            )
        except Exception as e:
            logger.error(f"Eroare la apelul Claude: {e}")
            yield _sse_event("error", {
                "type": "error",
                "message": f"Eroare la comunicarea cu AI: {str(e)}",
            })
            yield _sse_event("done", {"type": "done"})
            return

        # 4) Procesăm răspunsul
        stop_reason = response.stop_reason
        assistant_content = response.content

        # Colectăm textul și tool_use blocks
        text_parts = []
        tool_uses = []

        for block in assistant_content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        # 5) Emitem text dacă există
        if text_parts:
            full_text = "".join(text_parts)
            yield _sse_event("text_delta", {
                "type": "text_delta",
                "content": full_text,
            })

        # 6) Dacă nu sunt tool calls, am terminat
        if not tool_uses:
            yield _sse_event("done", {"type": "done"})
            return

        # 7) Procesăm fiecare tool call
        # Adăugăm răspunsul asistentului la mesaje (pentru continuarea conversației)
        messages.append({
            "role": "assistant",
            "content": [_content_block_to_dict(b) for b in assistant_content],
        })

        tool_results_for_claude = []

        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input
            call_id = tool_use.id

            # Emitem evenimentul tool_call
            yield _sse_event("tool_call", {
                "type": "tool_call",
                "tool_name": tool_name,
                "tool_input": tool_input,
                "call_id": call_id,
            })

            # Executăm tool-ul
            start_time = time.time()
            try:
                result = await asyncio.to_thread(
                    execute_tool, db, tool_name, tool_input
                )
            except Exception as e:
                logger.error(f"Eroare la execuția tool '{tool_name}': {e}")
                result = {"error": f"Eroare internă: {str(e)}"}

            duration_ms = int((time.time() - start_time) * 1000)

            # Emitem evenimentul tool_result
            yield _sse_event("tool_result", {
                "type": "tool_result",
                "call_id": call_id,
                "tool_name": tool_name,
                "result": result,
                "duration_ms": duration_ms,
            })

            # Pregătim rezultatul pentru Claude
            tool_results_for_claude.append({
                "type": "tool_result",
                "tool_use_id": call_id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        # 8) Adăugăm tool results la mesaje
        messages.append({
            "role": "user",
            "content": tool_results_for_claude,
        })

        # 9) Dacă stop_reason e "end_turn", am terminat
        if stop_reason == "end_turn":
            yield _sse_event("done", {"type": "done"})
            return

        # Altfel, continuăm loop-ul (stop_reason == "tool_use")

    # Limita de iterații atinsă
    yield _sse_event("text_delta", {
        "type": "text_delta",
        "content": (
            "Am atins limita de pași pentru această conversație. "
            "Te rog reformulează cererea sau continuă cu un mesaj nou."
        ),
    })
    yield _sse_event("done", {"type": "done"})


def _content_block_to_dict(block) -> dict:
    """Convertește un content block din răspunsul Claude în dict serializabil."""
    if block.type == "text":
        return {"type": "text", "text": block.text}
    elif block.type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    return {"type": block.type}
