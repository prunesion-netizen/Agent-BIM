"""
model_import.py — Endpoint pentru importul fișierelor IFC.

Primește un fișier IFC, îl parsează cu ifcopenshell, persistă fișierul
pe disc și salvează metadata + summary parsat în DB.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.services.auth import get_current_user
from app.repositories.projects_repository import (
    get_latest_uploaded_file,
    get_project,
    save_uploaded_file,
)
from app.schemas.model_summary import ModelSummary
from app.services.ifc_parser import generate_model_summary_from_ifc

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"


@router.post(
    "/projects/{project_id}/import-ifc",
    response_model=ModelSummary,
    summary="Import IFC → ModelSummary automat",
)
async def api_import_ifc(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
) -> ModelSummary:
    """Primește un fișier .ifc, parsează conținutul, persistă și returnează ModelSummary."""

    # 1. Verifică proiectul
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proiectul nu a fost găsit.")

    # 2. Verifică extensia
    filename = file.filename or ""
    if not filename.lower().endswith(".ifc"):
        raise HTTPException(
            status_code=400,
            detail="Fișierul trebuie să aibă extensia .ifc",
        )

    # 3. Salvează persistent
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time() * 1000)
    saved_path = UPLOAD_DIR / f"{project_id}_{timestamp}_{filename}"

    content = await file.read()
    saved_path.write_bytes(content)
    file_size = len(content)

    # 4. Parsează
    summary = generate_model_summary_from_ifc(str(saved_path))

    # 5. Persistă metadata + summary în DB
    save_uploaded_file(
        db,
        project_id=project_id,
        filename=filename,
        file_path=str(saved_path),
        file_type="ifc",
        file_size_bytes=file_size,
        parsed_summary_json=summary.model_dump(mode="json"),
    )
    db.commit()

    return summary


@router.get(
    "/projects/{project_id}/ifc-file",
    summary="Descarcă fișierul IFC binar",
)
def api_get_ifc_file(
    project_id: int,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Returnează fișierul IFC binar al proiectului (cel mai recent upload)."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proiectul nu a fost găsit.")

    uploaded = get_latest_uploaded_file(db, project_id, "ifc")
    if not uploaded:
        raise HTTPException(status_code=404, detail="Nu există fișier IFC pentru acest proiect.")

    file_path = Path(uploaded.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fișierul IFC nu a fost găsit pe disc.")

    return FileResponse(
        path=str(file_path),
        filename=uploaded.filename,
        media_type="application/octet-stream",
    )


@router.get(
    "/projects/{project_id}/ifc-info",
    summary="Metadata fișier IFC (fără descărcare)",
)
def api_get_ifc_info(
    project_id: int,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Returnează metadata JSON despre cel mai recent fișier IFC uploadat."""
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proiectul nu a fost găsit.")

    uploaded = get_latest_uploaded_file(db, project_id, "ifc")
    if not uploaded:
        raise HTTPException(status_code=404, detail="Nu există fișier IFC pentru acest proiect.")

    return {
        "filename": uploaded.filename,
        "file_size_bytes": uploaded.file_size_bytes,
        "file_size_mb": round((uploaded.file_size_bytes or 0) / (1024 * 1024), 2),
        "uploaded_at": uploaded.created_at.isoformat() if uploaded.created_at else None,
        "summary": uploaded.parsed_summary_json,
    }
