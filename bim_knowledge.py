import os
from docx import Document


def extract_text_from_docx(filepath):
    doc = Document(filepath)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def load_bim_knowledge():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    doc_files = [
        "Ghid BIM.docx",
        "Importanța și Implementarea BIM în Sectorul Construcțiilor din România.docx",
    ]

    sections = []
    for filename in doc_files:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            text = extract_text_from_docx(filepath)
            sections.append(f"=== {filename} ===\n{text}")
        else:
            print(f"Warning: {filename} not found at {filepath}")

    return "\n\n".join(sections)
