"""
requirements_templates.py — Template-uri default OIR / PIR / AIR per tip proiect.

Cascada ISO 19650-1: OIR → PIR → AIR → EIR
Fiecare nivel are cerințe pre-definite, reale, relevante pentru România.
"""

from __future__ import annotations

from app.schemas.project_context import InformationRequirement


# ══════════════════════════════════════════════════════════════════════════════
# OIR — Organizational Information Requirements
# ══════════════════════════════════════════════════════════════════════════════

_OIR_COMMON: list[dict] = [
    {
        "id": "OIR-01",
        "category": "Strategie",
        "description": "Informații necesare pentru luarea deciziilor strategice de investiție și planificare a portofoliului de active",
        "priority": "high",
        "success_criteria": "Rapoarte decizionale generate din modelul BIM la fiecare etapă majoră",
    },
    {
        "id": "OIR-02",
        "category": "Legal",
        "description": "Conformitate cu legislația națională (Legea 10/1995, HG 907/2016) și reglementările de urbanism",
        "priority": "high",
        "success_criteria": "Documentație conformă depusă la autoritățile competente",
    },
    {
        "id": "OIR-03",
        "category": "FM",
        "description": "Date structurate pentru managementul facilităților (FM) pe întreaga durată de viață a activului",
        "priority": "medium",
        "success_criteria": "Export COBie complet validat la predare",
    },
    {
        "id": "OIR-04",
        "category": "Sustenabilitate",
        "description": "Informații pentru evaluarea performanței energetice și impactului de mediu (nZEB, BREEAM, LEED)",
        "priority": "medium",
        "success_criteria": "Simulare energetică realizată pe modelul BIM LOD 300+",
    },
    {
        "id": "OIR-05",
        "category": "Financiar",
        "description": "Extragere cantități și costuri din model BIM pentru controlul bugetului",
        "priority": "high",
        "success_criteria": "Deviz generat automat din model cu diferență <5% față de estimare manuală",
    },
]

_OIR_HOSPITAL: list[dict] = [
    {
        "id": "OIR-06",
        "category": "Siguranță",
        "description": "Trasabilitatea echipamentelor medicale și a zonelor sterile pe toată durata de viață",
        "priority": "high",
        "success_criteria": "Fiecare echipament medical identificat în model cu cod unic și fișă tehnică",
    },
    {
        "id": "OIR-07",
        "category": "Operațional",
        "description": "Fluxuri de circulație pacienți/personal/logistică modelate și validate",
        "priority": "high",
        "success_criteria": "Simulare flux validată de echipa medicală",
    },
]

_OIR_INFRASTRUCTURE: list[dict] = [
    {
        "id": "OIR-06",
        "category": "Operațional",
        "description": "Monitorizare structurală și senzori IoT integrați în modelul asset",
        "priority": "high",
        "success_criteria": "Puncte de monitorizare definite în model cu coordonate precise",
    },
    {
        "id": "OIR-07",
        "category": "Legal",
        "description": "Predare cadastru digital și documentație GIS conformă la autoritățile locale",
        "priority": "high",
        "success_criteria": "Export GIS/shapefile validat din modelul georeferențiat",
    },
]

