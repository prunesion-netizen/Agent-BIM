"""Adaugă tabele uploaded_files și audit_logs.

Revision ID: 005_uploads_and_audit
Revises: 004_add_conversations
Create Date: 2026-03-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_uploads_and_audit"
down_revision: Union[str, None] = "004_add_conversations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    json_type = sa.JSON() if is_sqlite else postgresql.JSONB()

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False, server_default="ifc"),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("parsed_summary_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_uploaded_files_project_id", "uploaded_files", ["project_id"])
    op.create_index(
        "ix_uploaded_files_project_type", "uploaded_files", ["project_id", "file_type"]
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False, server_default="agent"),
        sa.Column("details_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_project_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_uploaded_files_project_type", table_name="uploaded_files")
    op.drop_index("ix_uploaded_files_project_id", table_name="uploaded_files")
    op.drop_table("uploaded_files")
