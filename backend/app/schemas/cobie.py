"""
cobie.py — Pydantic schemas + constante pentru validarea COBie XLSX.

COBie (Construction Operations Building information exchange) definește
16 sheet-uri standard cu coloane obligatorii per sheet.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════════════
# Constante COBie standard
# ══════════════════════════════════════════════════════════════════════════════

COBIE_REQUIRED_SHEETS: list[str] = [
    "Facility",
    "Floor",
    "Space",
    "Zone",
    "Type",
    "Component",
    "System",
    "Assembly",
    "Spare",
    "Resource",
    "Job",
    "Document",
    "Attribute",
    "Coordinate",
    "Connection",
    "Issue",
]

# Coloane obligatorii per sheet (Name, CreatedBy, CreatedOn sunt comune)
_COMMON_COLS = ["Name", "CreatedBy", "CreatedOn"]

COBIE_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "Facility": _COMMON_COLS + [
        "Category", "ProjectName", "SiteName", "LinearUnits",
        "AreaUnits", "VolumeUnits", "CurrencyUnit", "AreaMeasurement",
    ],
    "Floor": _COMMON_COLS + ["Category", "Elevation"],
    "Space": _COMMON_COLS + ["FloorName", "Category", "RoomTag"],
    "Zone": _COMMON_COLS + ["Category", "SpaceNames"],
    "Type": _COMMON_COLS + [
        "Category", "Description", "Manufacturer",
        "ModelNumber", "NominalLength", "NominalWidth", "NominalHeight",
    ],
    "Component": _COMMON_COLS + [
        "TypeName", "Space", "Description", "SerialNumber",
    ],
    "System": _COMMON_COLS + ["Category", "ComponentNames"],
    "Assembly": _COMMON_COLS + ["SheetName", "ParentName", "ChildNames"],
    "Spare": _COMMON_COLS + ["Category", "TypeName", "Suppliers"],
    "Resource": _COMMON_COLS + ["Category", "TypeName"],
    "Job": _COMMON_COLS + ["Category", "TypeName", "Duration", "Frequency"],
    "Document": _COMMON_COLS + [
        "Category", "ApprovalBy", "Stage", "SheetName", "RowName",
        "Directory", "File",
    ],
    "Attribute": _COMMON_COLS + [
        "SheetName", "RowName", "Value", "Unit", "Description",
    ],
    "Coordinate": _COMMON_COLS + [
        "Category", "SheetName", "RowName",
        "CoordinateXAxis", "CoordinateYAxis", "CoordinateZAxis",
    ],
    "Connection": _COMMON_COLS + [
        "ConnectionType", "SheetName", "RowName1", "RowName2",
    ],
    "Issue": _COMMON_COLS + [
        "Type", "Risk", "Chance", "Impact", "SheetName1", "RowName1",
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic models
# ══════════════════════════════════════════════════════════════════════════════

class CobieSheetCheck(BaseModel):
    """Rezultat validare per sheet COBie."""
    sheet_name: str
    status: str = Field(description="pass | warning | fail | missing")
    row_count: int = 0
    expected_columns: list[str] = []
    present_columns: list[str] = []
    missing_columns: list[str] = []
    empty_required_cells: int = 0
    total_required_cells: int = 0
    details: str = ""


class CobieValidationCheck(BaseModel):
    """Verificare project-specific (comparație cu ProjectContext)."""
    id: str
    label: str
    status: str = Field(description="pass | warning | fail")
    details: str = ""


class CobieValidationResult(BaseModel):
    """Rezultat complet validare COBie."""
    score: float = 0.0
    overall_status: str = "fail"
    total_checks: int = 0
    pass_count: int = 0
    warning_count: int = 0
    fail_count: int = 0
    sheet_checks: list[CobieSheetCheck] = []
    project_checks: list[CobieValidationCheck] = []
    recommendations: list[str] = []


class CobieValidationRead(BaseModel):
    """Response API — validare COBie salvată."""
    id: int
    project_id: int
    filename: str
    file_size_bytes: Optional[int] = None
    validation_type: str
    overall_status: str
    score: float
    total_checks: int
    pass_count: int
    warning_count: int
    fail_count: int
    results_json: Optional[dict] = None
    sheet_stats_json: Optional[dict] = None
    created_at: Optional[str] = None


class CobieTemplateRequest(BaseModel):
    """Request pentru generare template COBie XLSX."""
    include_ai_suggestions: bool = False
    target_sheets: Optional[list[str]] = None
