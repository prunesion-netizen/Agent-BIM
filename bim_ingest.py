"""
bim_ingest.py — Indexare documente BIM în ChromaDB
Rulează O SINGURĂ DATĂ (sau ori de câte ori se adaugă documente noi).

Utilizare:
    python bim_ingest.py

Procesează toate PDF și DOCX din folderul BIM/, le împarte în
fragmente de 800 caractere (overlap 150) și le stochează în ChromaDB
cu metadate {source, category, page, chunk_index}.
"""

import os
import re
import sys
import hashlib
import time
from pathlib import Path

# Fix encoding pe Windows (cp1250 nu suporta caractere romanesti)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import chromadb
from chromadb.config import Settings

# ── Categorii de documente ─────────────────────────────────────────────────────
CATEGORY_RULES = [
    (r"19650",            "ISO 19650"),
    (r"RTC.?8\b",         "RTC8"),
    (r"RTC.?9\b",         "RTC9"),
    (r"UK.BIM|PAS.1192", "UK BIM Framework"),
    (r"curs.bim|manager", "Curs BIM Manager"),
    (r"COBie",            "COBie"),
    (r"\bIFC\b",          "IFC"),
    (r"INOVECO|SEAU|studiu.de.caz|case.study", "Studii de caz"),
    (r"academic|universit|cercet",             "Resurse Academice"),
    # ── Documente de proiect / contract ──────────────────────────────────
    (r"contract|acord.cadru|act.aditional",    "Contract"),
    (r"caiet.sarcini|specificat",              "Specificatii Tehnice"),
    (r"BEP|executie.plan|execution.plan",      "BEP"),
    (r"EIR|cerint.*informatii|information.req","EIR"),
    (r"proces.verbal|PV\b|minuta|sedinta",     "PV Sedinta"),
    (r"raport.progres|raport.lunar|situatie",  "Raport Progres"),
]

BIM_FOLDER    = Path("BIM")
CHROMA_DIR    = "chroma_db"
COLLECTION    = "bim_knowledge"
EMBED_MODEL   = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150
MAX_FILE_MB   = 50
MIN_PAGE_CHARS = 100   # pagini cu mai puțin de N caractere → considerate imagine-only


def detect_category(filename: str) -> str:
    name = filename.upper()
    for pattern, cat in CATEGORY_RULES:
        if re.search(pattern, name, re.IGNORECASE):
            return cat
    return "General BIM"


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Împarte textul în fragmente cu suprapunere."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def extract_pdf(path: Path):
    """Extrage text din PDF cu PyMuPDF. Returnează lista de (page_num, text)."""
    import fitz  # pymupdf
    pages = []
    try:
        doc = fitz.open(str(path))
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if len(text.strip()) >= MIN_PAGE_CHARS:
                pages.append((i + 1, text.strip()))
        doc.close()
    except Exception as e:
        print(f"  ⚠ Eroare PDF {path.name}: {e}")
    return pages


def extract_docx(path: Path):
    """Extrage text din DOCX. Returnează lista de (1, text_complet)."""
    from docx import Document
    try:
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        return [(1, text)] if text.strip() else []
    except Exception as e:
        print(f"  ⚠ Eroare DOCX {path.name}: {e}")
        return []


def md5_id(*parts) -> str:
    data = "|".join(str(p) for p in parts)
    return hashlib.md5(data.encode("utf-8")).hexdigest()


def should_skip(path: Path) -> bool:
    name = path.name
    if name.startswith("~$"):
        return True
    if "__MACOSX" in str(path):
        return True
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        print(f"  ⊘ Sărită (>{MAX_FILE_MB}MB): {name}")
        return True
    return False


def collect_files():
    pdfs  = list(BIM_FOLDER.rglob("*.pdf"))
    docxs = list(BIM_FOLDER.rglob("*.docx"))
    return pdfs + docxs


def main():
    if not BIM_FOLDER.exists():
        print(f"✗ Folderul '{BIM_FOLDER}' nu există. Plasează documentele BIM acolo și re-rulează.")
        return

    print("=" * 60)
    print(" Agent BIM — Ingestie documente RAG")
    print("=" * 60)

    # ── Model embedding multilingual ──────────────────────────────
    print(f"Se incarca modelul de embedding: {EMBED_MODEL}")
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer(EMBED_MODEL)
    print("Model incarcat.\n")

    # ── ChromaDB (fara embedding_function — embed manual) ─────────
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    existing_ids = set(collection.get(include=[])["ids"])
    print(f"Chunks existente in DB: {len(existing_ids)}")

    # ── Colectare fișiere ─────────────────────────────────────────
    files = collect_files()
    print(f"Fișiere găsite: {len(files)}  (PDF + DOCX)\n")

    total_chunks = 0
    skipped      = 0
    t0           = time.time()

    for file_path in files:
        if should_skip(file_path):
            skipped += 1
            continue

        ext      = file_path.suffix.lower()
        rel_name = str(file_path.relative_to(BIM_FOLDER))
        category = detect_category(file_path.name)

        print(f"  ▸ {rel_name}  [{category}]")

        if ext == ".pdf":
            pages = extract_pdf(file_path)
        elif ext == ".docx":
            pages = extract_docx(file_path)
        else:
            continue

        if not pages:
            print(f"    – fără text utilizabil, sărită")
            skipped += 1
            continue

        # Construim chunks per pagină
        ids, docs, metas = [], [], []
        for page_num, page_text in pages:
            chunks = chunk_text(page_text)
            for ci, chunk in enumerate(chunks):
                if len(chunk.strip()) < 30:
                    continue
                chunk_id = md5_id(rel_name, page_num, ci, chunk[:80])
                if chunk_id in existing_ids:
                    continue  # idempotent skip
                ids.append(chunk_id)
                docs.append(chunk)
                metas.append({
                    "source":      rel_name,
                    "category":    category,
                    "page":        page_num,
                    "chunk_index": ci,
                })

        if ids:
            # Calculam embedding-urile cu sentence-transformers
            embeddings = embedder.encode(docs, show_progress_bar=False).tolist()
            # Upsert in batch-uri de 500
            batch_size = 500
            for bi in range(0, len(ids), batch_size):
                collection.upsert(
                    ids=ids[bi:bi+batch_size],
                    documents=docs[bi:bi+batch_size],
                    embeddings=embeddings[bi:bi+batch_size],
                    metadatas=metas[bi:bi+batch_size],
                )
            total_chunks += len(ids)
            print(f"    + {len(ids)} chunks noi")

    elapsed = time.time() - t0
    final_count = collection.count()

    print("\n" + "=" * 60)
    print(f" Ingestie finalizată în {elapsed:.0f}s")
    print(f" Chunks adăugate acum : {total_chunks}")
    print(f" Total chunks în DB   : {final_count}")
    print(f" Fișiere sărite       : {skipped}")
    print("=" * 60)

    if final_count > 0:
        print("\n✓ ChromaDB gata. Poți porni aplicația: python app.py")
    else:
        print("\n⚠ Niciun chunk indexat. Verifică că folderul BIM/ conține documente.")


if __name__ == "__main__":
    main()
