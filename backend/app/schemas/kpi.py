"""
kpi.py — Scheme Pydantic pentru KPI tracking.
"""

from __future__ import annotations

from pydantic import BaseModel


class KpiMeasurementCreate(BaseModel):
    """Măsurare KPI de creat."""
    kpi_name: str
    category: str
    value: float
    target_value: float | None = None
    measurement_date: str


class KpiMeasurementRead(BaseModel):
    """Măsurare KPI returnată de API."""
    id: int
    project_id: int
    kpi_name: str
    category: str
    value: float
    target_value: float | None = None
    measurement_date: str
    created_at: str


class KpiDashboardRead(BaseModel):
    """Dashboard KPI complet."""
    project_id: int
    kpis: list[dict] = []
    categories: list[str] = []
    overall_score: float = 0.0
