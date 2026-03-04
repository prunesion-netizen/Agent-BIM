"""
kpi_tracker.py — Tracking KPI-uri proiect BIM.
"""

from __future__ import annotations

import datetime
import logging

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.sql_models import (
    ClashRecordModel,
    DeliverableModel,
    KpiMeasurementModel,
)
from app.repositories.projects_repository import (
    get_latest_generated_document,
    get_latest_project_context,
    get_latest_uploaded_file,
    get_project,
    list_verification_reports,
)
from app.services.audit import log_action
from app.services.project_health import compute_project_health

logger = logging.getLogger(__name__)

# Definiții KPI standard
KPI_DEFINITIONS = [
    {"name": "bep_compliance", "category": "quality", "target": 100.0, "description": "Scor completitudine BEP"},
    {"name": "delivery_on_time", "category": "delivery", "target": 100.0, "description": "% livrabile la termen"},
    {"name": "clash_resolution_rate", "category": "coordination", "target": 100.0, "description": "% clash-uri rezolvate"},
    {"name": "model_completeness", "category": "quality", "target": 100.0, "description": "Scor completitudine model"},
    {"name": "verification_score", "category": "quality", "target": 100.0, "description": "Scor ultima verificare BEP"},
]


def compute_current_kpis(db: Session, project_id: int) -> dict:
    """
    Calculează KPI-urile curente ale proiectului și le salvează.
    """
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    today = datetime.date.today()
    kpis = []

    # 1. BEP Compliance (health score)
    health = compute_project_health(db, project_id)
    health_score = health.get("score", 0)
    kpis.append({
        "name": "bep_compliance",
        "category": "quality",
        "value": float(health_score),
        "target": 100.0,
    })

    # 2. Delivery on-time
    deliverables = (
        db.query(DeliverableModel)
        .filter(DeliverableModel.project_id == project_id)
        .all()
    )
    if deliverables:
        total = len(deliverables)
        overdue = sum(
            1 for d in deliverables
            if d.due_date and d.due_date < today
            and d.status not in ("completed", "delivered")
        )
        on_time_pct = round(((total - overdue) / total) * 100, 1)
    else:
        on_time_pct = 100.0
    kpis.append({
        "name": "delivery_on_time",
        "category": "delivery",
        "value": on_time_pct,
        "target": 100.0,
    })

    # 3. Clash resolution rate
    clashes = (
        db.query(ClashRecordModel)
        .filter(ClashRecordModel.project_id == project_id)
        .all()
    )
    if clashes:
        resolved = sum(1 for c in clashes if c.status == "resolved")
        clash_rate = round((resolved / len(clashes)) * 100, 1)
    else:
        clash_rate = 100.0
    kpis.append({
        "name": "clash_resolution_rate",
        "category": "coordination",
        "value": clash_rate,
        "target": 100.0,
    })

    # 4. Model completeness (based on IFC)
    ifc_file = get_latest_uploaded_file(db, project_id, "ifc")
    model_score = 100.0 if ifc_file else 0.0
    kpis.append({
        "name": "model_completeness",
        "category": "quality",
        "value": model_score,
        "target": 100.0,
    })

    # 5. Verification score
    reports = list_verification_reports(db, project_id)
    if reports:
        latest = reports[0]
        fail_count = latest.fail_count or 0
        warn_count = latest.warning_count or 0
        # Simple scoring: 100 - (fails * 15 + warnings * 5), min 0
        verif_score = max(0.0, 100.0 - fail_count * 15 - warn_count * 5)
    else:
        verif_score = 0.0
    kpis.append({
        "name": "verification_score",
        "category": "quality",
        "value": verif_score,
        "target": 100.0,
    })

    # Salvează măsurătorile
    for kpi in kpis:
        entry = KpiMeasurementModel(
            project_id=project_id,
            kpi_name=kpi["name"],
            category=kpi["category"],
            value=kpi["value"],
            target_value=kpi["target"],
            measurement_date=today,
        )
        db.add(entry)

    db.flush()

    # Scor overall = media KPI-urilor
    overall = round(sum(k["value"] for k in kpis) / len(kpis), 1) if kpis else 0.0

    return {
        "project_id": project_id,
        "kpis": kpis,
        "categories": sorted(set(k["category"] for k in kpis)),
        "overall_score": overall,
        "measurement_date": today.isoformat(),
    }


def get_kpi_dashboard(db: Session, project_id: int) -> dict:
    """Returnează dashboard KPI cu ultimele măsurători."""
    # Compute fresh KPIs
    result = compute_current_kpis(db, project_id)
    if "error" in result:
        return result

    # Get historical data for trends
    history = (
        db.query(KpiMeasurementModel)
        .filter(KpiMeasurementModel.project_id == project_id)
        .order_by(desc(KpiMeasurementModel.measurement_date))
        .limit(50)
        .all()
    )

    trends: dict[str, list] = {}
    for m in history:
        if m.kpi_name not in trends:
            trends[m.kpi_name] = []
        trends[m.kpi_name].append({
            "date": m.measurement_date.isoformat(),
            "value": m.value,
        })

    result["trends"] = trends
    return result
