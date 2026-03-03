"""
agent_tools.py — Definirea tool-urilor agentului BIM (Anthropic tool schemas)
și funcțiile handler care refolosesc serviciile existente.

13 tool-uri:
1. get_project_info       — Info proiect + status
2. get_project_context    — Fișa completă BEP (ProjectContext)
3. generate_bep           — Generare BEP complet
4. verify_bep             — Verificare BEP vs Model
5. export_bep_docx        — Returnează URL descărcare DOCX
6. update_project_context — Update câmpuri specifice
7. get_verification_history — Istoric verificări
8. search_bim_standards   — Căutare standarde BIM (ChromaDB)
9. analyze_ifc_model      — Analizează modelul IFC importat
10. list_document_versions — Lista versiuni BEP
11. compare_bep_versions  — Comparare între versiuni BEP
12. get_audit_trail       — Jurnal activități proiect
13. get_project_health_check — Diagnostic sănătate proiect
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.projects_repository import (
    get_project,
    get_latest_project_context,
    save_project_context,
    get_latest_generated_document,
    save_generated_document,
    list_verification_reports,
    get_latest_uploaded_file,
    list_audit_logs,
    list_bep_documents,
)
from app.models.sql_models import GeneratedDocumentModel
from app.schemas.converters import (
    project_model_to_read,
    document_model_to_read,
    document_model_to_history_item,
)
from app.schemas.project_context import ProjectContext
from app.services.project_status import (
    on_context_saved,
    on_bep_generated,
    on_bep_verified,
)
from app.services.bep_generator import generate_bep
from app.services.chat_expert import store_bep
from app.ai_client import call_llm_bep_verifier
from app.services.bep_docx_exporter import markdown_to_docx
from app.services.standards_search import search_standards
from app.services.audit import log_action
from app.services.bep_diff import compare_bep_versions as _diff_bep
from app.services.project_health import compute_project_health

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Tool definitions (Anthropic tool schema format)
# ══════════════════════════════════════════════════════════════════════════════

AGENT_TOOLS: list[dict] = [
    {
        "name": "get_project_info",
        "description": (
            "Returnează informații despre proiectul curent: "
            "nume, cod, client, tip, status, date creare/actualizare."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_project_context",
        "description": (
            "Returnează fișa completă BEP (ProjectContext) a proiectului: "
            "faza, discipline, CDE, LOD, obiective BIM, echipa, software, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "generate_bep",
        "description": (
            "Generează un BIM Execution Plan (BEP) complet pentru proiect "
            "pe baza fișei BEP (ProjectContext). Necesită ca fișa BEP să fie deja completată. "
            "Returnează BEP-ul în format Markdown."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului pentru care se generează BEP-ul",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "verify_bep",
        "description": (
            "Verifică conformitatea BEP-ului generat cu modelul BIM al proiectului. "
            "Compară ce e specificat în BEP cu starea modelului și identifică "
            "neconformități, riscuri sau lipsuri. Necesită BEP generat anterior."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "export_bep_docx",
        "description": (
            "Exportă BEP-ul proiectului ca document DOCX. "
            "Returnează URL-ul de descărcare. Necesită BEP generat anterior."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "update_project_context",
        "description": (
            "Actualizează câmpuri specifice din fișa BEP (ProjectContext) a proiectului. "
            "Trimite un dict cu câmpurile de actualizat. Câmpurile nespecificate rămân neschimbate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
                "updates": {
                    "type": "object",
                    "description": (
                        "Dict cu câmpurile de actualizat din ProjectContext. "
                        "Exemplu: {\"project_name\": \"Spital Nord\", \"cde_platform\": \"acc\"}"
                    ),
                },
            },
            "required": ["project_id", "updates"],
        },
    },
    {
        "name": "get_verification_history",
        "description": (
            "Returnează istoricul verificărilor BEP vs Model ale proiectului: "
            "data, status general, număr de fail/warning."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "search_bim_standards",
        "description": (
            "Caută în baza de date de standarde și norme BIM (ISO 19650, RTC, etc.) "
            "pentru a găsi informații relevante. Folosește pentru a răspunde la întrebări "
            "despre standarde, bune practici, cerințe normative."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Textul de căutare (întrebare sau cuvinte cheie)",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Numărul de rezultate dorite (default 5)",
                },
            },
            "required": ["query"],
        },
    },
    # ── Tool-uri noi (Faza 1A, 2A, 2B, 3B) ──────────────────────────────
    {
        "name": "analyze_ifc_model",
        "description": (
            "Analizează modelul IFC importat pentru proiect. Returnează un sumar "
            "detaliat: total elemente pe categorii, discipline detectate, "
            "georeferențiere, format IFC, potențiale probleme de clash."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "list_document_versions",
        "description": (
            "Returnează lista tuturor versiunilor BEP generate pentru proiect, "
            "cu date, dimensiuni și versiuni. Util pentru a vedea evoluția documentelor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "compare_bep_versions",
        "description": (
            "Compară două versiuni BEP ale proiectului pe secțiuni. "
            "Identifică secțiunile adăugate, șterse și modificate. "
            "Fără parametri de versiune, compară ultimele două versiuni."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
                "version_a_id": {
                    "type": "integer",
                    "description": "ID-ul documentului versiunii A (mai vechi). Opțional.",
                },
                "version_b_id": {
                    "type": "integer",
                    "description": "ID-ul documentului versiunii B (mai nou). Opțional.",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_audit_trail",
        "description": (
            "Returnează jurnalul de activități al proiectului: "
            "cine a făcut ce, când. Conformitate ISO 19650 — trasabilitate completă."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
                "limit": {
                    "type": "integer",
                    "description": "Numărul maxim de intrări (default 20)",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_project_health_check",
        "description": (
            "Verifică sănătatea proiectului BIM: scor completitudine (0-100%), "
            "câmpuri lipsă, alerte temporale, recomandări prioritizate. "
            "Folosește pentru a ghida utilizatorul spre pașii următori."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "ID-ul proiectului",
                },
            },
            "required": ["project_id"],
        },
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# Tool handlers — funcții care execută tool-urile
# ══════════════════════════════════════════════════════════════════════════════

def handle_get_project_info(db: Session, tool_input: dict) -> dict:
    """Handler pentru get_project_info."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}
    return project_model_to_read(project).model_dump()


