"""
model_summary.py — Schema Pydantic pentru rezumatul tehnic al unui model BIM.
Utilizat de endpoint-ul de verificare BEP vs Model.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CategoryStats(BaseModel):
    """Statistici per categorie de elemente din model (Revit/IFC)."""
    name: str = Field(..., description="Numele categoriei (ex: Walls, Floors, Ducts)")
    element_count: int = Field(..., description="Numarul de elemente din categorie")


class ModelSummary(BaseModel):
    """
    Rezumat tehnic al modelului BIM.
    Completat de utilizator sau extras automat dintr-un fișier Revit/IFC.
    """

    source: Literal["revit", "ifc", "other"] = Field(
        "revit", description="Sursa modelului"
    )

    disciplines_present: list[Literal[
        "architecture", "structure", "mep", "civil",
        "roads", "infrastructure", "other"
    ]] = Field(default_factory=list, description="Discipline prezente in model")

    categories: list[CategoryStats] = Field(
        default_factory=list,
        description="Statistici per categorie de elemente"
    )

    has_georeference: bool = Field(
        False, description="Modelul are georeferentiere"
    )

    coordinate_system: str | None = Field(
        None, description="Sistem de coordonate (ex: Stereo 70 / EPSG:31700)"
    )

    exchange_formats_available: list[Literal[
        "ifc4_3", "ifc2x3", "nwd", "nwc", "dwg", "other"
    ]] = Field(default_factory=list, description="Formate de schimb disponibile")

    lod_info_available: bool = Field(
        False, description="Exista informatii LOD/LOI in model"
    )

    notes: str | None = Field(
        None, description="Observatii suplimentare"
    )
