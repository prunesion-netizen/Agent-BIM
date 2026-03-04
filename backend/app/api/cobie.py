"""
cobie.py — Router COBie Validator: upload+validare, istoric, template download.
"""

import os
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.schemas.cobie import CobieTemplateRequest
from app.services.auth import get_current_user
from app.services.cobie_validator import (
    generate_cobie_template,
    get_cobie_validation_history,
    get_latest_cobie_validation,
    validate_cobie,
)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")


@router.post("/projects/{project_id}/validate-cobie")
async def upload_and_validate_cobie(
    project_id: int,
    file: UploadFile = File(...),
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload COBie XLSX și validare completă."""
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Fișierul trebuie să fie .xlsx")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    timestamp = int(time.time())
    safe_name = file.filename.replace(" ", "_")
    dest_filename = f"{project_id}_{timestamp}_cobie_{safe_name}"
    dest_path = os.path.join(UPLOAD_DIR, dest_filename)

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    try:
        result = validate_cobie(
            db=db,
            project_id=project_id,
            file_path=dest_path,
            filename=file.filename,
            file_size_bytes=len(content),
            validation_type="full",
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la validare: {str(e)}")


@router.get("/projects/{project_id}/cobie-validations")
def list_cobie_validations(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează istoricul validărilor COBie."""
    validations = get_cobie_validation_history(db, project_id)
    return [
        {
            "id": v.id,
            "filename": v.filename,
            "validation_type": v.validation_type,
            "overall_status": v.overall_status,
            "score": v.score,
            "total_checks": v.total_checks,
            "pass_count": v.pass_count,
            "warning_count": v.warning_count,
            "fail_count": v.fail_count,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in validations
    ]


@router.get("/projects/{project_id}/cobie-latest")
def get_latest_cobie(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează ultima validare COBie cu rezultate complete."""
    v = get_latest_cobie_validation(db, project_id)
    if not v:
        return {"message": "Nu există validări COBie pentru acest proiect."}
    return {
        "id": v.id,
        "filename": v.filename,
        "validation_type": v.validation_type,
        "overall_status": v.overall_status,
        "score": v.score,
        "total_checks": v.total_checks,
        "pass_count": v.pass_count,
        "warning_count": v.warning_count,
        "fail_count": v.fail_count,
        "results_json": v.results_json,
        "sheet_stats_json": v.sheet_stats_json,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


@router.post("/projects/{project_id}/generate-cobie-template")
def generate_template(
    project_id: int,
    body: CobieTemplateRequest | None = None,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generează și descarcă template COBie XLSX."""
    req = body or CobieTemplateRequest()
    output = generate_cobie_template(
        db=db,
        project_id=project_id,
        include_ai_suggestions=req.include_ai_suggestions,
        target_sheets=req.target_sheets,
    )
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=COBie_Template_{project_id}.xlsx"
        },
    )