_OIR_LANDFILL: list[dict] = [
    {
        "id": "OIR-06",
        "category": "Mediu",
        "description": "Monitorizare emisii, levigat și stabilitate taluzuri pe întreaga durată de exploatare",
        "priority": "high",
        "success_criteria": "Senzori de monitorizare poziționați în model cu acces FM digital",
    },
    {
        "id": "OIR-07",
        "category": "Legal",
        "description": "Conformitate cu Directiva 1999/31/CE privind depozitele de deșeuri și autorizația de mediu",
        "priority": "high",
        "success_criteria": "Documentație de mediu generată din model și depusă la APM",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# PIR — Project Information Requirements
# ══════════════════════════════════════════════════════════════════════════════

_PIR_COMMON: list[dict] = [
    {
        "id": "PIR-01",
        "category": "Proiectare",
        "description": "Model BIM 3D LOD 300 pentru toate disciplinele, cu coordonare clash-free la emiterea DDE",
        "priority": "high",
        "success_criteria": "0 clash-uri hard între discipline la milestone DDE",
    },
    {
        "id": "PIR-02",
        "category": "Coordonare",
        "description": "Ședințe de coordonare BIM săptămânale cu raport clash detection",
        "priority": "high",
        "success_criteria": "Raport BCF generat și distribuit după fiecare ședință",
    },
    {
        "id": "PIR-03",
        "category": "Livrare",
        "description": "Export IFC validat la fiecare milestone conform TIDP",
        "priority": "high",
        "success_criteria": "Fișiere IFC validate cu IFC Checker, fără erori critice",
    },
    {
        "id": "PIR-04",
        "category": "Calitate",
        "description": "Verificare BEP vs model la fiecare fază de proiectare",
        "priority": "medium",
        "success_criteria": "Raport verificare cu scor >80% la fiecare milestone",
    },
    {
        "id": "PIR-05",
        "category": "Cantități",
        "description": "Extragere cantități din model BIM pentru deviz estimativ și verificare",
        "priority": "medium",
        "success_criteria": "Liste cantități exportate din model la fiecare fază",
    },
]

_PIR_HOSPITAL: list[dict] = [
    {
        "id": "PIR-06",
        "category": "Siguranță",
        "description": "Modelarea zonelor de risc clinic (sterile, radioactive, infecțioase) cu proprietăți specifice",
        "priority": "high",
        "success_criteria": "Zone clasificate în model cu atribute IfcZone validate",
    },
]

_PIR_INFRASTRUCTURE: list[dict] = [
    {
        "id": "PIR-06",
        "category": "Geospațial",
        "description": "Georeferențierea modelului în Stereo 70 / ETRS89 cu toleranță <10cm",
        "priority": "high",
        "success_criteria": "IfcMapConversion definit, validat cu puncte de control topografic",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# AIR — Asset Information Requirements
# ══════════════════════════════════════════════════════════════════════════════

_AIR_COMMON: list[dict] = [
    {
        "id": "AIR-01",
        "category": "Identificare",
        "description": "Fiecare echipament/component major identificat cu cod unic, tip, producător și model",
        "priority": "high",
        "success_criteria": "COBie Type sheet completat cu Manufacturer + ModelNumber pentru toate tipurile",
        "related_assets": ["Echipamente HVAC", "Lifturi", "Generatoare", "UPS"],
        "related_deliverables": ["COBie", "BIM-LIV-AsBuilt"],
    },
    {
        "id": "AIR-02",
        "category": "Mantenanță",
        "description": "Program de mentenanță preventivă (frecvență, durată, resurse) pentru echipamentele critice",
        "priority": "medium",
        "success_criteria": "COBie Job sheet populat cu frecvențe și durate reale",
        "related_assets": ["Instalații HVAC", "Sisteme PSI", "Ascensoare"],
        "related_deliverables": ["COBie", "Plan mentenanță"],
    },
    {
        "id": "AIR-03",
        "category": "Performanță",
        "description": "Proprietăți termice, acustice și de rezistență la foc pentru elementele de anvelopă",
        "priority": "medium",
        "success_criteria": "PropertySets cu U-value, Rw, REI definite pe elemente de anvelopă în model",
        "related_assets": ["Pereți exteriori", "Tâmplărie", "Acoperiș"],
        "related_deliverables": ["Raport energetic", "Certificat energetic"],
    },
    {
        "id": "AIR-04",
        "category": "Spațiu",
        "description": "Suprafețe utile, arii circulație și volume pe zone funcționale",
        "priority": "high",
        "success_criteria": "COBie Space sheet cu FloorName + Category + RoomTag completate",
        "related_assets": [],
        "related_deliverables": ["COBie", "Bilanț suprafețe"],
    },
    {
        "id": "AIR-05",
        "category": "Documente",
        "description": "Fișe tehnice, certificate de conformitate și garanții atașate echipamentelor",
        "priority": "medium",
        "success_criteria": "COBie Document sheet cu fișiere atașate per echipament",
        "related_assets": ["Toate echipamentele majore"],
        "related_deliverables": ["COBie", "Dosar As-Built"],
    },
]

_AIR_HOSPITAL: list[dict] = [
    {
        "id": "AIR-06",
        "category": "Medical",
        "description": "Echipamente medicale cu clasă de risc, protocol dezinfecție, cerințe alimentare electrice",
        "priority": "high",
        "success_criteria": "Fiecare echipament medical cu PropertySet dedicat (clasă risc, putere, circuit)",
        "related_assets": ["CT", "RMN", "Echipamente bloc operator", "Echipamente ATI"],
        "related_deliverables": ["COBie", "Caiet sarcini echipamente"],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════


def get_default_oir(project_type: str) -> list[InformationRequirement]:
    """Returnează OIR-uri default per tip proiect."""
    items = list(_OIR_COMMON)
    if project_type == "hospital":
        items.extend(_OIR_HOSPITAL)
    elif project_type in ("infrastructure", "roads"):
        items.extend(_OIR_INFRASTRUCTURE)
    elif project_type == "landfill":
        items.extend(_OIR_LANDFILL)
    return [InformationRequirement(**item) for item in items]


def get_default_pir(project_type: str) -> list[InformationRequirement]:
    """Returnează PIR-uri default per tip proiect."""
    items = list(_PIR_COMMON)
    if project_type == "hospital":
        items.extend(_PIR_HOSPITAL)
    elif project_type in ("infrastructure", "roads"):
        items.extend(_PIR_INFRASTRUCTURE)
    return [InformationRequirement(**item) for item in items]


def get_default_air(project_type: str) -> list[InformationRequirement]:
    """Returnează AIR-uri default per tip proiect."""
    items = list(_AIR_COMMON)
    if project_type == "hospital":
        items.extend(_AIR_HOSPITAL)
    return [InformationRequirement(**item) for item in items]


def build_traceability_matrix(
    oir: list[InformationRequirement],
    pir: list[InformationRequirement],
    air: list[InformationRequirement],
) -> dict:
    """
    Construiește matricea de trasabilitate OIR → PIR → AIR.

    Maparea se face pe baza categoriilor partajate:
    - PIR cu aceeași categorie ca un OIR sunt legate
    - AIR cu aceeași categorie ca un PIR sunt legate
    """
    matrix: dict = {
        "oir_count": len(oir),
        "pir_count": len(pir),
        "air_count": len(air),
        "links": [],
    }

    # Build category maps
    oir_by_cat: dict[str, list[str]] = {}
    for o in oir:
        oir_by_cat.setdefault(o.category, []).append(o.id)

    pir_by_cat: dict[str, list[str]] = {}
    for p in pir:
        pir_by_cat.setdefault(p.category, []).append(p.id)

    # OIR → PIR links (category overlap)
    for p in pir:
        linked_oirs = oir_by_cat.get(p.category, [])
        for oir_id in linked_oirs:
            matrix["links"].append({
                "from": oir_id,
                "to": p.id,
                "type": "OIR→PIR",
                "category": p.category,
            })

    # PIR → AIR links (category overlap)
    for a in air:
        linked_pirs = pir_by_cat.get(a.category, [])
        for pir_id in linked_pirs:
            matrix["links"].append({
                "from": pir_id,
                "to": a.id,
                "type": "PIR→AIR",
                "category": a.category,
            })

    # Summary per level
    matrix["oir_categories"] = sorted(set(o.category for o in oir))
    matrix["pir_categories"] = sorted(set(p.category for p in pir))
    matrix["air_categories"] = sorted(set(a.category for a in air))

    # Coverage: categories with OIR but no PIR
    oir_cats = set(o.category for o in oir)
    pir_cats = set(p.category for p in pir)
    air_cats = set(a.category for a in air)
    matrix["gaps"] = {
        "oir_without_pir": sorted(oir_cats - pir_cats),
        "pir_without_air": sorted(pir_cats - air_cats),
    }

    return matrix
