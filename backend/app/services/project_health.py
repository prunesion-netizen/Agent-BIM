"""
project_health.py — Diagnostic sănătate proiect BIM.

Calculează un scor de completitudine (0-100%) bazat pe câmpurile
ProjectContext, alertează pe câmpuri lipsă, și oferă recomandări.
"""

from __future__ import annotations

import datetime
import logging

from sqlalchemy.orm import Session

from app.repositories.projects_repository import (
    get_project,
    get_latest_project_context,
    get_latest_generated_document,
    get_latest_uploaded_file,
    list_verification_reports,
)

logger = logging.getLogger(__name__)

# Câmpuri critice din ProjectContext cu greutatea lor (total = 100)
_FIELD_WEIGHTS: dict[str, int] = {
    "project_name": 5,
    "project_type": 5,
    "client_name": 5,
    "disciplines": 10,
    "bim_objectives": 10,
    "lod_specification": 8,
    "cde_platform": 8,
    "main_exchange_format": 5,
    "team_roles": 10,
    "software_list": 8,
    "project_phase": 5,
    "coordination_method": 5,
    "naming_convention": 5,
    "delivery_milestones": 5,
    "bep_version": 3,
    "georeferencing": 3,
}


def compute_project_health(db: Session, project_id: int) -> dict:
    """
    Calculează sănătatea proiectului BIM.

    Returns:
        Dict cu:
        - score: 0-100 (completitudine)
        - missing_fields: lista câmpurilor lipsă
        - alerts: lista alertelor temporale
        - recommendations: lista recomandărilor ordonate
        - has_bep: bool
        - has_ifc: bool
        - has_verification: bool
        - bep_version: str | None
        - last_verification_status: str | None
    """
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    result: dict = {
        "project_name": project.name,
        "project_code": project.code,
        "project_status": project.status,
        "score": 0,
        "missing_fields": [],
        "alerts": [],
        "recommendations": [],
        "has_bep": False,
        "has_ifc": False,
        "has_verification": False,
        "bep_version": None,
        "last_verification_status": None,
    }

    # ── Scor completitudine context ──────────────────────────────────────
    ctx_entry = get_latest_project_context(db, project_id)
    total_weight = sum(_FIELD_WEIGHTS.values())
    earned = 0

    if ctx_entry and ctx_entry.context_json:
        ctx = ctx_entry.context_json
        for field_name, weight in _FIELD_WEIGHTS.items():
            value = ctx.get(field_name)
            if value and value != "" and value != []:
                earned += weight
            else:
                result["missing_fields"].append(field_name)
    else:
        result["missing_fields"] = list(_FIELD_WEIGHTS.keys())
        result["alerts"].append("Nu există fișă BEP (ProjectContext) definită.")
        result["recommendations"].append(
            "Completează fișa proiectului din tab-ul 'Fișa BEP' — este primul pas."
        )

    result["score"] = round((earned / total_weight) * 100) if total_weight else 0

    # ── BEP generat ──────────────────────────────────────────────────────
    bep_doc = get_latest_generated_document(db, project_id, "bep")
    if bep_doc:
        result["has_bep"] = True
        result["bep_version"] = bep_doc.version
        # Alertă dacă BEP-ul e vechi
        if bep_doc.created_at:
            days_old = (datetime.datetime.now(datetime.timezone.utc) - bep_doc.created_at).days
            if days_old > 30:
                result["alerts"].append(
                    f"BEP-ul a fost generat acum {days_old} zile. "
                    "Consideră regenerarea pentru a reflecta schimbările recente."
                )
    else:
        result["recommendations"].append(
            "Generează un BEP — documentul central al managementului BIM."
        )

    # ── Model IFC ────────────────────────────────────────────────────────
    ifc_file = get_latest_uploaded_file(db, project_id, "ifc")
    if ifc_file:
        result["has_ifc"] = True
    else:
        result["recommendations"].append(
            "Importă un model IFC pentru analiza automată a disciplinelor și categoriilor."
        )

    # ── Verificare BEP ───────────────────────────────────────────────────
    reports = list_verification_reports(db, project_id)
    if reports:
        result["has_verification"] = True
        latest = reports[0]
        result["last_verification_status"] = latest.summary_status
        if latest.summary_status == "fail":
            result["alerts"].append(
                f"Ultima verificare BEP a avut status FAIL "
                f"({latest.fail_count} neconformități). Rezolvă problemele identificate."
            )
        elif latest.summary_status == "warning":
            result["alerts"].append(
                f"Ultima verificare BEP are {latest.warning_count} avertismente."
            )
        # Alertă dacă verificarea e veche
        if latest.created_at:
            days_old = (datetime.datetime.now(datetime.timezone.utc) - latest.created_at).days
            if days_old > 30:
                result["alerts"].append(
                    f"Ultima verificare BEP a fost acum {days_old} zile. "
                    "Rulează o verificare nouă."
                )
    elif bep_doc:
        result["recommendations"].append(
            "Rulează o verificare BEP vs model pentru a identifica neconformități."
        )

    # ── Recomandări bazate pe câmpuri lipsă ───────────────────────────────
    critical_missing = [
        f for f in result["missing_fields"]
        if f in ("disciplines", "bim_objectives", "lod_specification", "cde_platform", "team_roles")
    ]
    if critical_missing:
        result["recommendations"].append(
            f"Completează câmpurile critice lipsă: {', '.join(critical_missing)}"
        )

    return result
