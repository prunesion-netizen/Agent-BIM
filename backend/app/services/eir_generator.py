"""
eir_generator.py — Generare EIR (Exchange Information Requirements) din ProjectContext.

Folosește Claude API pentru a genera cerințe de informare structurate.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.ai_client import call_llm_chat_expert
from app.models.sql_models import EirModel
from app.services.json_utils import extract_json as _extract_json
from app.repositories.projects_repository import (
    get_latest_project_context,
    get_project,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)


def generate_eir(db: Session, project_id: int, eir_type: str = "eir") -> dict:
    """
    Generează EIR structurat din ProjectContext folosind Claude.

    Returns:
        Dict cu content_json (information_requirements, security, acceptance_criteria).
    """
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    if not ctx_entry:
        return {"error": "Nu există fișă BEP (ProjectContext). Completează mai întâi fișa proiectului."}

    ctx = ctx_entry.context_json

    prompt = f"""Generează un document EIR (Exchange Information Requirements) conform ISO 19650-2
pentru următorul proiect BIM:

**Proiect**: {ctx.get('project_name', project.name)}
**Tip**: {ctx.get('project_type', 'N/A')}
**Client**: {ctx.get('client_name', project.client_name or 'N/A')}
**Discipline**: {', '.join(ctx.get('disciplines', []))}
**LOD**: {ctx.get('lod_specification', 'N/A')}
**Obiective BIM**: {ctx.get('bim_objectives', 'N/A')}
**Platforma CDE**: {ctx.get('cde_platform', 'N/A')}
**Format schimb**: {ctx.get('main_exchange_format', 'N/A')}
**Faza proiect**: {ctx.get('project_phase', 'N/A')}
**Echipă**: {json.dumps(ctx.get('team_roles', []), ensure_ascii=False)}

Răspunde STRICT în format JSON cu structura:
{{
    "information_requirements": [
        {{
            "category": "string (geometry/properties/documentation/coordination/delivery)",
            "requirement": "string — descrierea cerinței",
            "priority": "high/medium/low",
            "acceptance_criteria": "string — criteriul de acceptare",
            "responsible_discipline": "string"
        }}
    ],
    "security_requirements": {{
        "classification_level": "standard/restricted/confidential",
        "access_control": "string — politica acces",
        "data_handling": "string — politica date"
    }},
    "acceptance_criteria": {{
        "model_quality": "string",
        "information_completeness": "string",
        "coordination_requirements": "string"
    }},
    "delivery_schedule": {{
        "milestones": ["string"],
        "format_requirements": ["string"]
    }}
}}

Generează minim 8 cerințe de informare acoperind toate disciplinele."""

    try:
        response_text = call_llm_chat_expert(
            context=f"Proiect: {project.name} ({project.code})",
            question=prompt,
            max_tokens=8192,
        )

        # Parse JSON from response
        content_json = _extract_json(response_text)

        eir_entry = EirModel(
            project_id=project_id,
            eir_type=eir_type,
            content_json=content_json,
            version="1.0",
        )
        db.add(eir_entry)
        db.flush()

        log_action(db, project_id, "generate_eir", {
            "eir_id": eir_entry.id,
            "eir_type": eir_type,
            "requirements_count": len(content_json.get("information_requirements", [])),
        })

        return {
            "success": True,
            "eir_id": eir_entry.id,
            "content_json": content_json,
        }
    except Exception as e:
        logger.error(f"Eroare la generare EIR: {e}")
        return {"error": f"Eroare la generarea EIR: {str(e)}"}


def get_latest_eir(db: Session, project_id: int, eir_type: str = "eir") -> EirModel | None:
    """Returnează cel mai recent EIR pentru un proiect."""
    from sqlalchemy import desc
    return (
        db.query(EirModel)
        .filter(EirModel.project_id == project_id, EirModel.eir_type == eir_type)
        .order_by(desc(EirModel.created_at))
        .first()
    )


