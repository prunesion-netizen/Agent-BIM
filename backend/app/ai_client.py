"""
ai_client.py — Interfața cu Claude API (Anthropic).
Funcții pentru generare BEP, Chat Expert BIM și Verificare BEP vs Model.
"""

import os
import json
import logging
import re

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Client singleton ──────────────────────────────────────────────────────────
_client = None

def _get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY nu este setat in variabilele de mediu.")
        _client = Anthropic(api_key=api_key)
    return _client


MODEL = "claude-sonnet-4-6"


# ── System prompts ────────────────────────────────────────────────────────────

SYSTEM_PROMPT_BEP_MANAGER = (
    "Ești un BIM Manager senior și consultant în managementul informațiilor "
    "conform SR EN ISO 19650-1/2/3.\n\n"
    "Primești:\n"
    "- un obiect JSON numit project_context, cu toate datele relevante despre proiect;\n\n"
    "Scop:\n"
    "Generezi un BIM Execution Plan (BEP) complet, în limba română, adaptat "
    "proiectului din project_context, respectând structura și principiile ISO 19650-2.\n\n"
    "Reguli:\n"
    "- Folosește toate valorile din project_context exact cum sunt.\n"
    "- Nu inventa standarde sau cerințe care nu există.\n"
    "- Adaptează limbajul și exemplele la tipul de proiect (clădire, spital, depozit de deșeuri etc.).\n"
    "- BEP-ul trebuie să includă capitolele:\n"
    "  1. Informații generale\n"
    "  2. Obiective BIM, OIR, AIR, PIR\n"
    "  3. Echipa BIM (roluri, responsabilități, RACI la nivel de principiu)\n"
    "  4. CDE (platformă, structură foldere, flux WIP/Shared/Published/Archived, naming)\n"
    "  5. Standarde și protocoale BIM\n"
    "  6. Software și platforme\n"
    "  7. Nivele de detaliu LOD/LOI (explicații + matrice orientativă)\n"
    "  8. Livrabile BIM și calendar (livrabil vs jalon)\n"
    "  9. Coordonare BIM și clash detection\n"
    "  10. Documentație As-Built și predare\n"
    "  11. Managementul calității BIM (verificări, KPI, audituri)\n"
    "  12. Plan de implementare BIM pe faze\n"
    "  13. Aprobări și istoricul reviziilor.\n\n"
    "- Daca lipsesc informatii, scrie clar 'de completat de beneficiar' sau 'de stabilit la kick-off'.\n"
    "- Fii clar și profesionist; evită repetițiile inutile.\n\n"
    "Output:\n"
    "- întoarce BEP-ul în format Markdown structurat (titluri, subcapitole, tabele), "
    "pentru a fi convertit în DOCX/PDF."
)

SYSTEM_PROMPT_CHAT_EXPERT = (
    "Esti 'Expert BIM Romania', un specialist BIM si in managementul informatiilor "
    "conform ISO 19650. Răspunzi la întrebări în limba română, pe baza contextului "
    "primit (BEP-ul proiectului, EIR, standarde BIM și proceduri interne).\n\n"
    "Reguli:\n"
    "- Dacă răspunsul este clar din context, citează pe scurt secțiunea relevantă în cuvintele tale.\n"
    "- Dacă ceva nu este specificat în context, explică bune practici generale ISO 19650 și BIM.\n"
    "- Răspunde concis, structurat, cu bullet points unde are sens.\n"
    "- Nu inventa cerințe contractuale care nu există; precizează când răspunsul este o recomandare generală."
)

