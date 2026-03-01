"""Adaugă coloane summary_status, fail_count, warning_count pe generated_documents.

Revision ID: 003_add_verification_summary
Revises: 002_add_description
Create Date: 2026-03-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_add_verification_summary"
down_revision: Union[str, None] = "002_add_description"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("generated_documents") as batch_op:
        batch_op.add_column(
            sa.Column("summary_status", sa.String(20), nullable=True)
        )
        batch_op.add_column(
            sa.Column("fail_count", sa.Integer(), nullable=True, server_default="0")
        )
        batch_op.add_column(
            sa.Column("warning_count", sa.Integer(), nullable=True, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("generated_documents") as batch_op:
        batch_op.drop_column("warning_count")
        batch_op.drop_column("fail_count")
        batch_op.drop_column("summary_status")
