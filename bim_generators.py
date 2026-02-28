"""
bim_generators.py — Generatoare documente BIM pentru orice proiect
Foloseste RAG + Claude AI pentru a genera documente profesionale DOCX.

Utilizare din Flask:
    from bim_generators import generate_document
    path = generate_document("bep", "Ghizela")
"""

import os
import re
import datetime
import threading
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────
GENERATED_DIR = Path("generated")
GENERATED_DIR.mkdir(exist_ok=True)

AI_MODEL     = "claude-sonnet-4-6"
BLUE_DARK    = RGBColor(0x1D, 0x4E, 0xD8)
GRAY_TEXT    = RGBColor(0x37, 0x41, 0x51)
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)

_ai_client = None
def get_ai():
    global _ai_client
    if _ai_client is None:
        _ai_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _ai_client

# ── RAG helper ─────────────────────────────────────────────────────────────────
try:
    from bim_rag import query_rag as _query_rag
    _RAG_OK = True
except Exception:
    _RAG_OK = False
    def _query_rag(q, n=5):
        return {"context": "", "sources": [], "rag_used": False}


def get_project_context(project: str, queries: list, n: int = 5) -> str:
    """Extrage context RAG pentru un proiect și o lista de interogari."""
    parts = []
    for q in queries:
        full_q = f"{q} {project}" if project else q
        r = _query_rag(full_q, n=n)
        if r.get("rag_used") and r.get("context"):
            parts.append(r["context"])
    return "\n\n---\n\n".join(parts)


