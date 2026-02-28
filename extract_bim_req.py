"""
Extrage toate fragmentele relevante BIM din documentele Ghizela
si le salveaza pentru analiza si constructia BEP-ului.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR  = "chroma_db"
COLLECTION  = "bim_knowledge"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

client     = chromadb.PersistentClient(path=CHROMA_DIR)
col        = client.get_collection(COLLECTION)
embedder   = SentenceTransformer(EMBED_MODEL)

QUERIES = [
    "cerinte BIM modelare digitala proiect",
    "software BIM Autodesk Revit IFC formate fisiere",
    "livrabile BIM modele faze proiect predare",
    "BIM manager coordinator responsabilitati echipa",
    "Common Data Environment CDE management informatii",
    "LOD nivel detaliu modele BIM",
    "As-Built documentatie finala predare beneficiar",
    "standarde BIM ISO 19650 aplicabile proiect",
    "coordonare interferente clash detection modele",
    "obiectul contractului lucrari constructii depozit celula",
]

TARGET_SOURCES = [
    "Ghizela\\PT Ghizela\\PT+CS+DE\\PT+CS+DE\\2024-02-21_PT_CJT_EDITABIL\\2025-02-21_Parte_Scrisa\\2025-02-21_03_CS.docx",
    "Ghizela\\PT Ghizela\\PT+CS+DE\\PT+CS+DE\\2024-02-21_PT_CJT_EDITABIL\\2025-02-21_Parte_Scrisa\\2025-02-21_00_Memoriu_PT.docx",
    "Ghizela\\PT Ghizela\\PT+CS+DE\\PT+CS+DE\\2025-02-21_DTOE_EDITABIL\\2024-11-21_00_DTOE.docx",
    "Ghizela\\BIM\\ACC Docs si Build.docx",
    "Ghizela\\Documente contractuale\\Ghizela\\SEAP.pdf",
]

all_results = {}  # chunk_text -> metadata

for q in QUERIES:
    emb = embedder.encode(q).tolist()
    res = col.query(
        query_embeddings=[emb],
        n_results=15,
        include=["documents", "metadatas", "distances"],
    )
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        src = meta["source"]
        # Prioritize Ghizela documents
        if any(src == t for t in TARGET_SOURCES) or "Ghizela" in src:
            key = doc[:100]
            if key not in all_results:
                all_results[key] = {
                    "doc": doc,
                    "source": src,
                    "page": meta["page"],
                    "relevance": round(1.0 - dist, 3),
                    "query": q,
                }

# Sort by source then page
items = sorted(all_results.values(), key=lambda x: (x["source"], x["page"]))

print(f"Total fragmente unice relevante din Ghizela: {len(items)}")
print("=" * 70)

current_src = None
for item in items:
    if item["source"] != current_src:
        current_src = item["source"]
        print(f"\n{'='*70}")
        print(f"SURSA: {current_src}")
        print(f"{'='*70}")
    print(f"\n[Pag. {item['page']} | Relevanta: {item['relevance']} | Query: {item['query']}]")
    print(item["doc"][:600])
    print("-" * 40)
