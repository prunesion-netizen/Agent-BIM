"""
bep_verifier.py — Serviciu de verificare conformitate BEP vs Model BIM.
Construiește contextul de verificare și apelează Claude.
"""

import logging

from app.ai_client import call_llm_bep_verifier
from app.services.chat_expert import get_bep_content

logger = logging.getLogger(__name__)


def verify_bep(
    project_code: str,
    model_summary: dict,
    project_context: dict | None = None,
) -> dict:
    """
    Verifică conformitatea BEP vs model BIM.

    Args:
        project_code: codul proiectului (pentru a prelua BEP-ul stocat)
        model_summary: rezumat tehnic al modelului BIM
        project_context: (opțional) datele proiectului din fișa BEP

    Returns:
        dict cu: report_markdown, checks, summary
    """
    bep_content = get_bep_content(project_code)
    if not bep_content:
        raise ValueError(
            f"Nu există BEP stocat pentru proiectul '{project_code}'. "
            "Generează mai întâi un BEP din fișa de proiect."
        )

    verification_context = {
        "project_context": project_context or {},
        "bep_excerpt": bep_content,
        "model_summary": model_summary,
    }

    logger.info(
        f"Verificare BEP vs Model: project={project_code}, "
        f"model_keys={list(model_summary.keys())}"
    )

    return call_llm_bep_verifier(verification_context)
