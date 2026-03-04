"""
handover.py — Serviciu handover checklist (ISO 19650-3).
"""

from __future__ import annotations

import datetime
import json
import logging

from sqlalchemy.orm import Session

from app.ai_client import call_llm_chat_expert
from app.models.sql_models import HandoverChecklistModel
from app.services.json_utils import extract_json as _extract_json
from app.repositories.projects_repository import (
    get_latest_project_context,
    get_project,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)

# Categorii standard handover
HANDOVER_CATEGORIES = [
    "modele_as_built",
    "documentatie",
    "date_operare",
    "clasificare_spatii",
    "sisteme_mep",
    "coordonare_finala",
]


def generate_handover_checklist(db: Session, project_id: int) -> dict:
    """Generează checklist handover din ProjectContext."""
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    if not ctx_entry:
        return {"error": "Nu există fișă BEP."}

    ctx = ctx_entry.context_json
    disciplines = ctx.get("disciplines", [])

    prompt = f"""Generează un checklist de predare (handover) conform ISO 19650-3
pentru un proiect BIM.

**Proiect**: {ctx.get('project_name', project.name)}
**Discipline**: {', '.join(disciplines)}
**Faza**: {ctx.get('project_phase', 'N/A')}

Categorii: modele_as_built, documentatie, date_operare, clasificare_spatii, sisteme_mep, coordonare_finala

Răspunde STRICT în format JSON:
{{
    "items": [
        {{
            "item_name": "string — denumirea elementului de verificat",
            "category": "string — categoria din lista de mai sus"
        }}
    ]
}}

Generează cel puțin 15 elemente acoperind toate categoriile."""

    try:
        response_text = call_llm_chat_expert(
            context=f"Proiect: {project.name} ({project.code})",
            question=prompt,
            max_tokens=8192,
        )

        data = _extract_json(response_text)
        items_data = data.get("items", [])

        # Șterge items vechi
        db.query(HandoverChecklistModel).filter(
            HandoverChecklistModel.project_id == project_id
        ).delete()

        created = []
        for item in items_data:
            entry = HandoverChecklistModel(
                project_id=project_id,
                item_name=item.get("item_name", ""),
                category=item.get("category", "documentatie"),
            )
            db.add(entry)
            created.append(entry)

        db.flush()

        log_action(db, project_id, "generate_handover", {
            "items_count": len(created),
        })

        return {
            "success": True,
            "items_count": len(created),
        }
    except Exception as e:
        logger.error(f"Eroare la generare handover: {e}")
        return {"error": f"Eroare la generarea handover: {str(e)}"}


def get_handover_status(db: Session, project_id: int) -> dict:
    """Returnează statusul handover checklist."""
    items = (
        db.query(HandoverChecklistModel)
        .filter(HandoverChecklistModel.project_id == project_id)
        .order_by(HandoverChecklistModel.category, HandoverChecklistModel.item_name)
        .all()
    )

    if not items:
        return {
            "total_items": 0,
            "completed_items": 0,
            "completion_percent": 0.0,
            "by_category": {},
            "items": [],
        }

    by_category: dict[str, dict] = {}
    completed = 0

    item_list = []
    for item in items:
        if item.category not in by_category:
            by_category[item.category] = {"total": 0, "completed": 0}
        by_category[item.category]["total"] += 1
        if item.is_completed:
            completed += 1
            by_category[item.category]["completed"] += 1
        item_list.append({
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "is_completed": item.is_completed,
            "completed_by": item.completed_by,
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        })

    total = len(items)

    return {
        "total_items": total,
        "completed_items": completed,
        "completion_percent": round((completed / total) * 100, 1) if total else 0.0,
        "by_category": by_category,
        "items": item_list,
    }


def toggle_handover_item(
    db: Session, item_id: int, completed_by: str = "system"
) -> dict:
    """Toggle completare element handover."""
    item = db.get(HandoverChecklistModel, item_id)
    if not item:
        return {"error": "Element negăsit."}

    item.is_completed = not item.is_completed
    if item.is_completed:
        item.completed_by = completed_by
        item.completed_at = datetime.datetime.now(datetime.timezone.utc)
    else:
        item.completed_by = None
        item.completed_at = None
    db.flush()

    return {"success": True, "is_completed": item.is_completed}
