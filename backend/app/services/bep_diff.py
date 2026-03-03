"""
bep_diff.py — Comparare între versiuni BEP pe secțiuni Markdown.

Parsează Markdown-ul pe secțiuni (## heading), compară și raportează
secțiunile adăugate, șterse și modificate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SectionDiff:
    """Diferența dintre două versiuni BEP."""
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    modified: list[dict] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)


def _parse_sections(markdown: str) -> dict[str, str]:
    """
    Parsează Markdown pe secțiuni delimitate de headings (## ...).

    Returns:
        Dict {heading_title: section_content}
    """
    sections: dict[str, str] = {}
    current_heading = "_intro"
    current_lines: list[str] = []

    for line in markdown.splitlines():
        match = re.match(r"^##\s+(.+)$", line.strip())
        if match:
            # Salvează secțiunea anterioară
            content = "\n".join(current_lines).strip()
            if content:
                sections[current_heading] = content
            current_heading = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Ultima secțiune
    content = "\n".join(current_lines).strip()
    if content:
        sections[current_heading] = content

    return sections


def compare_bep_versions(markdown_a: str, markdown_b: str) -> dict:
    """
    Compară două versiuni BEP și returnează diff-ul pe secțiuni.

    Args:
        markdown_a: Markdown-ul versiunii mai vechi (A)
        markdown_b: Markdown-ul versiunii mai noi (B)

    Returns:
        Dict cu structura diff-ului:
        {
            "added": [...],       # Secțiuni noi în B
            "removed": [...],     # Secțiuni șterse din A
            "modified": [{heading, summary}, ...],
            "unchanged": [...],
            "summary": "..."
        }
    """
    sections_a = _parse_sections(markdown_a)
    sections_b = _parse_sections(markdown_b)

    headings_a = set(sections_a.keys())
    headings_b = set(sections_b.keys())

    diff = SectionDiff()

    # Secțiuni adăugate
    diff.added = sorted(headings_b - headings_a)

    # Secțiuni șterse
    diff.removed = sorted(headings_a - headings_b)

    # Secțiuni comune: verificăm dacă s-au modificat
    for heading in sorted(headings_a & headings_b):
        content_a = sections_a[heading]
        content_b = sections_b[heading]
        if content_a != content_b:
            # Calculăm o metrică simplă de diferență
            lines_a = content_a.splitlines()
            lines_b = content_b.splitlines()
            len_diff = len(lines_b) - len(lines_a)
            direction = "extinsă" if len_diff > 0 else "redusă" if len_diff < 0 else "reformulată"
            diff.modified.append({
                "heading": heading,
                "summary": f"Secțiune {direction} ({len(lines_a)} → {len(lines_b)} linii)",
                "lines_before": len(lines_a),
                "lines_after": len(lines_b),
            })
        else:
            diff.unchanged.append(heading)

    # Summary text
    parts = []
    if diff.added:
        parts.append(f"{len(diff.added)} secțiuni noi")
    if diff.removed:
        parts.append(f"{len(diff.removed)} secțiuni șterse")
    if diff.modified:
        parts.append(f"{len(diff.modified)} secțiuni modificate")
    if diff.unchanged:
        parts.append(f"{len(diff.unchanged)} secțiuni neschimbate")

    return {
        "added": diff.added,
        "removed": diff.removed,
        "modified": diff.modified,
        "unchanged": diff.unchanged,
        "summary": ", ".join(parts) if parts else "Nu sunt diferențe.",
    }