def handle_get_project_context(db: Session, tool_input: dict) -> dict:
    """Handler pentru get_project_context."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    if not ctx_entry:
        return {
            "error": (
                f"Nu există fișă BEP (ProjectContext) pentru proiectul "
                f"'{project.name}' ({project.code}). "
                "Utilizatorul trebuie să completeze mai întâi fișa din tab-ul 'Fișa BEP'."
            ),
        }
    return ctx_entry.context_json


def handle_generate_bep(db: Session, tool_input: dict) -> dict:
    """Handler pentru generate_bep."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    if not ctx_entry:
        return {
            "error": (
                "Nu există fișă BEP (ProjectContext). "
                "Completează mai întâi fișa proiectului din tab-ul 'Fișa BEP'."
            ),
        }

    try:
        project_context = ProjectContext(**ctx_entry.context_json)
        result = generate_bep(project_context)
        bep_markdown = result["bep_markdown"]

        doc = save_generated_document(
            db,
            project_id=project_id,
            doc_type="bep",
            title=f"BEP {project.code} {project_context.bep_version}",
            content_markdown=bep_markdown,
            version=project_context.bep_version,
        )
        on_bep_generated(db, project_id)
        store_bep(project.code, bep_markdown)

        log_action(db, project_id, "generate_bep", {
            "document_id": doc.id,
            "version": project_context.bep_version,
            "length": len(bep_markdown),
        })

        return {
            "success": True,
            "message": (
                f"BEP generat cu succes pentru proiectul '{project.name}' "
                f"({project.code}), versiunea {project_context.bep_version}."
            ),
            "document_id": doc.id,
            "bep_version": project_context.bep_version,
            "bep_length": len(bep_markdown),
        }
    except Exception as e:
        logger.error(f"Eroare la generare BEP: {e}")
        return {"error": f"Eroare la generarea BEP: {str(e)}"}


