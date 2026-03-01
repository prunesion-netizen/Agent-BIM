"""Adaugă câmpul description pe tabelul projects.

Revision ID: 002_add_description
Revises: 001_initial
Create Date: 2026-03-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_add_description"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(
            sa.Column("description", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("description")
