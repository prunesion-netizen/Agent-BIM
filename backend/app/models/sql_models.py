"""
sql_models.py — Modele SQLAlchemy 2.0 pentru Agent BIM.

Tabele: projects, project_contexts, generated_documents,
        agent_conversations, agent_messages, document_states,
        document_approvals, eir_documents, deliverables,
        raci_entries, loin_entries, handover_items,
        security_classifications, clash_records, kpi_measurements.
"""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, _is_sqlite

# JSONB pe PostgreSQL, JSON pe SQLite
if not _is_sqlite:
    from sqlalchemy.dialects.postgresql import JSONB as _JsonType
else:
    _JsonType = JSON


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    project_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project_contexts: Mapped[list[ProjectContextModel]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    generated_documents: Mapped[list[GeneratedDocumentModel]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectContextModel(Base):
    __tablename__ = "project_contexts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    context_json: Mapped[dict] = mapped_column(_JsonType, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship(back_populates="project_contexts")


class GeneratedDocumentModel(Base):
    __tablename__ = "generated_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    summary_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fail_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    warning_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    cde_state: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="wip"
    )
    approval_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="draft"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship(back_populates="generated_documents")

    __table_args__ = (
        Index("ix_generated_documents_project_doc_type", "project_id", "doc_type"),
    )


class UploadedFileModel(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False, default="ifc")
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parsed_summary_json: Mapped[Optional[dict]] = mapped_column(_JsonType, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship()

    __table_args__ = (
        Index("ix_uploaded_files_project_type", "project_id", "file_type"),
    )


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="agent")
    details_json: Mapped[Optional[dict]] = mapped_column(_JsonType, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship()


class AgentConversationModel(Base):
    __tablename__ = "agent_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Conversație nouă")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[ProjectModel] = relationship()
    messages: Mapped[list[AgentMessageModel]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan",
        order_by="AgentMessageModel.sequence_num",
    )


class AgentMessageModel(Base):
    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("agent_conversations.id", ondelete="CASCADE"), index=True
    )
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool_steps_json: Mapped[Optional[dict]] = mapped_column(_JsonType, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped[AgentConversationModel] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_agent_messages_conv_seq", "conversation_id", "sequence_num"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# FAZA 1: CDE Workflow + Aprobare Documente
# ══════════════════════════════════════════════════════════════════════════════


class DocumentStateModel(Base):
    """Istoric tranziții CDE: WIP → Shared → Published → Archived."""
    __tablename__ = "document_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("generated_documents.id", ondelete="CASCADE"), index=True
    )
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    changed_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped[GeneratedDocumentModel] = relationship()


class DocumentApprovalModel(Base):
    """Lanț aprobare: author → checker → approver."""
    __tablename__ = "document_approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("generated_documents.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # checker / approver
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped[GeneratedDocumentModel] = relationship()

    __table_args__ = (
        Index("ix_document_approvals_doc_role", "document_id", "role"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# FAZA 2: EIR/AIR + TIDP/MIDP
# ══════════════════════════════════════════════════════════════════════════════


class EirModel(Base):
    """Cerințe informare structurate (EIR / AIR)."""
    __tablename__ = "eir_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    eir_type: Mapped[str] = mapped_column(String(10), nullable=False, default="eir")  # eir / air
    content_json: Mapped[dict] = mapped_column(_JsonType, nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship()


class DeliverableModel(Base):
    """Livrabil individual din TIDP/MIDP."""
    __tablename__ = "deliverables"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    discipline: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False, default="ifc4")
    lod: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    responsible_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    due_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[ProjectModel] = relationship()

    __table_args__ = (
        Index("ix_deliverables_project_discipline", "project_id", "discipline"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# FAZA 3: RACI Matrix + LOIN Structure
# ══════════════════════════════════════════════════════════════════════════════


class RaciEntryModel(Base):
    """Intrare RACI: task × role × assignment."""
    __tablename__ = "raci_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_code: Mapped[str] = mapped_column(String(50), nullable=False)
    assignment: Mapped[str] = mapped_column(String(1), nullable=False)  # R/A/C/I
    discipline: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship()

    __table_args__ = (
        Index("ix_raci_project_task", "project_id", "task_name"),
    )


class LoinEntryModel(Base):
    """Level of Information Need per element × discipline × phase."""
    __tablename__ = "loin_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    element_type: Mapped[str] = mapped_column(String(100), nullable=False)
    discipline: Mapped[str] = mapped_column(String(50), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    detail_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    dimensionality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    information_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship()

    __table_args__ = (
        Index("ix_loin_project_element", "project_id", "element_type"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# FAZA 4: Operațional + Securitate + Clash + KPI
# ══════════════════════════════════════════════════════════════════════════════


class HandoverChecklistModel(Base):
    """Element din checklist-ul de predare/handover."""
    __tablename__ = "handover_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship()


class SecurityClassificationModel(Base):
    """Clasificare securitate informații (ISO 19650-5)."""
    __tablename__ = "security_classifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, unique=True
    )
    classification_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="standard"
    )
    security_plan_json: Mapped[Optional[dict]] = mapped_column(_JsonType, nullable=True)
    sensitive_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[ProjectModel] = relationship()


class ClashRecordModel(Base):
    """Înregistrare clash detectat între discipline."""
    __tablename__ = "clash_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    discipline_a: Mapped[str] = mapped_column(String(50), nullable=False)
    discipline_b: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    assigned_to_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    project: Mapped[ProjectModel] = relationship()

    __table_args__ = (
        Index("ix_clash_records_project_status", "project_id", "status"),
    )


class KpiMeasurementModel(Base):
    """Măsurare KPI proiect BIM."""
    __tablename__ = "kpi_measurements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kpi_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    measurement_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship()

    __table_args__ = (
        Index("ix_kpi_project_name", "project_id", "kpi_name"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# FAZA 5: COBie Validator
# ══════════════════════════════════════════════════════════════════════════════


class CobieValidationModel(Base):
    """Rezultat validare COBie XLSX."""
    __tablename__ = "cobie_validations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    validation_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="full"
    )  # "structure" | "full"
    overall_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="fail"
    )  # "pass" | "warning" | "fail"
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_checks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    results_json: Mapped[Optional[dict]] = mapped_column(_JsonType, nullable=True)
    sheet_stats_json: Mapped[Optional[dict]] = mapped_column(_JsonType, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship()

    __table_args__ = (
        Index("ix_cobie_validations_project", "project_id"),
    )


class NotificationModel(Base):
    """Notificari in-app pentru utilizatori."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="info"
    )  # "cde_change" | "deadline" | "clash" | "verification" | "bep" | "info"
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[UserModel] = relationship()
    project: Mapped[Optional[ProjectModel]] = relationship()