SYSTEM_PROMPT_BEP_VERIFIER = """\
Ești un auditor BIM și specialist în controlul calității modelelor conform SR EN ISO 19650.

Primești:
- project_context: date structurale despre un proiect (tipul proiectului, discipline, CDE, \
livrabile și cerințe BIM),
- bep_excerpt: fragmente din BIM Execution Plan (BEP) al proiectului,
- model_summary: un rezumat tehnic al modelului BIM actual (discipline prezente, categorii \
de elemente, georeferențiere, formate de schimb etc.).

Scop:
- Compari ce este specificat în BEP cu starea modelului descrisă în model_summary.
- Identifici neconformități, riscuri sau lipsuri, la nivel de principii \
(nu faci verificare geometrică detaliată).

Reguli:
- Verifică în special:
  - dacă disciplinele din model acoperă disciplinele cerute în BEP;
  - dacă formatele de schimb (IFC/NWD etc.) sunt disponibile așa cum BEP pretinde;
  - dacă există georeferențiere și sistem de coordonate, când BEP o cere;
  - dacă există cel puțin un indiciu că LOD/LOI sunt abordate \
(dacă model_summary conține astfel de info);
  - orice altă diferență evidentă între ce promite BEP și ce avem în model_summary.
- Clasifică fiecare verificare ca:
  - "pass" (conform),
  - "warning" (posibilă problemă sau informație lipsă),
  - "fail" (neconformitate clară).
- Dacă anumite informații nu se regăsesc în model_summary, marchează verificarea \
ca "warning" și explică ce ar trebui verificat manual.
- Fii specific în explicații, dar concis. Adresează-te utilizatorilor tehnici BIM români.

Output:
- Întoarce răspunsul STRICT ca JSON valid (fără text înainte sau după), cu structura:
{
  "report_markdown": "... raport Markdown structurat pe secțiuni: Rezumat, Verificări cheie, Recomandări ...",
  "checks": [
    {
      "id": "string scurt unic (ex: discipline_coverage)",
      "label": "Titlu scurt al verificării",
      "status": "pass | warning | fail",
      "details": "Explicație concisă a rezultatului"
    }
  ],
  "summary": {
    "total_checks": <int>,
    "pass_count": <int>,
    "warning_count": <int>,
    "fail_count": <int>,
    "overall_status": "pass | warning | fail"
  }
}

- report_markdown: un raport narativ Markdown cu secțiunile Rezumat, Verificări cheie, Recomandări.
- checks: lista de verificări individuale, fiecare cu id, label, status și details.
- summary: totaluri și status general (fail dacă orice check e fail, \
warning dacă orice check e warning, pass doar dacă totul e pass)."""


# ── Funcții LLM ───────────────────────────────────────────────────────────────

