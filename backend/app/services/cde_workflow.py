"""
cde_workflow.py — Serviciu CDE Workflow (ISO 19650).

Gestionează tranzițiile de stare ale documentelor:
WIP → Shared → Published → Archived

și lanțul de aprobare: author → checker → approver.
"""

from __future__ import annotations

import datetime
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.sql_models import (
    DocumentApprovalModel,
    DocumentStateModel,
    GeneratedDocumentModel,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)

# Tranziții valide CDE
VALID_TRANSITIONS: dict[str, list[str]] = {
    "wip": ["shared"],
    "shared": ["published", "wip"],  # respingere → înapoi la WIP
    "published": ["archived"],
    "archived": [],
}


def transition_document_state(
    db: Session,
    document_id: int,
    target_state: str,
    changed_by: str = "system",
    reason: str | None = None,
) -> DocumentStateModel:
    """Tranziție stare CDE cu validare."""
    doc = db.get(GeneratedDocumentModel, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document negăsit.")

    current_state = doc.cde_state or "wip"

    if target_state not in VALID_TRANSITIONS.get(current_state, []):
        raise HTTPException(
            status_code=400,
            detail=f"Tranziție invalidă: {current_state} → {target_state}. "
                   f"Tranziții valide: {VALID_TRANSITIONS.get(current_state, [])}",
        )

    # Shared necesită submit for approval mai întâi
    if target_state == "published":
        approvals = (
            db.query(DocumentApprovalModel)
            .filter(DocumentApprovalModel.document_id == document_id)
            .all()
        )
        if not approvals:
            raise HTTPException(
                status_code=400,
                detail="Documentul trebuie trimis spre aprobare înainte de publicare.",
            )
        pending = [a for a in approvals if a.status == "pending"]
        rejected = [a for a in approvals if a.status == "rejected"]
        if pending:
            raise HTTPException(
                status_code=400,
                detail=f"Mai sunt {len(pending)} aprobări în așteptare.",
            )
        if rejected:
            raise HTTPException(
                status_code=400,
                detail="Documentul are aprobări respinse. Retrimite spre aprobare.",
            )

    # Salvează tranziția
    state_entry = DocumentStateModel(
        document_id=document_id,
        state=target_state,
        previous_state=current_state,
        changed_by=changed_by,
        reason=reason,
    )
    db.add(state_entry)

    doc.cde_state = target_state
    if target_state == "shared":
        doc.approval_status = "in_review"
    elif target_state == "published":
        doc.approval_status = "approved"
    elif target_state == "wip":
        doc.approval_status = "draft"

    db.flush()

    log_action(db, doc.project_id, "cde_transition", {
        "document_id": document_id,
        "from": current_state,
        "to": target_state,
        "changed_by": changed_by,
    })

    return state_entry


def submit_for_approval(
    db: Session,
    document_id: int,
    checker_username: str | None = None,
    approver_username: str | None = None,
) -> list[DocumentApprovalModel]:
    """Creează lanțul de aprobare checker + approver."""
    doc = db.get(GeneratedDocumentModel, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document negăsit.")

    if (doc.cde_state or "wip") != "wip":
        raise HTTPException(
            status_code=400,
            detail="Documentul trebuie să fie în starea WIP pentru a fi trimis spre aprobare.",
        )

    # Șterge aprobări anterioare dacă există
    db.query(DocumentApprovalModel).filter(
        DocumentApprovalModel.document_id == document_id
    ).delete()

    approvals = []

    checker = DocumentApprovalModel(
        document_id=document_id,
        role="checker",
        assigned_to=checker_username,
        status="pending",
    )
    db.add(checker)
    approvals.append(checker)

    approver = DocumentApprovalModel(
        document_id=document_id,
        role="approver",
        assigned_to=approver_username,
        status="pending",
    )
    db.add(approver)
    approvals.append(approver)

    # Tranziție automată la Shared
    transition_document_state(db, document_id, "shared", changed_by="system", reason="Trimis spre aprobare")

    db.flush()

    log_action(db, doc.project_id, "submit_for_approval", {
        "document_id": document_id,
        "checker": checker_username,
        "approver": approver_username,
    })

    return approvals


def process_approval(
    db: Session,
    approval_id: int,
    status: str,
    comment: str | None = None,
) -> DocumentApprovalModel:
    """Procesează o decizie de aprobare."""
    approval = db.get(DocumentApprovalModel, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Aprobare negăsită.")

    if approval.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Aprobarea a fost deja procesată: {approval.status}",
        )

    # Checker trebuie aprobat înainte de approver
    if approval.role == "approver":
        checker = (
            db.query(DocumentApprovalModel)
            .filter(
                DocumentApprovalModel.document_id == approval.document_id,
                DocumentApprovalModel.role == "checker",
            )
            .first()
        )
        if checker and checker.status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Checker-ul trebuie să aprobe mai întâi.",
            )

    approval.status = status
    approval.comment = comment
    approval.decided_at = datetime.datetime.now(datetime.timezone.utc)
    db.flush()

    doc = db.get(GeneratedDocumentModel, approval.document_id)

    # Dacă respins, doc se întoarce la WIP
    if status == "rejected":
        transition_document_state(
            db, approval.document_id, "wip",
            changed_by="approval_system",
            reason=f"Respins de {approval.role}: {comment or 'fără motiv'}",
        )

    # Dacă toate aprobate, auto-tranziție la Published
    if status == "approved":
        all_approvals = (
            db.query(DocumentApprovalModel)
            .filter(DocumentApprovalModel.document_id == approval.document_id)
            .all()
        )
        all_approved = all(a.status == "approved" for a in all_approvals)
        if all_approved:
            transition_document_state(
                db, approval.document_id, "published",
                changed_by="approval_system",
                reason="Toate aprobările completate cu succes",
            )

    log_action(db, doc.project_id if doc else 0, "process_approval", {
        "approval_id": approval_id,
        "role": approval.role,
        "status": status,
        "comment": comment,
    })

    return approval


def get_document_cde_status(db: Session, document_id: int) -> dict:
    """Returnează status CDE complet pentru un document."""
    doc = db.get(GeneratedDocumentModel, document_id)
    if not doc:
        return {"error": "Document negăsit."}

    states = (
        db.query(DocumentStateModel)
        .filter(DocumentStateModel.document_id == document_id)
        .order_by(DocumentStateModel.created_at.desc())
        .all()
    )

    approvals = (
        db.query(DocumentApprovalModel)
        .filter(DocumentApprovalModel.document_id == document_id)
        .all()
    )

    return {
        "document_id": doc.id,
        "document_title": doc.title,
        "cde_state": doc.cde_state or "wip",
        "approval_status": doc.approval_status or "draft",
        "state_history": [
            {
                "id": s.id,
                "state": s.state,
                "previous_state": s.previous_state,
                "changed_by": s.changed_by,
                "reason": s.reason,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            }
            for s in states
        ],
        "approvals": [
            {
                "id": a.id,
                "role": a.role,
                "assigned_to": a.assigned_to,
                "status": a.status,
                "comment": a.comment,
                "decided_at": a.decided_at.isoformat() if a.decided_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else "",
            }
            for a in approvals
        ],
    }
