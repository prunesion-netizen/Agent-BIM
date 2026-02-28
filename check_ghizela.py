import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import chromadb
from collections import defaultdict

CHROMA_DIR = "chroma_db"
client = chromadb.PersistentClient(path=CHROMA_DIR)
col = client.get_collection("bim_knowledge")

print(f"Total chunks in DB: {col.count()}")
print()

# Paginate in batches of 2000
by_source = defaultdict(int)
offset = 0
batch = 2000
while True:
    results = col.get(include=["metadatas"], limit=batch, offset=offset)
    if not results["metadatas"]:
        break
    for meta in results["metadatas"]:
        by_source[meta["source"]] += 1
    offset += batch
    if len(results["metadatas"]) < batch:
        break

# Show Ghizela sources
print("=== Fisiere Ghizela indexate ===")
ghizela = {k: v for k, v in by_source.items() if "Ghizela" in k or "ghizela" in k}
if ghizela:
    for src, count in sorted(ghizela.items(), key=lambda x: -x[1]):
        print(f"  {count:4d} chunks | {src}")
else:
    print("  NICIUN fisier Ghizela gasit in DB!")
    print()
    # Show last 20 added sources (highest offset)
    print("  Ultimele 30 surse in DB (probabil documentele noi):")
    all_sorted = sorted(by_source.keys())
    for src in all_sorted[-30:]:
        print(f"    {by_source[src]:4d} chunks | {src}")

print()
print(f"Total surse unice: {len(by_source)}")