def handle_verify_bep(db: Session, tool_input: dict) -> dict:
    """Handler pentru verify_bep."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    bep_doc = get_latest_generated_document(db, project_id, "bep")
    if not bep_doc:
        return {
            "error": (
                "Nu există BEP generat. Generează mai întâi un BEP "
                "folosind tool-ul generate_bep."
            ),
        }

    ctx_entry = get_latest_project_context(db, project_id)
    project_context = ctx_entry.context_json if ctx_entry else {}

    # Construim un model_summary minimal din context
    model_summary = {
        "disciplines_present": project_context.get("disciplines", []),
        "exchange_formats": [project_context.get("main_exchange_format", "ifc4_3")],
        "has_georeferencing": True,
        "coordinate_system": "Stereo 70",
        "source": "auto-generated from project context",
    }

    # Dacă avem IFC importat, folosim summary-ul parsat
    ifc_file = get_latest_uploaded_file(db, project_id, "ifc")
    if ifc_file and ifc_file.parsed_summary_json:
        model_summary = ifc_file.parsed_summary_json

    verification_context = {
        "project_context": project_context,
        "bep_excerpt": bep_doc.content_markdown,
        "model_summary": model_summary,
    }

    try:
        result = call_llm_bep_verifier(verification_context)

        report_md = result.get("report_markdown", "")
        checks = result.get("checks", [])
        summary = result.get("summary", {})

        doc = save_generated_document(
            db,
            project_id=project_id,
            doc_type="bep_verification_report",
            title=f"Raport verificare BEP vs Model - {project.code}",
            content_markdown=report_md,
            summary_status=summary.get("overall_status"),
            fail_count=summary.get("fail_count", 0),
            warning_count=summary.get("warning_count", 0),
        )
        on_bep_verified(db, project_id, checks)

        log_action(db, project_id, "verify_bep", {
            "document_id": doc.id,
            "overall_status": summary.get("overall_status"),
            "fail_count": summary.get("fail_count", 0),
            "warning_count": summary.get("warning_count", 0),
            "checks_count": len(checks),
        })

        return {
            "success": True,
            "message": f"Verificare completă. Status: {summary.get('overall_status', 'N/A')}.",
            "document_id": doc.id,
            "summary": summary,
            "checks_count": len(checks),
            "report_excerpt": report_md[:500] if report_md else "",
        }
    except Exception as e:
        logger.error(f"Eroare la verificare BEP: {e}")
        return {"error": f"Eroare la verificarea BEP: {str(e)}"}


def handle_export_bep_docx(db: Session, tool_input: dict) -> dict:
    """Handler pentru export_bep_docx."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    bep_doc = get_latest_generated_document(db, project_id, "bep")
    if not bep_doc:
        return {
            "error": (
                "Nu există BEP generat. Generează mai întâi un BEP "
                "folosind tool-ul generate_bep."
            ),
        }

    # Verificăm că exportul funcționează (nu salvăm, doar validăm)
    try:
        markdown_to_docx(bep_doc.content_markdown, project.code)
    except Exception as e:
        return {"error": f"Eroare la exportul DOCX: {str(e)}"}

    log_action(db, project_id, "export_bep_docx", {
        "bep_version": bep_doc.version,
    })

    download_url = f"/api/projects/{project_id}/export-bep-docx"
    return {
        "success": True,
        "message": (
            f"BEP-ul proiectului '{project.name}' ({project.code}) "
            "este gata pentru descărcare ca DOCX."
        ),
        "download_url": download_url,
        "filename": f"BEP_{project.code}.docx",
    }


def handle_update_project_context(db: Session, tool_input: dict) -> dict:
    """Handler pentru update_project_context."""
    project_id = tool_input["project_id"]
    updates = tool_input.get("updates", {})

    if not updates:
        return {"error": "Nu au fost specificate câmpuri de actualizat."}

    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ctx_entry = get_latest_project_context(db, project_id)
    if not ctx_entry:
        return {
            "error": (
                "Nu există fișă BEP. Completează mai întâi fișa proiectului "
                "din tab-ul 'Fișa BEP'."
            ),
        }

    # Merge updates into existing context
    merged = {**ctx_entry.context_json, **updates}

    try:
        new_context = ProjectContext(**merged)
        save_project_context(db, project_id, new_context)
        on_context_saved(db, project_id)

        log_action(db, project_id, "update_project_context", {
            "updated_fields": list(updates.keys()),
        })

        return {
            "success": True,
            "message": f"Fișa BEP actualizată. Câmpuri modificate: {list(updates.keys())}",
            "updated_fields": list(updates.keys()),
        }
    except Exception as e:
        logger.error(f"Eroare la actualizare context: {e}")
        return {"error": f"Eroare la actualizarea fișei: {str(e)}"}


