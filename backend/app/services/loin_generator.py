"""
loin_generator.py — Generare LOIN (Level of Information Need — BS EN 17412-1).
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.ai_client import call_llm_chat_expert
from app.models.sql_models import LoinEntryModel
from app.services.json_utils import extract_json as _extract_json
from app.repositories.projects_repository import (
    get_latest_project_context,
    get_project,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)


def generate_loin_matrix(db: Session, project_id: int) -> dict:
    """Generează matrice LOIN din ProjectContext folosind Claude."""
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    if not ctx_entry:
        return {"error": "Nu există fișă BEP. Completează mai întâi fișa proiectului."}

    ctx = ctx_entry.context_json
    disciplines = ctx.get("disciplines", [])
    lod = ctx.get("lod_specification", "LOD 300")

    prompt = f"""Generează o matrice LOIN (Level of Information Need) conform BS EN 17412-1
pentru un proiect BIM.

**Proiect**: {ctx.get('project_name', project.name)}
**Discipline**: {', '.join(disciplines)}
**LOD target**: {lod}
**Faza**: {ctx.get('project_phase', 'N/A')}

Tipuri de elemente IFC standard:
- IfcWall, IfcSlab, IfcColumn, IfcBeam, IfcDoor, IfcWindow
- IfcRoof, IfcStair, IfcRailing, IfcCurtainWall
- IfcPipe, IfcDuct, IfcCableCarrier
- IfcSpace, IfcZone, IfcSite, IfcBuilding

Răspunde STRICT în format JSON:
{{
    "entries": [
        {{
            "element_type": "string — tipul elementului IFC",
            "discipline": "string — disciplina",
            "phase": "string — faza proiectului (concept/design/construction/handover)",
            "detail_level": "string — LOD (100/200/300/350/400/500)",
            "dimensionality": "string — 2D/3D",
            "information_content": "string — ce informații trebuie incluse"
        }}
    ]
}}

Generează cel puțin o intrare per element × disciplină relevantă."""

    try:
        response_text = call_llm_chat_expert(
            context=f"Proiect: {project.name} ({project.code})",
            question=prompt,
            max_tokens=8192,
        )

        data = _extract_json(response_text)
        entries_data = data.get("entries", [])

        # Șterge LOIN vechi
        db.query(LoinEntryModel).filter(
            LoinEntryModel.project_id == project_id
        ).delete()

        created = []
        for e in entries_data:
            entry = LoinEntryModel(
                project_id=project_id,
                element_type=e.get("element_type", ""),
                discipline=e.get("discipline", ""),
                phase=e.get("phase", "design"),
                detail_level=e.get("detail_level"),
                dimensionality=e.get("dimensionality"),
                information_content=e.get("information_content"),
            )
            db.add(entry)
            created.append(entry)

        db.flush()

        log_action(db, project_id, "generate_loin", {
            "entries_count": len(created),
        })

        return {
            "success": True,
            "entries_count": len(created),
            "element_types": list(set(e.element_type for e in created)),
            "phases": list(set(e.phase for e in created)),
        }
    except Exception as e:
        logger.error(f"Eroare la generare LOIN: {e}")
        return {"error": f"Eroare la generarea LOIN: {str(e)}"}


def get_loin_matrix(db: Session, project_id: int) -> dict:
    """Returnează matricea LOIN curentă."""
    entries = (
        db.query(LoinEntryModel)
        .filter(LoinEntryModel.project_id == project_id)
        .order_by(LoinEntryModel.element_type, LoinEntryModel.discipline)
        .all()
    )

    if not entries:
        return {
            "project_id": project_id,
            "entries": [],
            "element_types": [],
            "phases": [],
            "total_entries": 0,
        }

    items = []
    for e in entries:
        items.append({
            "id": e.id,
            "element_type": e.element_type,
            "discipline": e.discipline,
            "phase": e.phase,
            "detail_level": e.detail_level,
            "dimensionality": e.dimensionality,
            "information_content": e.information_content,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        })

    return {
        "project_id": project_id,
        "entries": items,
        "element_types": sorted(set(e.element_type for e in entries)),
        "phases": sorted(set(e.phase for e in entries)),
        "total_entries": len(items),
    }
