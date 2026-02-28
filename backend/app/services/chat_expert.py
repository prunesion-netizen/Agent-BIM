"""
chat_expert.py — Serviciu Chat Expert BIM.
Construiește context din BEP + standarde, apelează Claude.
"""

import logging

from app.ai_client import call_llm_chat_expert

logger = logging.getLogger(__name__)

# In-memory BEP store keyed by project_code (string)
_BEP_STORE: dict[str, str] = {}


def _get_bep_for_project(project_id: str | None) -> str:
    """Returnează BEP-ul stocat pentru un proiect."""
    if project_id and project_id in _BEP_STORE:
        return _BEP_STORE[project_id]
    return ""


def store_bep(project_id: str, bep_content: str) -> None:
    """Stochează un BEP generat (in-memory)."""
    _BEP_STORE[project_id] = bep_content
    logger.info(f"BEP stored for project '{project_id}' ({len(bep_content)} chars)")


def get_stored_projects() -> list[str]:
    """Returnează lista de project_codes cu BEP stocat."""
    return list(_BEP_STORE.keys())


async def chat_expert(project_id: str | None, message: str) -> str:
    """
    Răspunde la o întrebare BIM folosind context din BEP + standarde.

    Args:
        project_id: ID-ul proiectului (sau None pentru întrebări generale)
        message: Întrebarea utilizatorului

    Returns:
        Răspunsul AI ca string
    """
    # Construiește contextul
    parts = []

    bep_content = _get_bep_for_project(project_id)
    if bep_content:
        parts.append(f"=== BEP PROIECT ===\n{bep_content}")

    # Placeholder pentru standarde și EIR
    parts.append(
        "=== STANDARDE DE REFERINȚĂ ===\n"
        "SR EN ISO 19650-1:2019 — Concepte și principii BIM\n"
        "SR EN ISO 19650-2:2021 — Faza de livrare a activelor\n"
        "SR EN ISO 19650-3:2021 — Faza operațională\n"
        "RTC 8, RTC 9 — Referențiale tehnice construcții\n"
        "BS EN 17412-1:2021 — Level of Information Need"
    )

    context = "\n\n".join(parts)

    logger.info(
        f"Chat Expert: project_id={project_id}, "
        f"context_len={len(context)}, question_len={len(message)}"
    )

    return call_llm_chat_expert(context, message)
