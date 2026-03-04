"""
raci_generator.py — Generare matrice RACI din team_roles + disciplines.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai_client import call_llm_chat_expert
from app.models.sql_models import RaciEntryModel
from app.services.json_utils import extract_json as _extract_json
from app.repositories.projects_repository import (
    get_latest_project_context,
    get_project,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)

# Roluri BIM standard când team_roles nu e definit
DEFAULT_BIM_ROLES = [
    {"role_code": "BIM_MGR", "role_name": "BIM Manager"},
    {"role_code": "BIM_COORD", "role_name": "BIM Coordinator"},
    {"role_code": "PROJ_LEAD", "role_name": "Project Lead"},
    {"role_code": "ARCH", "role_name": "Arhitect"},
    {"role_code": "STR", "role_name": "Inginer Structuri"},
    {"role_code": "MEP", "role_name": "Inginer MEP"},
    {"role_code": "CLIENT", "role_name": "Client/Beneficiar"},
]


def generate_raci_matrix(db: Session, project_id: int) -> dict:
    """Generează matrice RACI din ProjectContext folosind Claude."""
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    if not ctx_entry:
        return {"error": "Nu există fișă BEP. Completează mai întâi fișa proiectului."}

    ctx = ctx_entry.context_json
    team_roles = ctx.get("team_roles", [])
    disciplines = ctx.get("disciplines", [])

    if not team_roles:
        team_roles = DEFAULT_BIM_ROLES
        logger.info("team_roles lipsă, se folosesc roluri BIM implicite.")

    prompt = f"""Generează o matrice RACI (Responsible, Accountable, Consulted, Informed)
pentru un proiect BIM conform ISO 19650-2.

**Proiect**: {ctx.get('project_name', project.name)}
**Discipline**: {', '.join(disciplines)}
**Roluri echipă**: {json.dumps(team_roles, ensure_ascii=False)}
**Faza**: {ctx.get('project_phase', 'N/A')}

Task-uri BIM standard de inclus:
- Definire cerințe informare (EIR)
- Elaborare BEP (BIM Execution Plan)
- Modelare 3D per disciplină
- Coordonare interdisciplinară (clash detection)
- Verificare calitate model (model checking)
- Livrare informații (information delivery)
- Revizuire și aprobare documente
- Managementul CDE
- Generare documente (planuri, secțiuni)
- Predare/handover as-built

Răspunde STRICT în format JSON:
{{
    "entries": [
        {{
            "task_name": "string",
            "role_code": "string — codul rolului din echipă",
            "assignment": "R/A/C/I",
            "discipline": "string sau null",
            "phase": "string sau null"
        }}
    ]
}}

Fiecare task trebuie să aibă cel puțin un R (Responsible) și un A (Accountable)."""

    try:
        response_text = call_llm_chat_expert(
            context=f"Proiect: {project.name} ({project.code})",
            question=prompt,
            max_tokens=8192,
        )

        data = _extract_json(response_text)
        entries_data = data.get("entries", [])

        # Șterge RACI vechi
        db.query(RaciEntryModel).filter(
            RaciEntryModel.project_id == project_id
        ).delete()

        created = []
        for e in entries_data:
            assignment = e.get("assignment", "").upper()
            if assignment not in ("R", "A", "C", "I"):
                continue
            entry = RaciEntryModel(
                project_id=project_id,
                task_name=e.get("task_name", ""),
                role_code=e.get("role_code", ""),
                assignment=assignment,
                discipline=e.get("discipline"),
                phase=e.get("phase"),
            )
            db.add(entry)
            created.append(entry)

        db.flush()

        log_action(db, project_id, "generate_raci", {
            "entries_count": len(created),
        })

        return {
            "success": True,
            "entries_count": len(created),
            "tasks": list(set(e.task_name for e in created)),
            "roles": list(set(e.role_code for e in created)),
        }
    except Exception as e:
        logger.error(f"Eroare la generare RACI: {e}")
        return {"error": f"Eroare la generarea RACI: {str(e)}"}


def get_raci_matrix(db: Session, project_id: int) -> dict:
    """Returnează matricea RACI curentă."""
    entries = (
        db.query(RaciEntryModel)
        .filter(RaciEntryModel.project_id == project_id)
        .order_by(RaciEntryModel.task_name, RaciEntryModel.role_code)
        .all()
    )

    if not entries:
        return {
            "project_id": project_id,
            "entries": [],
            "tasks": [],
            "roles": [],
            "total_entries": 0,
        }

    items = []
    for e in entries:
        items.append({
            "id": e.id,
            "task_name": e.task_name,
            "role_code": e.role_code,
            "assignment": e.assignment,
            "discipline": e.discipline,
            "phase": e.phase,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        })

    return {
        "project_id": project_id,
        "entries": items,
        "tasks": sorted(set(e.task_name for e in entries)),
        "roles": sorted(set(e.role_code for e in entries)),
        "total_entries": len(items),
    }
