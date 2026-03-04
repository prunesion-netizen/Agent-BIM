"""
security_plan.py — Generare plan securitate informații (ISO 19650-5).
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.ai_client import call_llm_chat_expert
from app.models.sql_models import SecurityClassificationModel
from app.services.json_utils import extract_json as _extract_json
from app.repositories.projects_repository import (
    get_latest_project_context,
    get_project,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)


def generate_security_plan(
    db: Session,
    project_id: int,
    classification_level: str = "standard",
    sensitive_areas: str | None = None,
) -> dict:
    """Generează plan securitate conform ISO 19650-5."""
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    ctx = ctx_entry.context_json if ctx_entry else {}

    prompt = f"""Generează un plan de securitate a informațiilor conform ISO 19650-5
pentru un proiect BIM.

**Proiect**: {ctx.get('project_name', project.name)}
**Clasificare**: {classification_level}
**Zone sensibile**: {sensitive_areas or 'N/A'}
**Tip proiect**: {ctx.get('project_type', project.project_type or 'N/A')}
**CDE**: {ctx.get('cde_platform', 'N/A')}

Răspunde STRICT în format JSON:
{{
    "security_triage": {{
        "sensitivity_level": "{classification_level}",
        "requires_special_measures": true/false,
        "justification": "string"
    }},
    "access_controls": [
        {{
            "resource": "string",
            "access_level": "public/internal/restricted/confidential",
            "authorized_roles": ["string"]
        }}
    ],
    "data_handling": {{
        "storage": "string",
        "transmission": "string",
        "disposal": "string"
    }},
    "breach_protocol": {{
        "detection": "string",
        "response": "string",
        "notification": "string"
    }}
}}"""

    try:
        response_text = call_llm_chat_expert(
            context=f"Proiect: {project.name} ({project.code})",
            question=prompt,
            max_tokens=8192,
        )

        plan_json = _extract_json(response_text)

        # Upsert security classification
        existing = (
            db.query(SecurityClassificationModel)
            .filter(SecurityClassificationModel.project_id == project_id)
            .first()
        )

        if existing:
            existing.classification_level = classification_level
            existing.security_plan_json = plan_json
            existing.sensitive_areas = sensitive_areas
            entry = existing
        else:
            entry = SecurityClassificationModel(
                project_id=project_id,
                classification_level=classification_level,
                security_plan_json=plan_json,
                sensitive_areas=sensitive_areas,
            )
            db.add(entry)

        db.flush()

        log_action(db, project_id, "generate_security_plan", {
            "classification_level": classification_level,
        })

        return {
            "success": True,
            "classification_level": classification_level,
            "security_plan": plan_json,
        }
    except Exception as e:
        logger.error(f"Eroare la generare security plan: {e}")
        return {"error": f"Eroare: {str(e)}"}


def get_security_classification(db: Session, project_id: int) -> dict:
    """Returnează clasificarea securitate curentă."""
    entry = (
        db.query(SecurityClassificationModel)
        .filter(SecurityClassificationModel.project_id == project_id)
        .first()
    )

    if not entry:
        return {
            "has_security_plan": False,
            "classification_level": "unclassified",
            "security_plan": None,
        }

    return {
        "has_security_plan": True,
        "classification_level": entry.classification_level,
        "security_plan": entry.security_plan_json,
        "sensitive_areas": entry.sensitive_areas,
        "created_at": entry.created_at.isoformat() if entry.created_at else "",
    }
