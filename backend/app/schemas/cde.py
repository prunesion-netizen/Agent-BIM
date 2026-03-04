"""
cde.py — Scheme Pydantic pentru CDE workflow (ISO 19650 Common Data Environment).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


CdeState = Literal["wip", "shared", "published", "archived"]
ApprovalRole = Literal["checker", "approver"]
ApprovalStatus = Literal["pending", "approved", "rejected"]


class StateTransitionRequest(BaseModel):
    """Cerere de tranziție stare CDE."""
    target_state: CdeState
    reason: str | None = None
    changed_by: str = "system"


class StateTransitionRead(BaseModel):
    """Tranziție CDE returnată de API."""
    id: int
    document_id: int
    state: str
    previous_state: str | None = None
    changed_by: str
    reason: str | None = None
    created_at: str


class ApprovalRequest(BaseModel):
    """Cerere de creare lanț aprobare."""
    checker_username: str | None = None
    approver_username: str | None = None


class ApprovalDecision(BaseModel):
    """Decizie aprobare/respingere."""
    status: Literal["approved", "rejected"]
    comment: str | None = None


class ApprovalRead(BaseModel):
    """Aprobare returnată de API."""
    id: int
    document_id: int
    role: str
    assigned_to: str | None = None
    status: str
    comment: str | None = None
    decided_at: str | None = None
    created_at: str


class DocumentCdeStatus(BaseModel):
    """Status CDE complet pentru un document."""
    document_id: int
    document_title: str
    cde_state: str
    approval_status: str
    state_history: list[StateTransitionRead] = []
    approvals: list[ApprovalRead] = []
