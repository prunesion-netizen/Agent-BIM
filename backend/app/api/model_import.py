"""
model_import.py — Endpoint pentru importul fișierelor IFC.

Primește un fișier IFC, îl parsează cu ifcopenshell și returnează
un ModelSummary pre-populat pe care UI-ul îl poate afișa/edita.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.projects_repository import get_project
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
) -> ModelSummary:
    """Primește un fișier .ifc, parsează conținutul și returnează un ModelSummary."""

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

    # 3. Salvează temporar
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time() * 1000)
    tmp_path = UPLOAD_DIR / f"{project_id}_{timestamp}.ifc"

    try:
        content = await file.read()
        tmp_path.write_bytes(content)

        # 4. Parsează
        summary = generate_model_summary_from_ifc(str(tmp_path))
        return summary

    finally:
        # 5. Cleanup
        if tmp_path.exists():
            os.remove(tmp_path)