def handle_get_verification_history(db: Session, tool_input: dict) -> dict:
    """Handler pentru get_verification_history."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    reports = list_verification_reports(db, project_id)
    if not reports:
        return {
            "message": "Nu există verificări anterioare pentru acest proiect.",
            "history": [],
        }

    history = [document_model_to_history_item(r).model_dump() for r in reports]
    return {
        "total_count": len(history),
        "history": history,
    }


def handle_search_bim_standards(db: Session, tool_input: dict) -> dict:
    """Handler pentru search_bim_standards."""
    query = tool_input.get("query", "")
    n_results = tool_input.get("n_results", 5)

    if not query.strip():
        return {"error": "Query-ul de căutare nu poate fi gol."}

    try:
        results = search_standards(query, n_results=n_results)
        return {
            "query": query,
            "results_count": len(results),
            "results": results,
        }
    except Exception as e:
        logger.warning(f"Eroare la căutare standarde: {e}")
        return {
            "message": (
                "Baza de date de standarde nu este disponibilă momentan. "
                "Voi răspunde pe baza cunoștințelor generale despre ISO 19650."
            ),
            "results": [],
        }


# ── Handleri noi (Faza 1A, 2A, 2B, 3B) ─────────────────────────────────

def handle_analyze_ifc_model(db: Session, tool_input: dict) -> dict:
    """Handler pentru analyze_ifc_model — analizează modelul IFC importat."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    ifc_file = get_latest_uploaded_file(db, project_id, "ifc")
    if not ifc_file:
        return {
            "error": (
                "Nu există model IFC importat pentru acest proiect. "
                "Utilizatorul trebuie să importe un fișier IFC din tab-ul 'Verificare BEP'."
            ),
        }

    summary = ifc_file.parsed_summary_json or {}

    # Construim analiza detaliată
    categories = summary.get("categories", [])
    disciplines = summary.get("disciplines_present", [])
    total_elements = sum(c.get("element_count", 0) for c in categories)

    # Detectăm potențiale probleme
    issues: list[str] = []
    if not summary.get("has_georeference"):
        issues.append("Modelul nu are georeferențiere definită (IfcMapConversion / IfcProjectedCRS)")
    if len(disciplines) == 0:
        issues.append("Nu s-au detectat discipline standard (arhitectură, structură, MEP)")
    if total_elements < 10:
        issues.append(f"Număr foarte mic de elemente ({total_elements}) — modelul pare incomplet")
    if len(disciplines) == 1:
        issues.append(
            f"Modelul conține doar disciplina '{disciplines[0]}' — "
            "verifică dacă sunt necesare și alte discipline"
        )

    analysis = {
        "filename": ifc_file.filename,
        "file_size_mb": round((ifc_file.file_size_bytes or 0) / (1024 * 1024), 2),
        "total_elements": total_elements,
        "disciplines_detected": disciplines,
        "categories": categories,
        "has_georeferencing": summary.get("has_georeference", False),
        "coordinate_system": summary.get("coordinate_system"),
        "exchange_format": summary.get("exchange_formats_available", []),
        "notes": summary.get("notes", ""),
        "potential_issues": issues,
        "imported_at": ifc_file.created_at.isoformat() if ifc_file.created_at else "",
    }

    log_action(db, project_id, "analyze_ifc_model", {
        "filename": ifc_file.filename,
        "total_elements": total_elements,
        "disciplines": disciplines,
    })

    return {
        "success": True,
        "message": (
            f"Analiză model IFC: {ifc_file.filename} — "
            f"{total_elements} elemente, {len(disciplines)} discipline, "
            f"{'cu' if summary.get('has_georeference') else 'fără'} georeferențiere."
        ),
        "analysis": analysis,
    }