def ask_claude(system: str, user: str, max_tokens: int = 3000) -> str:
    resp = get_ai().messages.create(
        model=AI_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


# ── DOCX Helpers ───────────────────────────────────────────────────────────────
def _shd(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _setup_doc(title: str, project: str) -> Document:
    doc = Document()
    for sec in doc.sections:
        sec.top_margin    = Cm(2.0)
        sec.bottom_margin = Cm(2.0)
        sec.left_margin   = Cm(2.5)
        sec.right_margin  = Cm(2.0)
    # Cover header
    p = doc.add_paragraph()
    r = p.add_run("━" * 55)
    r.font.color.rgb = BLUE_DARK
    r.font.size = Pt(12)

    p2 = doc.add_paragraph()
    r2 = p2.add_run(title)
    r2.font.size = Pt(20)
    r2.font.bold = True
    r2.font.color.rgb = BLUE_DARK

    if project:
        p3 = doc.add_paragraph()
        r3 = p3.add_run(f"Proiect: {project}")
        r3.font.size = Pt(13)
        r3.font.color.rgb = GRAY_TEXT

    p4 = doc.add_paragraph()
    r4 = p4.add_run(f"Generat: {datetime.date.today().strftime('%d.%m.%Y')} · Agent BIM Romania")
    r4.font.size = Pt(9)
    r4.font.italic = True
    r4.font.color.rgb = GRAY_TEXT
    doc.add_paragraph()
    return doc


def _add_h1(doc, text):
    p = doc.add_heading(text, level=1)
    if p.runs:
        p.runs[0].font.color.rgb = BLUE_DARK
        p.runs[0].font.size = Pt(15)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)


def _add_h2(doc, text):
    p = doc.add_heading(text, level=2)
    if p.runs:
        p.runs[0].font.color.rgb = GRAY_TEXT
        p.runs[0].font.size = Pt(12)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(3)


def _add_body(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(10)
    r.font.color.rgb = GRAY_TEXT
    p.paragraph_format.space_after = Pt(4)
    return p


def _add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    r.font.size = Pt(10)
    r.font.color.rgb = GRAY_TEXT
    return p


def _add_table(doc, headers: list, rows: list):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    # Header row
    hr = t.rows[0]
    for j, h in enumerate(headers):
        _shd(hr.cells[j], "1D4ED8")
        p = hr.cells[j].paragraphs[0]
        r = p.add_run(str(h))
        r.font.bold  = True
        r.font.size  = Pt(9)
        r.font.color.rgb = WHITE
        p.alignment  = WD_ALIGN_PARAGRAPH.CENTER
    # Data rows
    for i, row in enumerate(rows):
        dr = t.rows[i + 1]
        bg = "F0F9FF" if i % 2 == 0 else "FFFFFF"
        for j, cell in enumerate(row):
            _shd(dr.cells[j], bg)
            p = dr.cells[j].paragraphs[0]
            r = p.add_run(str(cell))
            r.font.size = Pt(8.5)
            r.font.color.rgb = GRAY_TEXT
            if j == 0:
                r.font.bold = True
    doc.add_paragraph()


def _md_to_doc(doc, text: str):
    """Conversie Markdown simplu → paragrafele DOCX (heading, bullet, body)."""
    lines = text.split("\n")
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("### "):
            _add_h2(doc, line[4:])
        elif line.startswith("## "):
            _add_h1(doc, line[3:])
        elif line.startswith("# "):
            _add_h1(doc, line[2:])
        elif re.match(r"^[-*•]\s+", line):
            _add_bullet(doc, re.sub(r"^[-*•]\s+", "", line))
        elif re.match(r"^\d+\.\s+", line):
            _add_bullet(doc, re.sub(r"^\d+\.\s+", "", line))
        else:
            _add_body(doc, line)


# ══════════════════════════════════════════════════════════════════════════════
# GENERATOARE
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_BIM = (
    "Ești expert BIM senior în România, specializat în ISO 19650, BEP, EIR, LOD, CDE. "
    "Generezi documente profesionale, complete, în română. "
    "Folosești datele din context când există; altfel folosești standardele internaționale. "
    "Formatul răspunsului: Markdown cu ## pentru capitole, ### pentru subcapitole, - pentru liste."
)


def gen_bep(project: str) -> str:
    """Generează BIM Execution Plan. Returnează calea fișierului."""
    ctx = get_project_context(project, [
        "obiectul contractului beneficiar proiectant",
        "cerinte BIM modelare software livrabile",
        "Common Data Environment CDE platforma",
        "LOD nivel detaliu faze proiect",
        "standarde ISO 19650 BIM",
        "echipa BIM manager coordinator responsabilitati",
    ])

    prompt = f"""Genereaza un BEP (BIM Execution Plan) complet pentru proiectul: **{project}**

Context din documentele proiectului:
{ctx or "Nu exista context specific – foloseste standarde generale BIM si ISO 19650."}

Include TOATE sectiunile standard:
## 1. Informatii generale proiect
## 2. Obiectivele BIM (OIR / AIR / PIR)
## 3. Echipa BIM – Roluri si Responsabilitati (RACI)
## 4. Mediul Comun de Date (CDE)
## 5. Standarde, Software si Formate
## 6. Nivelele de Detaliu (LOD 100-400) pe faze
## 7. Livrabile BIM si Calendar
## 8. Coordonare si Clash Detection
## 9. Documentatie As-Built si Predare
## 10. Managementul Calitatii BIM
## 11. Aprobari si Istoricul Reviziilor

Fii detaliat, profesional. Minim 800 cuvinte."""

    content = ask_claude(SYSTEM_BIM, prompt, max_tokens=4000)

    doc = _setup_doc("PLAN DE EXECUȚIE BIM (BEP)", project)
    _md_to_doc(doc, content)

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe = re.sub(r"[^\w]", "_", project)[:30]
    out  = GENERATED_DIR / f"BEP_{safe}_{ts}.docx"
    doc.save(str(out))
    return str(out)


def gen_lod(project: str) -> str:
    """Generează Matrice LOD. Returnează calea fișierului."""
    ctx = get_project_context(project, [
        "faze proiect PT DDE executie receptie",
        "elemente BIM structuri instalatii arhitectura",
        "LOD nivel detaliu livrabile",
    ])

    prompt = f"""Genereaza o Matrice LOD completa pentru proiectul: **{project}**

Context:
{ctx or "Proiect de constructii – foloseste matrice LOD standard."}

## 1. Introducere – Ce este LOD
## 2. Definitii LOD (100 / 200 / 300 / 350 / 400)
## 3. Matrice LOD pe elemente si faze
(descrie textual: Element | PT | DDE | Executie | As-Built | Note)
## 4. Responsabilitati LOD pe rol
## 5. Verificare si validare LOD

Fii specific. Include minimum 15 tipuri de elemente BIM relevante pentru proiect."""

    content = ask_claude(SYSTEM_BIM, prompt, max_tokens=3000)

    doc = _setup_doc("MATRICE LOD / LOI", project)
    _md_to_doc(doc, content)

    # Adauga tabelul LOD standard
    _add_h1(doc, "Tabel de referință LOD")
    _add_table(doc,
        ["LOD", "Denumire", "Precizie geometrie", "Informații incluse"],
        [
            ["100", "Concept",     "Simbolic / volum",          "Suprafețe, volume, orientare aproximativă"],
            ["200", "Schematic",   "Generalizată",               "Dimensiuni generale, materiale principale"],
            ["300", "Definit",     "Specifică, cotată",          "Dimensiuni exacte, specificații materiale"],
            ["350", "Coordonare",  "LOD 300 + interfețe",        "Toate interfețele cu alte disciplini definite"],
            ["400", "Fabricare",   "Exactă (As-Built)",          "Toate detaliile, starea reală din teren"],
        ]
    )

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe = re.sub(r"[^\w]", "_", project)[:30]
    out  = GENERATED_DIR / f"LOD_{safe}_{ts}.docx"
    doc.save(str(out))
    return str(out)


def gen_eir(project: str) -> str:
    """Generează Employer's Information Requirements. Returnează calea fișierului."""
    ctx = get_project_context(project, [
        "beneficiar cerinte informatii proiect",
        "obiective BIM client investitor",
        "standarde ISO 19650 EIR cerinte",
        "livrabile predare documentatie",
    ])

    prompt = f"""Genereaza un EIR (Employer's Information Requirements) complet pentru proiectul: **{project}**

Context:
{ctx or "Proiect de constructii – EIR conform ISO 19650-2."}

## 1. Scopul EIR
## 2. Obiectivele BIM ale Beneficiarului
## 3. Cerinte de informatii organizationale (OIR)
## 4. Cerinte de informatii pentru activul construit (AIR)
## 5. Cerinte tehnice (software, formate, standarde)
## 6. Cerinte de management (CDE, procese, echipa)
## 7. Cerinte comerciale (termene, penalitati, livrabile)
## 8. Criterii de acceptanta
## 9. Anexe – Template-uri solicitate

Conform ISO 19650-2. Profesional, detaliat."""

    content = ask_claude(SYSTEM_BIM, prompt, max_tokens=3500)

    doc = _setup_doc("CERINȚE DE INFORMAȚII ALE BENEFICIARULUI (EIR)", project)
    _md_to_doc(doc, content)

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe = re.sub(r"[^\w]", "_", project)[:30]
    out  = GENERATED_DIR / f"EIR_{safe}_{ts}.docx"
    doc.save(str(out))
    return str(out)


def gen_requirements(project: str) -> str:
    """Extrage cerințe BIM din documentele proiectului. Returnează calea fișierului."""
    queries_map = {
        "Cerinte BIM generale":     "cerinte BIM modelare digitala proiect",
        "Software si platforme":    "software BIM Autodesk Revit IFC formate fisiere",
        "Livrabile BIM":            "livrabile BIM modele faze proiect predare",
        "Echipa BIM":               "BIM manager coordinator responsabilitati echipa",
        "CDE":                      "Common Data Environment CDE management informatii",
        "LOD":                      "LOD nivel detaliu modele BIM",
        "As-Built":                 "As-Built documentatie finala predare beneficiar",
        "Standarde":                "standarde BIM ISO 19650 aplicabile proiect",
        "Coordonare":               "coordonare interferente clash detection modele",
        "Obiectul contractului":    "obiectul contractului lucrari constructii",
    }

    doc = _setup_doc(f"EXTRAGERE CERINȚE BIM", project)
    _add_body(doc,
        f"Cerințe BIM extrase automat din documentele proiectului '{project}' "
        f"folosind căutare semantică (RAG) în baza de cunoștințe BIM."
    )

    found_any = False
    all_frags = []

    for topic, query in queries_map.items():
        full_q = f"{query} {project}" if project else query
        r = _query_rag(full_q, n=5)
        if not r.get("rag_used") or not r.get("context"):
            continue

        docs_list  = []
        metas_list = []
        for src in r.get("sources", []):
            if project.lower() in src.get("source", "").lower() or not project:
                metas_list.append(src)

        if not metas_list:
            metas_list = r.get("sources", [])

        if metas_list:
            found_any = True
            _add_h2(doc, topic)
            for src in metas_list[:3]:
                title = src.get("title", src.get("source", ""))
                page  = src.get("page", "-")
                rel   = src.get("relevance", 0)
                _add_body(doc, f"📄 {title} | Pag. {page} | Relevanță: {rel:.2f}")

            frags = r["context"].split("---")
            for frag in frags[:3]:
                frag = frag.strip()
                if len(frag) > 50:
                    _add_body(doc, frag[:600] + ("…" if len(frag) > 600 else ""))
                    all_frags.append(frag[:400])

    if not found_any:
        _add_body(doc,
            "Nu s-au găsit documente specifice acestui proiect în baza de date. "
            "Verificați că documentele au fost indexate cu bim_ingest.py."
        )
    else:
        # Rezumat generat de AI
        doc.add_page_break()
        _add_h1(doc, "Analiză și Concluzii")
        combined = "\n\n".join(all_frags[:15])
        summary = ask_claude(
            "Ești expert BIM în România. Analizezi documente de proiect.",
            f"Pe baza fragmentelor de mai jos din documentele proiectului '{project}', "
            f"rezumă cerințele BIM identificate și recomandă ce lipsește:\n\n{combined}",
            max_tokens=1500,
        )
        _md_to_doc(doc, summary)

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe = re.sub(r"[^\w]", "_", project)[:30]
    out  = GENERATED_DIR / f"CERINTE_{safe}_{ts}.docx"
    doc.save(str(out))
    return str(out)


def gen_checklist(project: str) -> str:
    """Generează Checklist Coordonare BIM. Returnează calea fișierului."""
    ctx = get_project_context(project, [
        "coordonare BIM clash detection interferente",
        "verificare calitate modele BIM",
        "sedinte BIM coordonare",
    ])

    prompt = f"""Genereaza un checklist detaliat de Coordonare BIM pentru proiectul: **{project}**

Context:
{ctx or "Proiect de constructii – checklist standard de coordonare BIM."}

## 1. Checklist Pre-Modelare (inainte de start)
## 2. Checklist Calitate Model (per disciplina)
## 3. Checklist Coordonare (federare modele, clash detection)
## 4. Checklist Sedinta BIM (agenda, minute)
## 5. Checklist Publicare in CDE
## 6. Checklist Receptie Model As-Built

Formatul fiecarui item: - [ ] Descriere actiune (Responsabil: X | Termen: Y)
Minim 50 de itemi total."""

    content = ask_claude(SYSTEM_BIM, prompt, max_tokens=3000)

    doc = _setup_doc("CHECKLIST COORDONARE BIM", project)
    _md_to_doc(doc, content)

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe = re.sub(r"[^\w]", "_", project)[:30]
    out  = GENERATED_DIR / f"CHECKLIST_{safe}_{ts}.docx"
    doc.save(str(out))
    return str(out)


def gen_minutes(project: str) -> str:
    """Generează template Minuta Ședință BIM. Returnează calea fișierului."""
    today = datetime.date.today().strftime("%d.%m.%Y")
    doc = _setup_doc("MINUTA ȘEDINȚĂ BIM", project)

    _add_h1(doc, "Date ședință")
    _add_table(doc, ["Câmp", "Valoare"], [
        ["Proiect",       project],
        ["Data",          today],
        ["Ora",           "________"],
        ["Locație / Link","________"],
        ["Moderator",     "BIM Manager – ________________"],
        ["Secretar",      "________________"],
        ["Nr. ședință",   "BIM-MTG-____"],
    ])

    _add_h1(doc, "Participanți")
    _add_table(doc,
        ["Nume", "Organizație", "Rol BIM", "Prezent"],
        [
            ["________________", "________________", "BIM Manager",      "□ Da  □ Nu"],
            ["________________", "________________", "BIM Coordinator",  "□ Da  □ Nu"],
            ["________________", "________________", "BIM Author Civil",  "□ Da  □ Nu"],
            ["________________", "________________", "Contractor BIM",    "□ Da  □ Nu"],
            ["________________", "________________", "Reprezentant Client","□ Da  □ Nu"],
            ["________________", "________________", "________________",  "□ Da  □ Nu"],
        ]
    )

    _add_h1(doc, "Agenda")
    _add_table(doc,
        ["Nr.", "Subiect", "Responsabil", "Durată"],
        [
            ["1", "Deschidere – prezenta si aprobarea agendei", "Moderator", "5 min"],
            ["2", "Revizie actiuni din sedinta anterioara",      "Moderator", "10 min"],
            ["3", "Status modele BIM – prezentare disciplini",   "BIM Coordinators", "15 min"],
            ["4", "Clash detection – probleme noi si rezolvate", "BIM Manager", "20 min"],
            ["5", "Coordonare RFI-uri deschise",                 "Contractor BIM", "10 min"],
            ["6", "Diverse",                                     "Toti", "5 min"],
            ["7", "Actiuni urmatoare si data urmatoarei sedinte","Moderator", "5 min"],
        ]
    )

    _add_h1(doc, "Discuții și Decizii")
    for i in range(1, 8):
        _add_h2(doc, f"Punctul {i} agenda")
        _add_body(doc, "________________________________________________________________________")
        _add_body(doc, "________________________________________________________________________")

    _add_h1(doc, "Plan de Acțiuni")
    _add_table(doc,
        ["#", "Acțiune", "Responsabil", "Termen", "Status"],
        [
            [str(i), "________________________________", "__________", "__________", "□ Deschis"]
            for i in range(1, 8)
        ]
    )

    _add_h1(doc, "Aprobare Minută")
    _add_table(doc, ["Rol", "Nume", "Semnătură", "Data"], [
        ["Moderator / BIM Manager", "________________", "________________", "________________"],
        ["Reprezentant Client",     "________________", "________________", "________________"],
    ])

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe = re.sub(r"[^\w]", "_", project)[:30]
    out  = GENERATED_DIR / f"MINUTA_{safe}_{ts}.docx"
    doc.save(str(out))
    return str(out)


def gen_iso_analysis(project: str) -> str:
    """Analiză conformitate ISO 19650. Returnează calea fișierului."""
    ctx = get_project_context(project, [
        "ISO 19650 cerinte standarde BIM",
        "OIR AIR PIR cerinte informatii",
        "CDE BEP EIR procese BIM",
    ])

    prompt = f"""Analizeaza conformitatea proiectului **{project}** cu SR EN ISO 19650.

Context din documentele proiectului:
{ctx or "Nu exista context specific."}

## 1. Rezumat conformitate (scor estimat pe 10 puncte)
## 2. ISO 19650-1 – Concepte si principii – Status
## 3. ISO 19650-2 – Faza de livrare – Status
   ### 3.1 Cerinte EIR – conformitate
   ### 3.2 BEP – conformitate
   ### 3.3 CDE – conformitate
   ### 3.4 Livrabile – conformitate
## 4. Lacune identificate (ce lipseste)
## 5. Recomandari prioritare (top 5 actiuni)
## 6. Roadmap conformitate ISO 19650

Fii critic si constructiv. Identifica lacunele reale."""

    content = ask_claude(SYSTEM_BIM, prompt, max_tokens=3000)

    doc = _setup_doc("ANALIZĂ CONFORMITATE ISO 19650", project)
    _md_to_doc(doc, content)

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe = re.sub(r"[^\w]", "_", project)[:30]
    out  = GENERATED_DIR / f"ISO19650_{safe}_{ts}.docx"
    doc.save(str(out))
    return str(out)


# ── Job management (pentru generare async) ────────────────────────────────────
_jobs: dict = {}
_jobs_lock = threading.Lock()

GENERATORS = {
    "bep":          gen_bep,
    "lod":          gen_lod,
    "eir":          gen_eir,
    "requirements": gen_requirements,
    "checklist":    gen_checklist,
    "minutes":      gen_minutes,
    "iso":          gen_iso_analysis,
}

DOC_LABELS = {
    "bep":          "Plan de Execuție BIM (BEP)",
    "lod":          "Matrice LOD / LOI",
    "eir":          "Cerințe Beneficiar (EIR)",
    "requirements": "Extragere Cerințe BIM",
    "checklist":    "Checklist Coordonare",
    "minutes":      "Minută Ședință BIM",
    "iso":          "Analiză Conformitate ISO 19650",
}


def start_generation(doc_type: str, project: str) -> str:
    """Porneste generarea asincron. Returneaza job_id."""
    import uuid
    job_id = str(uuid.uuid4())[:8]
    with _jobs_lock:
        _jobs[job_id] = {"status": "running", "file": None, "error": None}

    def _run():
        try:
            fn = GENERATORS[doc_type]
            path = fn(project)
            with _jobs_lock:
                _jobs[job_id]["status"] = "done"
                _jobs[job_id]["file"]   = Path(path).name
        except Exception as e:
            with _jobs_lock:
                _jobs[job_id]["status"] = "error"
                _jobs[job_id]["error"]  = str(e)

    threading.Thread(target=_run, daemon=True).start()
    return job_id


def get_job_status(job_id: str) -> dict:
    with _jobs_lock:
        return dict(_jobs.get(job_id, {"status": "not_found"}))


def list_generated_files() -> list:
    """Lista fisierelor generate, sortate dupa data (cele mai noi primele)."""
    files = []
    for f in sorted(GENERATED_DIR.glob("*.docx"), key=lambda x: x.stat().st_mtime, reverse=True):
        files.append({
            "name":     f.name,
            "size_kb":  round(f.stat().st_size / 1024, 1),
            "modified": datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%d.%m.%Y %H:%M"),
        })
    return files
