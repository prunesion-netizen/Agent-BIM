"""Adaugă tabelele ISO 19650: CDE states, approvals, EIR, deliverables,
RACI, LOIN, handover, security, clash, KPI + coloane cde_state/approval_status
pe generated_documents.

Revision ID: 007_iso19650_full
Revises: 006_add_users
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007_iso19650_full"
down_revision: Union[str, None] = "006_add_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Coloane noi pe generated_documents ────────────────────────────────
    op.add_column(
        "generated_documents",
        sa.Column("cde_state", sa.String(20), nullable=True, server_default="wip"),
    )
    op.add_column(
        "generated_documents",
        sa.Column("approval_status", sa.String(20), nullable=True, server_default="draft"),
    )

    # ── FAZA 1: CDE States + Approvals ───────────────────────────────────
    op.create_table(
        "document_states",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("generated_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("previous_state", sa.String(20), nullable=True),
        sa.Column("changed_by", sa.String(100), nullable=False, server_default="system"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_document_states_document_id", "document_states", ["document_id"])

    op.create_table(
        "document_approvals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("generated_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_document_approvals_document_id", "document_approvals", ["document_id"])
    op.create_index("ix_document_approvals_doc_role", "document_approvals", ["document_id", "role"])

    # ── FAZA 2: EIR + Deliverables ───────────────────────────────────────
    op.create_table(
        "eir_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("eir_type", sa.String(10), nullable=False, server_default="eir"),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("version", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_eir_documents_project_id", "eir_documents", ["project_id"])

    op.create_table(
        "deliverables",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("discipline", sa.String(50), nullable=False),
        sa.Column("format", sa.String(50), nullable=False, server_default="ifc4"),
        sa.Column("lod", sa.String(10), nullable=True),
        sa.Column("responsible_role", sa.String(50), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("phase", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_deliverables_project_id", "deliverables", ["project_id"])
    op.create_index("ix_deliverables_project_discipline", "deliverables", ["project_id", "discipline"])

    # ── FAZA 3: RACI + LOIN ──────────────────────────────────────────────
    op.create_table(
        "raci_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("role_code", sa.String(50), nullable=False),
        sa.Column("assignment", sa.String(1), nullable=False),
        sa.Column("discipline", sa.String(50), nullable=True),
        sa.Column("phase", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_raci_entries_project_id", "raci_entries", ["project_id"])
    op.create_index("ix_raci_project_task", "raci_entries", ["project_id", "task_name"])

    op.create_table(
        "loin_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("element_type", sa.String(100), nullable=False),
        sa.Column("discipline", sa.String(50), nullable=False),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("detail_level", sa.String(20), nullable=True),
        sa.Column("dimensionality", sa.String(20), nullable=True),
        sa.Column("information_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_loin_entries_project_id", "loin_entries", ["project_id"])
    op.create_index("ix_loin_project_element", "loin_entries", ["project_id", "element_type"])

    # ── FAZA 4: Handover, Security, Clash, KPI ───────────────────────────
    op.create_table(
        "handover_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("completed_by", sa.String(100), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_handover_items_project_id", "handover_items", ["project_id"])

    op.create_table(
        "security_classifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("classification_level", sa.String(20), nullable=False, server_default="standard"),
        sa.Column("security_plan_json", sa.JSON(), nullable=True),
        sa.Column("sensitive_areas", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_security_classifications_project_id", "security_classifications", ["project_id"])

    op.create_table(
        "clash_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("discipline_a", sa.String(50), nullable=False),
        sa.Column("discipline_b", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("assigned_to_role", sa.String(50), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_clash_records_project_id", "clash_records", ["project_id"])
    op.create_index("ix_clash_records_project_status", "clash_records", ["project_id", "status"])

    op.create_table(
        "kpi_measurements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kpi_name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=True),
        sa.Column("measurement_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_kpi_measurements_project_id", "kpi_measurements", ["project_id"])
    op.create_index("ix_kpi_project_name", "kpi_measurements", ["project_id", "kpi_name"])


def downgrade() -> None:
    op.drop_table("kpi_measurements")
    op.drop_table("clash_records")
    op.drop_table("security_classifications")
    op.drop_table("handover_items")
    op.drop_table("loin_entries")
    op.drop_table("raci_entries")
    op.drop_table("deliverables")
    op.drop_table("eir_documents")
    op.drop_table("document_approvals")
    op.drop_table("document_states")
    op.drop_column("generated_documents", "approval_status")
    op.drop_column("generated_documents", "cde_state")
