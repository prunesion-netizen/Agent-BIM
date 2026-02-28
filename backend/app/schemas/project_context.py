"""
project_context.py — Modele Pydantic pentru fișa de proiect BEP 2.0
Conform ISO 19650-2, adaptate la specificul construcțiilor din România.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BimTeamRole(BaseModel):
    """Rol în echipa BIM."""
    role_name: str = Field(..., description="Numele rolului (ex: BIM Manager)")
    role_code: str = Field(..., description="Cod rol (ex: BM, BC, BA)")
    organization: str = Field(..., description="Organizația/firma")
    person_name: str | None = Field(None, description="Numele persoanei desemnate")
    email: str | None = Field(None, description="Adresa de email")


class SoftwareItem(BaseModel):
    """Software utilizat în proiect."""
    name: str = Field(..., description="Numele softului (ex: Autodesk Revit)")
    version_min: str = Field("", description="Versiunea minimă (ex: 2024)")
    use_case: str = Field("", description="Scop utilizare (ex: Modelare 3D)")


class ProjectContext(BaseModel):
    """
    Fișa de proiect BEP 2.0 — toate datele necesare pentru generarea
    unui BIM Execution Plan conform ISO 19650-2.
    """

    # ── Identificare proiect ──────────────────────────────────────────────
    project_name: str = Field(..., description="Denumirea proiectului")
    project_code: str = Field(..., description="Cod intern proiect")
    project_type: Literal[
        "building", "hospital", "landfill",
        "infrastructure", "industrial", "other"
    ] = Field(..., description="Tipul de proiect")
    project_description: str | None = Field(None, description="Descriere scurtă")

    # ── Locație ───────────────────────────────────────────────────────────
    location_city: str | None = None
    location_county: str | None = None
    location_country: str | None = Field("România")

    # ── Părți implicate ───────────────────────────────────────────────────
    client_name: str = Field(..., description="Numele beneficiarului")
    client_type: Literal["public", "private"] = "public"
    designer_name: str | None = None
    internal_project_number: str | None = None
    design_contract_number: str | None = None
    construction_contract_number: str | None = None

    # ── Faza și versiune BEP ──────────────────────────────────────────────
    current_phase: Literal[
        "precontract", "PT", "DDE", "execution", "asbuilt"
    ] = "PT"
    bep_date: date = Field(default_factory=date.today)
    bep_version: str = "1.0"

    # ── EIR ───────────────────────────────────────────────────────────────
    has_eir: bool = False
    eir_document_id: str | None = None
    client_bim_goals: list[str] = Field(default_factory=list)
    internal_bim_goals: list[str] = Field(default_factory=list)

    # ── Echipa BIM ────────────────────────────────────────────────────────
    bim_team_roles: list[BimTeamRole] = Field(default_factory=list)

    # ── CDE ───────────────────────────────────────────────────────────────
    cde_platform: Literal[
        "acc", "trimble", "bimcollab", "sharepoint", "other"
    ] = "acc"
    cde_modules: list[Literal[
        "docs", "coordinate", "build", "takeoff", "issues", "other"
    ]] = Field(default_factory=list)
    has_custom_cde_structure: bool = False
    document_naming_convention: str | None = None

    # ── Standarde ─────────────────────────────────────────────────────────
    iso_19650_1: bool = True
    iso_19650_2: bool = True
    iso_19650_3: bool = False
    other_bim_standards: list[str] = Field(default_factory=list)
    national_standards: list[str] = Field(default_factory=list)

    # ── Software ──────────────────────────────────────────────────────────
    design_software: list[SoftwareItem] = Field(default_factory=list)
    coordination_software: list[SoftwareItem] = Field(default_factory=list)
    planning_cost_software: list[SoftwareItem] = Field(default_factory=list)

    # ── Discipline și modele ──────────────────────────────────────────────
    disciplines: list[Literal[
        "architecture", "structure", "mep", "civil",
        "roads", "infrastructure", "other"
    ]] = Field(default_factory=list)
    uses_federated_models: bool = True
    main_exchange_format: Literal[
        "ifc4_3", "ifc2x3", "nwd", "nwc", "dwg", "other"
    ] = "ifc4_3"

    # ── LOD ───────────────────────────────────────────────────────────────
    lod_scale: str | None = None
    lod_target_pt: str | None = None
    lod_target_dde: str | None = None
    lod_target_execution: str | None = None
    loi_special_requirements: list[str] = Field(default_factory=list)

    # ── Livrabile și jaloane ──────────────────────────────────────────────
    bim_milestones: list[str] = Field(default_factory=list)
    bim_deliverable_types: list[str] = Field(default_factory=list)

    # ── Coordonare ────────────────────────────────────────────────────────
    coordination_meeting_design_frequency: str | None = None
    coordination_meeting_execution_frequency: str | None = None
    clash_detection_tool: Literal[
        "navisworks", "acc_coordinate", "bimcollab", "other"
    ] = "navisworks"
    clash_tolerance_critical_dde: str | None = None
    bim_kpis: list[str] = Field(default_factory=list)