def call_llm(project_context: dict) -> str:
    """
    Apelează Claude pentru a genera un BEP complet în Markdown.
    Primește project_context ca dict, returnează string Markdown.
    """
    client = _get_client()

    user_message = (
        "Generează un BEP complet pentru acest proiect.\n\n"
        "```json\n"
        f"{json.dumps(project_context, ensure_ascii=False, indent=2)}\n"
        "```"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT_BEP_MANAGER,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Eroare la apelul Claude pentru BEP: {e}")
        raise RuntimeError(f"Eroare generare BEP: {e}") from e


def call_llm_chat_expert(context: str, question: str) -> str:
    """
    Apelează Claude pentru Chat Expert BIM.
    Primește context (BEP + standarde) și întrebarea utilizatorului.
    Returnează răspunsul AI.
    """
    client = _get_client()

    system_with_context = (
        SYSTEM_PROMPT_CHAT_EXPERT
        + "\n\n--- CONTEXT ---\n\n"
        + context
        + "\n\n--- SFÂRȘIT CONTEXT ---"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system_with_context,
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Eroare la apelul Claude pentru Chat Expert: {e}")
        raise RuntimeError(f"Eroare Chat Expert: {e}") from e


def call_llm_bep_verifier(verification_context: dict) -> dict:
    """
    Apelează Claude pentru verificarea conformității BEP vs Model BIM.

    Args:
        verification_context: dict cu cheile:
            - project_context: dict (fișa BEP 2.0)
            - bep_excerpt: str (BEP-ul sau părți relevante)
            - model_summary: dict (rezumat model Revit/IFC)

    Returns:
        dict cu cheile: report_markdown, checks, summary
    """
    client = _get_client()

    user_message = (
        "Verifică conformitatea BEP vs model pentru acest context.\n\n"
        "```json\n"
        f"{json.dumps(verification_context, ensure_ascii=False, indent=2)}\n"
        "```"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            system=SYSTEM_PROMPT_BEP_VERIFIER,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text.strip()
        stop_reason = response.stop_reason

        result = _extract_verifier_json(raw, stop_reason)

        # Validare minimală a structurii
        if "report_markdown" not in result:
            result["report_markdown"] = ""
        if "checks" not in result:
            result["checks"] = []
        if "summary" not in result:
            result["summary"] = _build_summary(result["checks"])

        return result

    except Exception as e:
        logger.error(f"Eroare la apelul Claude pentru BEP Verifier: {e}")
        raise RuntimeError(f"Eroare verificare BEP: {e}") from e


def _extract_verifier_json(raw: str, stop_reason: str | None = None) -> dict:
    """Extrage JSON din răspunsul LLM, gestionând code fences și JSON trunchiat."""

    # 1) Elimină code fence dacă există (oriunde în text)
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1).strip()

    # 2) Extrage primul obiect JSON {...} din text
    start = raw.find("{")
    if start == -1:
        raise json.JSONDecodeError("Nu s-a găsit JSON în răspuns", raw, 0)
    raw = raw[start:]

    # 3) Încearcă parsare directă
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 4) JSON trunchiat (max_tokens atins) — repară
    if stop_reason == "max_tokens" or not raw.rstrip().endswith("}"):
        logger.warning("JSON trunchiat detectat — se încearcă repararea")
        return _repair_truncated_json(raw)

    # 5) Ultima încercare — curăță trailing text după ultimul }
    last_brace = raw.rfind("}")
    if last_brace != -1:
        try:
            return json.loads(raw[: last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("Nu s-a putut parsa JSON din răspuns", raw[:200], 0)


def _repair_truncated_json(raw: str) -> dict:
    """Repară JSON trunchiat extragând checks și report_markdown parțial."""
    result: dict = {}

    # Extrage checks[] (array complet sau parțial)
    checks_match = re.search(
        r'"checks"\s*:\s*\[',
        raw,
    )
    if checks_match:
        arr_start = checks_match.end() - 1  # include '['
        # Găsește sfârșitul array-ului sau repară-l
        depth = 0
        last_valid = arr_start
        for i in range(arr_start, len(raw)):
            if raw[i] == "[":
                depth += 1
            elif raw[i] == "]":
                depth -= 1
                if depth == 0:
                    last_valid = i + 1
                    break
            elif raw[i] == "}" and depth == 1:
                last_valid = i + 1  # ultimul obiect complet din array

        arr_str = raw[arr_start:last_valid]
        if not arr_str.rstrip().endswith("]"):
            # Taie ultimul obiect incomplet și închide array-ul
            last_complete = arr_str.rfind("}")
            if last_complete != -1:
                arr_str = arr_str[: last_complete + 1] + "]"
            else:
                arr_str = "[]"

        try:
            result["checks"] = json.loads(arr_str)
        except json.JSONDecodeError:
            result["checks"] = []

    # Extrage report_markdown (string trunchiat)
    report_match = re.search(r'"report_markdown"\s*:\s*"', raw)
    if report_match:
        str_start = report_match.end()
        # Parcurge string-ul JSON respectând escape-uri
        i = str_start
        chars = []
        while i < len(raw):
            if raw[i] == "\\" and i + 1 < len(raw):
                chars.append(raw[i : i + 2])
                i += 2
            elif raw[i] == '"':
                break
            else:
                chars.append(raw[i])
                i += 1
        md_raw = "".join(chars)
        # Decodează escape-urile JSON
        try:
            result["report_markdown"] = json.loads(f'"{md_raw}"')
        except json.JSONDecodeError:
            result["report_markdown"] = md_raw.replace("\\n", "\n").replace('\\"', '"')

    # Extrage summary dacă există complet
    summary_match = re.search(r'"summary"\s*:\s*\{', raw)
    if summary_match:
        brace_start = summary_match.end() - 1
        depth = 0
        for i in range(brace_start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        result["summary"] = json.loads(raw[brace_start : i + 1])
                    except json.JSONDecodeError:
                        pass
                    break

    if not result:
        raise json.JSONDecodeError("Nu s-a putut recupera nimic din JSON trunchiat", raw[:200], 0)

    return result


def _build_summary(checks: list[dict]) -> dict:
    """Construiește summary din lista de checks."""
    total = len(checks)
    pass_count = sum(1 for c in checks if c.get("status") == "pass")
    warning_count = sum(1 for c in checks if c.get("status") == "warning")
    fail_count = sum(1 for c in checks if c.get("status") == "fail")
    if fail_count > 0:
        overall = "fail"
    elif warning_count > 0:
        overall = "warning"
    else:
        overall = "pass"
    return {
        "total_checks": total,
        "pass_count": pass_count,
        "warning_count": warning_count,
        "fail_count": fail_count,
        "overall_status": overall,
    }
