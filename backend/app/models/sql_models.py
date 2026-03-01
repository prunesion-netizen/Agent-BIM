"""
sql_models.py — Modele SQLAlchemy 2.0 pentru Agent BIM.

Tabele: projects, project_contexts, generated_documents.
"""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
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
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[ProjectModel] = relationship(back_populates="generated_documents")

    __table_args__ = (
        Index("ix_generated_documents_project_doc_type", "project_id", "doc_type"),
    )
