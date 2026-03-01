"""
chat_expert.py — Serviciu Chat Expert BIM.
Construiește context din BEP + standarde, apelează Claude.
Include și modul Copilot cu context complet de proiect.
"""

import logging

from app.ai_client import call_llm_chat_expert, call_llm_chat_copilot

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


def get_bep_content(project_code: str) -> str | None:
    """Returnează conținutul BEP pentru un proiect (sau None)."""
    return _BEP_STORE.get(project_code)


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


# ── Copilot (context complet de proiect) ────────────────────────────────────

_STANDARDE = (
    "SR EN ISO 19650-1:2019 — Concepte și principii BIM\n"
    "SR EN ISO 19650-2:2021 — Faza de livrare a activelor\n"
    "SR EN ISO 19650-3:2021 — Faza operațională\n"
    "RTC 8, RTC 9 — Referențiale tehnice construcții\n"
    "BS EN 17412-1:2021 — Level of Information Need"
)


def _truncate_bep(bep_markdown: str, max_chars: int = 12000) -> str:
    """Truncează BEP la max_chars caractere (păstrează începutul cu structura)."""
    if len(bep_markdown) <= max_chars:
        return bep_markdown
    return bep_markdown[:max_chars] + "\n\n[... trunchiat ...]"


def build_copilot_context(chat_context: dict) -> str:
    """Serializează contextul complet al proiectului în secțiuni text."""
    sections: list[str] = []

    # Proiect
    proj = chat_context.get("project")
    if proj:
        sections.append(
            "=== PROIECT ===\n"
            f"Nume: {proj.get('name', 'N/A')}\n"
            f"Cod: {proj.get('code', 'N/A')}\n"
            f"Client: {proj.get('client_name') or 'N/A'}\n"
            f"Tip: {proj.get('project_type') or 'N/A'}\n"
            f"Status: {proj.get('status', 'N/A')}"
        )

    # Fișa proiect (ProjectContext)
    ctx = chat_context.get("project_context")
    if ctx:
        lines = ["=== FISA PROIECT ==="]
        for key in ("project_phase", "disciplines", "cde_platform", "lod_geometry",
                     "lod_information", "bim_objectives", "kpi_metrics",
                     "bim_software", "exchange_formats"):
            val = ctx.get(key)
            if val:
                lines.append(f"{key}: {val}")
        sections.append("\n".join(lines))

    # BEP
    bep = chat_context.get("bep")
    if bep:
        content = _truncate_bep(bep.get("content_markdown", ""))
        sections.append(
            f"=== BEP (v{bep.get('version', '?')}, {bep.get('created_at', '?')}) ===\n"
            + content
        )

    # Verificări
    verif = chat_context.get("verifications")
    if verif and verif.get("total_count", 0) > 0:
        latest = verif.get("latest")
        lines = ["=== ULTIMA VERIFICARE ==="]
        if latest:
            lines.append(f"Status general: {latest.get('summary_status', 'N/A')}")
            lines.append(f"Fail: {latest.get('fail_count', 0)}, Warning: {latest.get('warning_count', 0)}")
            lines.append(f"Data: {latest.get('created_at', 'N/A')}")
            report = latest.get("report_markdown", "")
            if report:
                lines.append(f"\nRaport:\n{report}")
        history = verif.get("history", [])
        if len(history) > 1:
            lines.append(f"\nIstoric ({len(history)} verificări):")
            for h in history[:5]:
                lines.append(
                    f"  - {h.get('created_at', '?')}: {h.get('summary_status', '?')} "
                    f"(fail={h.get('fail_count', 0)}, warn={h.get('warning_count', 0)})"
                )
        sections.append("\n".join(lines))

    # Standarde
    sections.append(f"=== STANDARDE DE REFERINȚĂ ===\n{_STANDARDE}")

    return "\n\n".join(sections)


async def chat_expert_copilot(chat_context: dict, message: str) -> str:
    """
    Copilot BIM — răspunde folosind contextul complet al proiectului.
    """
    context = build_copilot_context(chat_context)

    logger.info(
        f"Chat Copilot: project={chat_context.get('project', {}).get('code', '?')}, "
        f"context_len={len(context)}, question_len={len(message)}"
    )

    return call_llm_chat_copilot(context, message)
