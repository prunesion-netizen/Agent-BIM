"""
iso_compliance_checker.py — Verificare conformitate ISO 19650 completă (Faza 5).

Verifică toate părțile ISO 19650 și returnează scor per parte + overall.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.sql_models import (
    ClashRecordModel,
    CobieValidationModel,
    DeliverableModel,
    EirModel,
    HandoverChecklistModel,
    LoinEntryModel,
    RaciEntryModel,
    SecurityClassificationModel,
)
from app.repositories.projects_repository import (
    get_latest_generated_document,
    get_latest_project_context,
    get_latest_uploaded_file,
    get_project,
    list_verification_reports,
)
from app.services.project_health import compute_project_health

logger = logging.getLogger(__name__)


def check_full_compliance(db: Session, project_id: int) -> dict:
    """
    Verifică conformitatea completă ISO 19650 parts 1-5.

    Returns:
        Dict cu scor per parte + overall + recomandări.
    """
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    parts: dict[str, dict] = {}

    # ── ISO 19650-1: Concepte și principii ────────────────────────────────
    health = compute_project_health(db, project_id)
    ctx_entry = get_latest_project_context(db, project_id)
    has_context = ctx_entry is not None
    bep_doc = get_latest_generated_document(db, project_id, "bep")
    has_bep = bep_doc is not None

    part1_checks = []
    part1_score = 0

    if has_context:
        part1_checks.append({"check": "ProjectContext definit", "status": "pass"})
        part1_score += 25
    else:
        part1_checks.append({"check": "ProjectContext definit", "status": "fail"})

    if has_bep:
        part1_checks.append({"check": "BEP generat", "status": "pass"})
        part1_score += 25
    else:
        part1_checks.append({"check": "BEP generat", "status": "fail"})

    cde_state = bep_doc.cde_state if bep_doc else None
    if cde_state and cde_state != "wip":
        part1_checks.append({"check": "CDE workflow activ", "status": "pass"})
        part1_score += 25
    else:
        part1_checks.append({"check": "CDE workflow activ", "status": "warning"})
        part1_score += 10

    ifc_file = get_latest_uploaded_file(db, project_id, "ifc")
    if ifc_file:
        part1_checks.append({"check": "Model IFC importat", "status": "pass"})
        part1_score += 25
    else:
        part1_checks.append({"check": "Model IFC importat", "status": "warning"})
        part1_score += 5

    parts["iso_19650_1"] = {
        "title": "ISO 19650-1 — Concepte și principii",
        "score": part1_score,
        "checks": part1_checks,
    }

    # ── ISO 19650-2: Faza de livrare ─────────────────────────────────────
    part2_checks = []
    part2_score = 0

    # EIR definit?
    eir = db.query(EirModel).filter(EirModel.project_id == project_id).first()
    if eir:
        part2_checks.append({"check": "EIR definit", "status": "pass"})
        part2_score += 20
    else:
        part2_checks.append({"check": "EIR definit", "status": "fail"})

    # TIDP populat?
    deliverables = (
        db.query(DeliverableModel)
        .filter(DeliverableModel.project_id == project_id)
        .all()
    )
    if deliverables:
        part2_checks.append({"check": f"TIDP populat ({len(deliverables)} livrabile)", "status": "pass"})
        part2_score += 20
    else:
        part2_checks.append({"check": "TIDP populat", "status": "fail"})

    # RACI complet?
    raci_entries = (
        db.query(RaciEntryModel)
        .filter(RaciEntryModel.project_id == project_id)
        .all()
    )
    if raci_entries:
        tasks = set(e.task_name for e in raci_entries)
        has_r = any(e.assignment == "R" for e in raci_entries)
        has_a = any(e.assignment == "A" for e in raci_entries)
        if has_r and has_a:
            part2_checks.append({"check": f"RACI complet ({len(tasks)} tasks)", "status": "pass"})
            part2_score += 20
        else:
            part2_checks.append({"check": "RACI incomplet (lipsesc R/A)", "status": "warning"})
            part2_score += 10
    else:
        part2_checks.append({"check": "RACI definit", "status": "fail"})

    # LOIN definit?
    loin_entries = (
        db.query(LoinEntryModel)
        .filter(LoinEntryModel.project_id == project_id)
        .all()
    )
    if loin_entries:
        part2_checks.append({"check": f"LOIN definit ({len(loin_entries)} intrări)", "status": "pass"})
        part2_score += 20
    else:
        part2_checks.append({"check": "LOIN definit", "status": "fail"})

    # Verificare BEP efectuată?
    reports = list_verification_reports(db, project_id)
    if reports:
        latest = reports[0]
        status_str = latest.summary_status or "unknown"
        part2_checks.append({"check": f"Verificare BEP efectuată (status: {status_str})", "status": "pass"})
        part2_score += 20
    else:
        part2_checks.append({"check": "Verificare BEP efectuată", "status": "fail"})

    parts["iso_19650_2"] = {
        "title": "ISO 19650-2 — Faza de livrare",
        "score": part2_score,
        "checks": part2_checks,
    }

    # ── ISO 19650-3: Faza operațională ───────────────────────────────────
    part3_checks = []
    part3_score = 0

    handover_items = (
        db.query(HandoverChecklistModel)
        .filter(HandoverChecklistModel.project_id == project_id)
        .all()
    )
    if handover_items:
        completed = sum(1 for h in handover_items if h.is_completed)
        total = len(handover_items)
        pct = round((completed / total) * 100) if total else 0
        if pct >= 80:
            part3_checks.append({"check": f"Handover checklist ({pct}% complet)", "status": "pass"})
            part3_score += 50
        elif pct >= 50:
            part3_checks.append({"check": f"Handover checklist ({pct}% complet)", "status": "warning"})
            part3_score += 30
        else:
            part3_checks.append({"check": f"Handover checklist ({pct}% complet)", "status": "warning"})
            part3_score += 15
    else:
        part3_checks.append({"check": "Handover checklist definit", "status": "fail"})

    # Clash management
    clashes = (
        db.query(ClashRecordModel)
        .filter(ClashRecordModel.project_id == project_id)
        .all()
    )
    if clashes:
        open_clashes = sum(1 for c in clashes if c.status == "open")
        if open_clashes == 0:
            part3_checks.append({"check": "Toate clash-urile rezolvate", "status": "pass"})
            part3_score += 40
        else:
            part3_checks.append({"check": f"{open_clashes} clash-uri deschise", "status": "warning"})
            part3_score += 20
    else:
        part3_checks.append({"check": "Clash management (fără clash-uri)", "status": "pass"})
        part3_score += 30

    # COBie validation
    cobie = (
        db.query(CobieValidationModel)
        .filter(CobieValidationModel.project_id == project_id)
        .order_by(CobieValidationModel.created_at.desc())
        .first()
    )
    if cobie:
        if cobie.overall_status == "pass":
            part3_checks.append({"check": f"COBie validat (scor {cobie.score}%)", "status": "pass"})
            part3_score += 10
        elif cobie.overall_status == "warning":
            part3_checks.append({"check": f"COBie cu avertismente (scor {cobie.score}%)", "status": "warning"})
            part3_score += 5
        else:
            part3_checks.append({"check": f"COBie invalid (scor {cobie.score}%)", "status": "fail"})
    else:
        part3_checks.append({"check": "COBie validat", "status": "warning"})

    parts["iso_19650_3"] = {
        "title": "ISO 19650-3 — Faza operațională",
        "score": part3_score,
        "checks": part3_checks,
    }

    # ── ISO 19650-5: Securitate informații ────────────────────────────────
    part5_checks = []
    part5_score = 0

    security = (
        db.query(SecurityClassificationModel)
        .filter(SecurityClassificationModel.project_id == project_id)
        .first()
    )
    if security:
        part5_checks.append({"check": f"Clasificare securitate: {security.classification_level}", "status": "pass"})
        part5_score += 50
        if security.security_plan_json:
            part5_checks.append({"check": "Plan securitate generat", "status": "pass"})
            part5_score += 50
        else:
            part5_checks.append({"check": "Plan securitate generat", "status": "fail"})
    else:
        part5_checks.append({"check": "Clasificare securitate definită", "status": "fail"})
        part5_checks.append({"check": "Plan securitate generat", "status": "fail"})

    parts["iso_19650_5"] = {
        "title": "ISO 19650-5 — Securitate informații",
        "score": part5_score,
        "checks": part5_checks,
    }

    # ── Scor overall ─────────────────────────────────────────────────────
    scores = [p["score"] for p in parts.values()]
    overall = round(sum(scores) / len(scores)) if scores else 0

    # Recomandări
    recommendations = []
    if not has_context:
        recommendations.append("Completează fișa proiectului (ProjectContext) — fundament ISO 19650.")
    if not has_bep:
        recommendations.append("Generează BEP-ul proiectului.")
    if not eir:
        recommendations.append("Generează EIR (Exchange Information Requirements) — ISO 19650-2.")
    if not deliverables:
        recommendations.append("Generează TIDP (Task Information Delivery Plan).")
    if not raci_entries:
        recommendations.append("Generează matricea RACI pentru roluri și responsabilități.")
    if not loin_entries:
        recommendations.append("Generează LOIN (Level of Information Need) — BS EN 17412-1.")
    if not handover_items:
        recommendations.append("Creează checklist-ul de handover — ISO 19650-3.")
    if not security:
        recommendations.append("Definește clasificarea de securitate — ISO 19650-5.")
    if not reports:
        recommendations.append("Rulează verificarea BEP vs model.")
    if not cobie:
        recommendations.append("Uploadează și validează un fișier COBie XLSX — necesar pentru predarea informațiilor FM.")

    return {
        "project_id": project_id,
        "project_name": project.name,
        "overall_score": overall,
        "parts": parts,
        "recommendations": recommendations,
        "total_checks": sum(len(p["checks"]) for p in parts.values()),
        "pass_count": sum(
            1 for p in parts.values()
            for c in p["checks"] if c["status"] == "pass"
        ),
        "warning_count": sum(
            1 for p in parts.values()
            for c in p["checks"] if c["status"] == "warning"
        ),
        "fail_count": sum(
            1 for p in parts.values()
            for c in p["checks"] if c["status"] == "fail"
        ),
    }
