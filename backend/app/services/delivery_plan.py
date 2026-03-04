"""
delivery_plan.py — Generare TIDP/MIDP (Task/Master Information Delivery Plan).

Generează un livrabil per disciplină × fază și compilare MIDP.
"""

from __future__ import annotations

import datetime
import json
import logging

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai_client import call_llm_chat_expert
from app.models.sql_models import DeliverableModel
from app.services.json_utils import extract_json as _extract_json
from app.repositories.projects_repository import (
    get_latest_project_context,
    get_project,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)


def generate_tidp(db: Session, project_id: int) -> dict:
    """
    Generează TIDP (Task Information Delivery Plan) din ProjectContext.
    Creează un livrabil per disciplină × fază.
    """
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    if not ctx_entry:
        return {"error": "Nu există fișă BEP. Completează mai întâi fișa proiectului."}

    ctx = ctx_entry.context_json
    disciplines = ctx.get("disciplines", [])
    if not disciplines:
        return {"error": "Nu sunt definite discipline în fișa proiectului."}

    prompt = f"""Generează un Task Information Delivery Plan (TIDP) conform ISO 19650-2
pentru următorul proiect:

**Proiect**: {ctx.get('project_name', project.name)}
**Discipline**: {', '.join(disciplines)}
**LOD**: {ctx.get('lod_specification', 'N/A')}
**Faza**: {ctx.get('project_phase', 'N/A')}
**Format**: {ctx.get('main_exchange_format', 'ifc4')}
**Echipă**: {json.dumps(ctx.get('team_roles', []), ensure_ascii=False)}

Răspunde STRICT în format JSON cu un array de livrabile:
{{
    "deliverables": [
        {{
            "title": "string — titlul livrabilului",
            "discipline": "string — disciplina (exact cum e în lista de mai sus)",
            "format": "string — formatul fișierului",
            "lod": "string — LOD necesar",
            "responsible_role": "string — rolul responsabil",
            "phase": "string — faza proiectului",
            "due_offset_days": 30
        }}
    ]
}}

Generează cel puțin un livrabil per disciplină. Include documente de coordonare."""

    try:
        response_text = call_llm_chat_expert(
            context=f"Proiect: {project.name} ({project.code})",
            question=prompt,
            max_tokens=8192,
        )

        data = _extract_json(response_text)
        deliverables_data = data.get("deliverables", [])

        # Șterge livrabilele vechi generate automat
        db.query(DeliverableModel).filter(
            DeliverableModel.project_id == project_id
        ).delete()

        created = []
        base_date = datetime.date.today()
        for d in deliverables_data:
            due_offset = d.get("due_offset_days", 30)
            due_date = base_date + datetime.timedelta(days=due_offset)

            entry = DeliverableModel(
                project_id=project_id,
                title=d.get("title", "Livrabil"),
                discipline=d.get("discipline", disciplines[0] if disciplines else "general"),
                format=d.get("format", "ifc4"),
                lod=d.get("lod"),
                responsible_role=d.get("responsible_role"),
                due_date=due_date,
                phase=d.get("phase"),
                status="planned",
            )
            db.add(entry)
            created.append(entry)

        db.flush()

        log_action(db, project_id, "generate_tidp", {
            "deliverables_count": len(created),
            "disciplines": disciplines,
        })

        return {
            "success": True,
            "deliverables_count": len(created),
            "deliverables": [
                {
                    "id": e.id,
                    "title": e.title,
                    "discipline": e.discipline,
                    "format": e.format,
                    "lod": e.lod,
                    "responsible_role": e.responsible_role,
                    "due_date": e.due_date.isoformat() if e.due_date else None,
                    "phase": e.phase,
                    "status": e.status,
                }
                for e in created
            ],
        }
    except Exception as e:
        logger.error(f"Eroare la generare TIDP: {e}")
        return {"error": f"Eroare la generarea TIDP: {str(e)}"}


def get_delivery_plan(db: Session, project_id: int) -> dict:
    """Returnează planul de livrare curent (TIDP/MIDP summary)."""
    deliverables = (
        db.query(DeliverableModel)
        .filter(DeliverableModel.project_id == project_id)
        .order_by(DeliverableModel.discipline, DeliverableModel.due_date)
        .all()
    )

    if not deliverables:
        return {
            "total_deliverables": 0,
            "by_discipline": {},
            "by_status": {},
            "completion_percent": 0.0,
            "overdue_count": 0,
            "deliverables": [],
        }

    by_discipline: dict[str, int] = {}
    by_status: dict[str, int] = {}
    completed = 0
    overdue = 0
    today = datetime.date.today()

    items = []
    for d in deliverables:
        by_discipline[d.discipline] = by_discipline.get(d.discipline, 0) + 1
        by_status[d.status] = by_status.get(d.status, 0) + 1
        if d.status in ("completed", "delivered"):
            completed += 1
        if d.due_date and d.due_date < today and d.status not in ("completed", "delivered"):
            overdue += 1
        items.append({
            "id": d.id,
            "title": d.title,
            "discipline": d.discipline,
            "format": d.format,
            "lod": d.lod,
            "responsible_role": d.responsible_role,
            "due_date": d.due_date.isoformat() if d.due_date else None,
            "phase": d.phase,
            "status": d.status,
        })

    total = len(deliverables)

    return {
        "total_deliverables": total,
        "by_discipline": by_discipline,
        "by_status": by_status,
        "completion_percent": round((completed / total) * 100, 1) if total else 0.0,
        "overdue_count": overdue,
        "deliverables": items,
    }


def update_deliverable_status(
    db: Session, deliverable_id: int, new_status: str
) -> dict:
    """Actualizează statusul unui livrabil."""
    entry = db.get(DeliverableModel, deliverable_id)
    if not entry:
        return {"error": "Livrabil negăsit."}
    old_status = entry.status
    entry.status = new_status
    db.flush()

    log_action(db, entry.project_id, "update_deliverable", {
        "deliverable_id": deliverable_id,
        "from": old_status,
        "to": new_status,
    })

    return {
        "success": True,
        "deliverable_id": deliverable_id,
        "old_status": old_status,
        "new_status": new_status,
    }
