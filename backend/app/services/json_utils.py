"""
json_utils.py — Utilitar comun pentru extragerea JSON din răspunsuri LLM.
"""

import json
import re
import logging

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """
    Extrage JSON dintr-un răspuns LLM, gestionând:
    - Markdown code fences (```json ... ``` sau ```json ... fără închidere)
    - Text înainte/după JSON
    - JSON cu trailing commas
    - Fallback la raw_response dacă nimic nu merge
    """
    text = text.strip()

    # 1. Elimină code fences (cu sau fără closing ```)
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    elif text.startswith("```"):
        # Code fence fără closing — elimină prima linie și orice ``` de la final
        lines = text.split("\n")
        # Skip prima linie (```json)
        lines = lines[1:]
        # Elimină ultimul ``` dacă există
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 2. Încearcă parsare directă
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Extrage primul { ... ultimul }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # 4. Elimină trailing commas (pattern comun la LLM-uri)
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

    # 5. Încearcă array [...] dacă nu e obiect
    start_arr = text.find("[")
    end_arr = text.rfind("]")
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        candidate = text[start_arr:end_arr + 1]
        try:
            arr = json.loads(candidate)
            return {"items": arr}
        except json.JSONDecodeError:
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                arr = json.loads(cleaned)
                return {"items": arr}
            except json.JSONDecodeError:
                pass

    logger.warning("Nu s-a putut parsa JSON din răspunsul LLM, returnez raw_response")
    return {"raw_response": text}
