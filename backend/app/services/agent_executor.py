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
from dataclasses import dataclass, field
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.ai_client import _get_client, MODEL
from app.services.agent_prompts import build_system_prompt
from app.services.agent_tools import AGENT_TOOLS, execute_tool
from app.repositories.projects_repository import (
    get_project,
    get_latest_project_context,
    get_latest_generated_document,
    get_latest_uploaded_file,
    list_verification_reports,
)
from app.schemas.converters import project_model_to_read

logger = logging.getLogger(__name__)

MAX_AGENT_TURNS = 10  # limită de siguranță pentru loop-ul agentului


@dataclass
class AgentResult:
    """Rezultatul colectat din run_agent() pentru persistență."""
    final_text: str = ""
    tool_steps: list[dict] = field(default_factory=list)


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


def _build_context_summary(db: Session, project_id: int) -> dict | None:
    """Construiește un sumar de context pentru system prompt."""
    summary: dict = {}

    # Context BEP
    ctx_entry = get_latest_project_context(db, project_id)
    if ctx_entry and ctx_entry.context_json:
        ctx = ctx_entry.context_json
        summary["disciplines"] = ctx.get("disciplines", [])
        summary["bep_version"] = ctx.get("bep_version")

    # BEP generat?
    bep_doc = get_latest_generated_document(db, project_id, "bep")
    summary["has_bep"] = bep_doc is not None

    # IFC importat?
    ifc_file = get_latest_uploaded_file(db, project_id, "ifc")
    summary["has_ifc"] = ifc_file is not None

    # Ultima verificare
    reports = list_verification_reports(db, project_id)
    if reports:
        latest = reports[0]
        summary["last_verification_status"] = latest.summary_status

    # Health score (calcul simplu inline, fără import circular)
    if ctx_entry and ctx_entry.context_json:
        critical_fields = [
            "project_name", "disciplines", "bim_objectives",
            "lod_specification", "cde_platform", "team_roles",
        ]
        filled = sum(
            1 for f in critical_fields
            if ctx_entry.context_json.get(f) not in (None, "", [])
        )
        summary["health_score"] = round((filled / len(critical_fields)) * 100)
    else:
        summary["health_score"] = 0

    # Alerte
    alerts = []
    if not summary["has_bep"] and ctx_entry:
        alerts.append("Fișa BEP e completată dar BEP-ul nu a fost generat încă")
    if summary["has_bep"] and not reports:
        alerts.append("BEP-ul nu a fost verificat încă")
    if summary.get("last_verification_status") == "fail":
        alerts.append("Ultima verificare BEP a avut status FAIL")
    summary["alerts"] = alerts

    return summary if summary else None


async def run_agent(
    db: Session,
    project_id: int,
    user_message: str,
    conversation_history: list[dict] | None = None,
    collector: AgentResult | None = None,
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
        collector: Dacă e furnizat, colectează textul final și tool_steps

    Yields:
        SSE events ca string-uri formatate
    """
    # 1) Încarcă info proiect + context extins pentru system prompt
    project = get_project(db, project_id)
    project_info = None
    context_summary = None
    if project:
        project_info = project_model_to_read(project).model_dump()
        context_summary = _build_context_summary(db, project_id)

    system_prompt = build_system_prompt(project_info, context_summary)

    # 2) Construiește mesajele inițiale
    messages = _build_messages(user_message, conversation_history)

    # 3) Agent loop
    client = _get_client()
    turns = 0
    all_text_parts: list[str] = []

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
            all_text_parts.append(full_text)
            yield _sse_event("text_delta", {
                "type": "text_delta",
                "content": full_text,
            })

        # 6) Dacă nu sunt tool calls, am terminat
        if not tool_uses:
            if collector is not None:
                collector.final_text = "\n\n".join(all_text_parts)
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

            # Colectăm tool step pentru persistență
            if collector is not None:
                collector.tool_steps.append({
                    "call_id": call_id,
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "result": result,
                    "duration_ms": duration_ms,
                    "status": "error" if result.get("error") else "completed",
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
            if collector is not None:
                collector.final_text = "\n\n".join(all_text_parts)
            yield _sse_event("done", {"type": "done"})
            return

        # Altfel, continuăm loop-ul (stop_reason == "tool_use")

    # Limita de iterații atinsă
    limit_text = (
        "Am atins limita de pași pentru această conversație. "
        "Te rog reformulează cererea sau continuă cu un mesaj nou."
    )
    all_text_parts.append(limit_text)
    if collector is not None:
        collector.final_text = "\n\n".join(all_text_parts)
    yield _sse_event("text_delta", {
        "type": "text_delta",
        "content": limit_text,
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
