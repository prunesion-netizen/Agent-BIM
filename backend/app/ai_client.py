"""
ai_client.py — Interfața cu Claude API (Anthropic).
Funcții pentru generare BEP și Chat Expert BIM.
"""

import os
import json
import logging

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
