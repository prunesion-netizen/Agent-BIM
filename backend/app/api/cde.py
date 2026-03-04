"""
cde.py — Router CDE Workflow (ISO 19650).

Endpoints pentru tranziții de stare și aprobare documente.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.schemas.cde import ApprovalDecision, ApprovalRequest, StateTransitionRequest
from app.services.auth import get_current_user
from app.services.cde_workflow import (
    get_document_cde_status,
    process_approval,
    submit_for_approval,
    transition_document_state,
)
from app.models.sql_models import DocumentApprovalModel, GeneratedDocumentModel

router = APIRouter()


@router.post("/documents/{document_id}/transition")
def transition_state(
    document_id: int,
    body: StateTransitionRequest,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tranziție stare CDE a unui document."""
    entry = transition_document_state(
        db, document_id, body.target_state,
        changed_by=user.username,
        reason=body.reason,
    )
    db.commit()
    return {
        "success": True,
        "new_state": entry.state,
        "previous_state": entry.previous_state,
    }


@router.post("/documents/{document_id}/submit-for-approval")
def submit_approval(
    document_id: int,
    body: ApprovalRequest,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trimite document spre aprobare (checker + approver)."""
    approvals = submit_for_approval(
        db, document_id,
        checker_username=body.checker_username,
        approver_username=body.approver_username,
    )
    db.commit()
    return {
        "success": True,
        "approvals_created": len(approvals),
    }


@router.post("/approvals/{approval_id}/decide")
def decide_approval(
    approval_id: int,
    body: ApprovalDecision,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Procesează decizie aprobare/respingere."""
    approval = process_approval(
        db, approval_id, body.status, body.comment,
    )
    db.commit()
    return {
        "success": True,
        "role": approval.role,
        "status": approval.status,
    }


@router.get("/documents/{document_id}/cde-status")
def get_cde_status(
    document_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează status CDE complet pentru un document."""
    return get_document_cde_status(db, document_id)


@router.get("/projects/{project_id}/pending-approvals")
def get_pending_approvals(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează aprobările în așteptare pentru un proiect."""
    approvals = (
        db.query(DocumentApprovalModel)
        .join(GeneratedDocumentModel)
        .filter(
            GeneratedDocumentModel.project_id == project_id,
            DocumentApprovalModel.status == "pending",
        )
        .all()
    )
    return [
        {
            "id": a.id,
            "document_id": a.document_id,
            "role": a.role,
            "assigned_to": a.assigned_to,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        }
        for a in approvals
    ]


@router.get("/my-approvals")
def get_my_approvals(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează aprobările asignate utilizatorului curent."""
    approvals = (
        db.query(DocumentApprovalModel)
        .filter(
            DocumentApprovalModel.assigned_to == user.username,
            DocumentApprovalModel.status == "pending",
        )
        .all()
    )
    return [
        {
            "id": a.id,
            "document_id": a.document_id,
            "role": a.role,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        }
        for a in approvals
    ]
