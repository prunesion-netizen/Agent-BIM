"""
verifier.py — Router API pentru verificarea conformității BEP vs Model BIM.
POST /api/verify-bep — primește model_summary, returnează raport de verificare.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.bep_verifier import verify_bep

router = APIRouter()


class VerifyBepRequest(BaseModel):
    project_code: str
    model_summary: dict


class VerifyBepResponse(BaseModel):
    report_markdown: str
    checks: list[dict]
    summary: dict


@router.post("/verify-bep", response_model=VerifyBepResponse)
def api_verify_bep(req: VerifyBepRequest):
    """
    Verifică conformitatea BEP vs Model BIM.

    Primește project_code (pentru BEP-ul stocat) și model_summary
    (rezumat tehnic al modelului). Returnează raport cu checks și status.
    """
    if not req.project_code.strip():
        raise HTTPException(status_code=400, detail="project_code nu poate fi gol.")
    if not req.model_summary:
        raise HTTPException(status_code=400, detail="model_summary nu poate fi gol.")

    try:
        result = verify_bep(
            project_code=req.project_code.strip(),
            model_summary=req.model_summary,
        )
        return VerifyBepResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
