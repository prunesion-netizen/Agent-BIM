"""
bep_generator.py — Serviciu de generare BEP.
Convertește ProjectContext în dict, apelează Claude, returnează rezultatul.
"""

import logging

from app.schemas.project_context import ProjectContext
from app.ai_client import call_llm

logger = logging.getLogger(__name__)


def generate_bep(project_context: ProjectContext) -> dict:
    """
    Generează un BEP complet pe baza ProjectContext.

    Returns:
        dict cu:
        - bep_markdown: string Markdown cu BEP-ul generat
        - project_code: codul proiectului
        - bep_version: versiunea BEP
    """
    # Serializare la dict (cu date convertite la string)
    ctx_dict = project_context.model_dump(mode="json")

    logger.info(
        f"Generare BEP pentru proiectul '{project_context.project_name}' "
        f"(cod: {project_context.project_code}, faza: {project_context.current_phase})"
    )

    bep_markdown = call_llm(ctx_dict)

    return {
        "bep_markdown": bep_markdown,
        "project_code": project_context.project_code,
        "bep_version": project_context.bep_version,
    }
