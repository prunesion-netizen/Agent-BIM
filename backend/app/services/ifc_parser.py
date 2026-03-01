"""
ifc_parser.py — Parsează un fișier IFC și generează un ModelSummary pre-populat.

Folosește ifcopenshell pentru extracția metadatelor:
discipline, categorii de elemente, georeferențiere, schema IFC.
"""

from __future__ import annotations

import logging

import ifcopenshell

from app.schemas.model_summary import CategoryStats, ModelSummary

logger = logging.getLogger(__name__)

# Mapping: IFC entity types → discipline
_DISCIPLINE_MAP: dict[str, str] = {
    # Architecture
    "IfcWall": "architecture",
    "IfcSlab": "architecture",
    "IfcDoor": "architecture",
    "IfcWindow": "architecture",
    "IfcRoof": "architecture",
    "IfcStair": "architecture",
    "IfcRailing": "architecture",
    "IfcCurtainWall": "architecture",
    # Structure
    "IfcBeam": "structure",
    "IfcColumn": "structure",
    "IfcFooting": "structure",
    "IfcPile": "structure",
    "IfcReinforcingBar": "structure",
    # MEP
    "IfcDuctSegment": "mep",
    "IfcPipeSegment": "mep",
    "IfcFlowTerminal": "mep",
    "IfcFlowSegment": "mep",
    "IfcCableSegment": "mep",
    # Infrastructure / Roads
    "IfcRoad": "roads",
    "IfcAlignment": "infrastructure",
    "IfcCourse": "infrastructure",
}

# IFC schema → exchange format literal
_SCHEMA_FORMAT_MAP: dict[str, str] = {
    "IFC4X3": "ifc4_3",
    "IFC4x3": "ifc4_3",
    "IFC4": "ifc4_3",
    "IFC2X3": "ifc2x3",
    "IFC2x3": "ifc2x3",
}

MAX_CATEGORIES = 20


def generate_model_summary_from_ifc(file_path: str) -> ModelSummary:
    """Parsează un fișier IFC și returnează un ModelSummary pre-populat."""
    try:
        ifc_file = ifcopenshell.open(file_path)
    except Exception as exc:
        logger.exception("Nu s-a putut deschide fișierul IFC: %s", file_path)
        return ModelSummary(
            source="ifc",
            notes=f"Eroare la deschiderea fișierului IFC: {exc}",
        )

    try:
        return _extract_summary(ifc_file)
    except Exception as exc:
        logger.exception("Eroare la parsarea IFC: %s", file_path)
        return ModelSummary(
            source="ifc",
            notes=f"Eroare la parsarea IFC: {exc}",
        )


def _extract_summary(ifc_file: ifcopenshell.file) -> ModelSummary:
    """Logica principală de extracție din fișierul IFC deschis."""

    # ── Discipline & Categorii ───────────────────────────────────────────────
    disciplines: set[str] = set()
    category_counts: dict[str, int] = {}

    for ifc_type, discipline in _DISCIPLINE_MAP.items():
        try:
            elements = ifc_file.by_type(ifc_type)
        except Exception:
            continue
        count = len(elements)
        if count > 0:
            disciplines.add(discipline)
            category_counts[ifc_type] = count

    # Verifică dacă există tipuri IFC suplimentare cu elemente (→ "other")
    all_products = ifc_file.by_type("IfcProduct")
    mapped_count = sum(category_counts.values())
    if len(all_products) > mapped_count:
        remaining = len(all_products) - mapped_count
        if remaining > 0 and not disciplines:
            disciplines.add("other")

    # Categorii sortate descrescător, limitate la top N
    categories = [
        CategoryStats(name=name, element_count=count)
        for name, count in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        )
    ][:MAX_CATEGORIES]

    # ── Georeferențiere ──────────────────────────────────────────────────────
    has_georef = False
    coord_system: str | None = None

    try:
        map_conversions = ifc_file.by_type("IfcMapConversion")
        if map_conversions:
            has_georef = True
    except Exception:
        pass

    try:
        projected_crs_list = ifc_file.by_type("IfcProjectedCRS")
        if projected_crs_list:
            has_georef = True
            crs = projected_crs_list[0]
            if hasattr(crs, "Name") and crs.Name:
                coord_system = str(crs.Name)
    except Exception:
        pass

    # ── Schema → format ──────────────────────────────────────────────────────
    schema = ifc_file.schema
    exchange_format = _SCHEMA_FORMAT_MAP.get(schema, "ifc4_3")

    # ── Notes (metadata) ─────────────────────────────────────────────────────
    notes_parts: list[str] = [f"IFC Schema: {schema}"]

    try:
        apps = ifc_file.by_type("IfcApplication")
        if apps:
            app = apps[0]
            app_name = getattr(app, "ApplicationFullName", None) or ""
            app_ver = getattr(app, "Version", None) or ""
            if app_name:
                notes_parts.append(
                    f"Aplicație: {app_name} {app_ver}".strip()
                )
    except Exception:
        pass

    try:
        projects = ifc_file.by_type("IfcProject")
        if projects:
            proj_name = getattr(projects[0], "Name", None)
            if proj_name:
                notes_parts.append(f"Proiect IFC: {proj_name}")
    except Exception:
        pass

    return ModelSummary(
        source="ifc",
        disciplines_present=sorted(disciplines),
        categories=categories,
        has_georeference=has_georef,
        coordinate_system=coord_system,
        exchange_formats_available=[exchange_format],
        lod_info_available=False,
        notes="; ".join(notes_parts),
    )
