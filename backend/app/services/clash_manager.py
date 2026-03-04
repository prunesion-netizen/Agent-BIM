"""
clash_manager.py — Management clash-uri între discipline.
"""

from __future__ import annotations

import datetime
import logging

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.sql_models import ClashRecordModel
from app.services.audit import log_action

logger = logging.getLogger(__name__)


def create_clash(
    db: Session,
    project_id: int,
    discipline_a: str,
    discipline_b: str,
    severity: str = "medium",
    description: str | None = None,
    assigned_to_role: str | None = None,
) -> dict:
    """Creează o înregistrare clash."""
    entry = ClashRecordModel(
        project_id=project_id,
        discipline_a=discipline_a,
        discipline_b=discipline_b,
        severity=severity,
        description=description,
        assigned_to_role=assigned_to_role,
        status="open",
    )
    db.add(entry)
    db.flush()

    log_action(db, project_id, "create_clash", {
        "clash_id": entry.id,
        "disciplines": f"{discipline_a} vs {discipline_b}",
        "severity": severity,
    })

    return {"success": True, "clash_id": entry.id}


def resolve_clash(
    db: Session,
    clash_id: int,
    resolution_note: str | None = None,
) -> dict:
    """Rezolvă un clash."""
    entry = db.get(ClashRecordModel, clash_id)
    if not entry:
        return {"error": "Clash negăsit."}

    entry.status = "resolved"
    entry.resolution_note = resolution_note
    entry.resolved_at = datetime.datetime.now(datetime.timezone.utc)
    db.flush()

    log_action(db, entry.project_id, "resolve_clash", {
        "clash_id": clash_id,
    })

    return {"success": True}


def get_clash_summary(db: Session, project_id: int) -> dict:
    """Returnează sumar clash-uri proiect."""
    clashes = (
        db.query(ClashRecordModel)
        .filter(ClashRecordModel.project_id == project_id)
        .order_by(desc(ClashRecordModel.created_at))
        .all()
    )

    if not clashes:
        return {
            "total": 0,
            "open": 0,
            "resolved": 0,
            "by_severity": {},
            "by_discipline_pair": [],
            "clashes": [],
        }

    open_count = sum(1 for c in clashes if c.status == "open")
    resolved_count = sum(1 for c in clashes if c.status == "resolved")

    by_severity: dict[str, int] = {}
    pair_counts: dict[str, int] = {}

    items = []
    for c in clashes:
        by_severity[c.severity] = by_severity.get(c.severity, 0) + 1
        pair_key = f"{c.discipline_a} vs {c.discipline_b}"
        pair_counts[pair_key] = pair_counts.get(pair_key, 0) + 1
        items.append({
            "id": c.id,
            "discipline_a": c.discipline_a,
            "discipline_b": c.discipline_b,
            "severity": c.severity,
            "description": c.description,
            "status": c.status,
            "assigned_to_role": c.assigned_to_role,
            "resolution_note": c.resolution_note,
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        })

    return {
        "total": len(clashes),
        "open": open_count,
        "resolved": resolved_count,
        "by_severity": by_severity,
        "by_discipline_pair": [
            {"pair": k, "count": v} for k, v in pair_counts.items()
        ],
        "clashes": items,
    }