def handle_list_document_versions(db: Session, tool_input: dict) -> dict:
    """Handler pentru list_document_versions — lista versiuni BEP."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    docs = list_bep_documents(db, project_id)
    if not docs:
        return {
            "message": "Nu există documente BEP generate pentru acest proiect.",
            "versions": [],
        }

    versions = []
    for doc in docs:
        versions.append({
            "document_id": doc.id,
            "version": doc.version or "N/A",
            "title": doc.title,
            "content_length": len(doc.content_markdown) if doc.content_markdown else 0,
            "created_at": doc.created_at.isoformat() if doc.created_at else "",
        })

    return {
        "total_count": len(versions),
        "versions": versions,
    }


def handle_compare_bep_versions(db: Session, tool_input: dict) -> dict:
    """Handler pentru compare_bep_versions — diff între versiuni BEP."""
    project_id = tool_input["project_id"]
    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    version_a_id = tool_input.get("version_a_id")
    version_b_id = tool_input.get("version_b_id")

    if version_a_id and version_b_id:
        # Versiuni specificate
        doc_a = db.get(GeneratedDocumentModel, version_a_id)
        doc_b = db.get(GeneratedDocumentModel, version_b_id)
        if not doc_a or not doc_b:
            return {"error": "Unul sau ambele documente BEP nu au fost găsite."}
    else:
        # Ultimele două versiuni
        docs = list_bep_documents(db, project_id)
        if len(docs) < 2:
            return {
                "error": (
                    "Sunt necesare cel puțin 2 versiuni BEP pentru comparare. "
                    f"Proiectul are {len(docs)} versiune(i)."
                ),
            }
        doc_b = docs[0]  # cea mai recentă
        doc_a = docs[1]  # anterioară

    diff = _diff_bep(doc_a.content_markdown, doc_b.content_markdown)

    return {
        "success": True,
        "version_a": {
            "id": doc_a.id,
            "version": doc_a.version or "N/A",
            "created_at": doc_a.created_at.isoformat() if doc_a.created_at else "",
        },
        "version_b": {
            "id": doc_b.id,
            "version": doc_b.version or "N/A",
            "created_at": doc_b.created_at.isoformat() if doc_b.created_at else "",
        },
        "diff": diff,
    }


def handle_get_audit_trail(db: Session, tool_input: dict) -> dict:
    """Handler pentru get_audit_trail — jurnal de activități."""
    project_id = tool_input["project_id"]
    limit = tool_input.get("limit", 20)

    project = get_project(db, project_id)
    if not project:
        return {"error": f"Proiectul cu ID {project_id} nu există."}

    logs = list_audit_logs(db, project_id, limit=limit)
    if not logs:
        return {
            "message": "Nu există activități înregistrate pentru acest proiect.",
            "trail": [],
        }

    trail = []
    for log_entry in logs:
        trail.append({
            "action": log_entry.action,
            "actor": log_entry.actor,
            "details": log_entry.details_json,
            "created_at": log_entry.created_at.isoformat() if log_entry.created_at else "",
        })

    return {
        "total_count": len(trail),
        "trail": trail,
    }


def handle_get_project_health_check(db: Session, tool_input: dict) -> dict:
    """Handler pentru get_project_health_check — diagnostic sănătate proiect."""
    project_id = tool_input["project_id"]
    return compute_project_health(db, project_id)


# ══════════════════════════════════════════════════════════════════════════════
# Dispatcher — execută tool-ul corect pe baza numelui
# ══════════════════════════════════════════════════════════════════════════════

TOOL_HANDLERS: dict[str, Any] = {
    "get_project_info": handle_get_project_info,
    "get_project_context": handle_get_project_context,
    "generate_bep": handle_generate_bep,
    "verify_bep": handle_verify_bep,
    "export_bep_docx": handle_export_bep_docx,
    "update_project_context": handle_update_project_context,
    "get_verification_history": handle_get_verification_history,
    "search_bim_standards": handle_search_bim_standards,
    "analyze_ifc_model": handle_analyze_ifc_model,
    "list_document_versions": handle_list_document_versions,
    "compare_bep_versions": handle_compare_bep_versions,
    "get_audit_trail": handle_get_audit_trail,
    "get_project_health_check": handle_get_project_health_check,
}


def execute_tool(db: Session, tool_name: str, tool_input: dict) -> dict:
    """
    Execută un tool și returnează rezultatul ca dict.

    Args:
        db: Sesiune SQLAlchemy
        tool_name: Numele tool-ului de executat
        tool_input: Parametrii tool-ului

    Returns:
        dict cu rezultatul execuției
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Tool necunoscut: {tool_name}"}

    start = time.time()
    try:
        result = handler(db, tool_input)
        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            f"Tool '{tool_name}' executat în {duration_ms}ms"
        )
        return result
    except Exception as e:
        logger.error(f"Eroare la execuția tool-ului '{tool_name}': {e}")
        return {"error": f"Eroare internă la execuția tool-ului: {str(e)}"}
