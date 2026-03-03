"""
audit.py — Serviciu de audit trail pentru conformitate ISO 19650.

Înregistrează acțiunile efectuate asupra proiectelor: generare BEP,
verificare, export, actualizare context, analiză IFC, etc.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.repositories.projects_repository import save_audit_log

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    project_id: int,
    action: str,
    details: dict | None = None,
    actor: str = "agent",
) -> None:
    """
    Înregistrează o acțiune în jurnalul de audit.

    Args:
        db: Sesiune SQLAlchemy
        project_id: ID-ul proiectului
        action: Numele acțiunii (ex: "generate_bep", "verify_bep")
        details: Dict opțional cu detalii suplimentare
        actor: Cine a efectuat acțiunea (default: "agent")
    """
    try:
        save_audit_log(
            db,
            project_id=project_id,
            action=action,
            actor=actor,
            details_json=details,
        )
    except Exception as e:
        logger.warning(f"Nu s-a putut salva audit log: {e}")
