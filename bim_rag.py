"""
bim_rag.py — Singleton RAG engine pentru Agent BIM Romania

Foloseste aceeasi functie de embedding (SentenceTransformerEmbeddingFunction)
ca bim_ingest.py, astfel incat spatiile vectoriale sunt identice.

Interfata publica:
    init_rag()                     -> apelat la startup Flask
    query_rag(question, n=5)       -> dict {context, sources, rag_used}
    get_rag_stats()                -> dict {ready, chunk_count, model}
"""

import os
import logging

logger = logging.getLogger(__name__)

CHROMA_DIR  = "chroma_db"
COLLECTION  = "bim_knowledge"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
N_RESULTS   = 5

# Starea globala a motorului RAG
_rag_state = {
    "ready":       False,
    "collection":  None,
    "embedder":    None,
    "chunk_count": 0,
    "error":       None,
}


def init_rag() -> bool:
    """
    Initializeaza ChromaDB cu aceeasi functie de embedding folosita la ingestie.
    Apelata o singura data la pornirea Flask.
    Returneaza True daca RAG-ul este functional.
    """
    global _rag_state

    if _rag_state["ready"]:
        return True

    if not os.path.isdir(CHROMA_DIR):
        _rag_state["error"] = f"Directorul '{CHROMA_DIR}' lipseste. Ruleaza: python bim_ingest.py"
        logger.warning(_rag_state["error"])
        return False

    try:
        import chromadb
        from sentence_transformers import SentenceTransformer

        client = chromadb.PersistentClient(path=CHROMA_DIR)

        # Verificam ca exista colectia
        existing = [c.name for c in client.list_collections()]
        if COLLECTION not in existing:
            _rag_state["error"] = f"Colectia '{COLLECTION}' nu exista. Ruleaza: python bim_ingest.py"
            logger.warning(_rag_state["error"])
            return False

        # Fara embedding_function — embedurile sunt precomputate (ca la ingestie)
        collection = client.get_collection(COLLECTION)
        count = collection.count()
        if count == 0:
            _rag_state["error"] = "Colectia este goala. Ruleaza: python bim_ingest.py"
            logger.warning(_rag_state["error"])
            return False

        logger.info(f"ChromaDB conectat — {count} chunks")

        # Incarcam acelasi model folosit la ingestie
        logger.info(f"Se incarca modelul de embedding: {EMBED_MODEL}")
        embedder = SentenceTransformer(EMBED_MODEL)
        logger.info("Model embedding incarcat")

        _rag_state.update({
            "ready":       True,
            "collection":  collection,
            "embedder":    embedder,
            "chunk_count": count,
            "error":       None,
        })
        return True

    except ImportError as e:
        _rag_state["error"] = f"Dependente lipsa: {e}. Ruleaza: pip install -r requirements.txt"
        logger.error(_rag_state["error"])
        return False
    except Exception as e:
        _rag_state["error"] = f"Eroare initializare RAG: {e}"
        logger.error(_rag_state["error"])
        return False


def query_rag(question: str, n: int = N_RESULTS) -> dict:
    """
    Cauta cele mai relevante fragmente pentru intrebare.
    Embedding-ul este facut de ChromaDB prin aceeasi EF ca la ingestie.

    Returneaza:
        {
            "context":   str,   # text concatenat pentru system prompt
            "sources":   list,  # [{title, page, category, score}, ...]
            "rag_used":  bool
        }
    """
    if not _rag_state["ready"]:
        return {"context": "", "sources": [], "rag_used": False}

    try:
        collection = _rag_state["collection"]
        embedder   = _rag_state["embedder"]

        query_embedding = embedder.encode(question).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n, _rag_state["chunk_count"]),
            include=["documents", "metadatas", "distances"],
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        if not documents:
            return {"context": "", "sources": [], "rag_used": False}

        # Construim contextul si lista de surse
        context_parts = []
        sources = []
        seen_sources = set()

        for doc, meta, dist in zip(documents, metadatas, distances):
            source    = meta.get("source", "Necunoscut")
            page      = meta.get("page", 1)
            category  = meta.get("category", "General BIM")
            # Distanta cosinus -> scor relevanta (0-1, mai mare = mai relevant)
            relevance = round(max(0.0, 1.0 - dist), 3)

            title = _short_title(source)

            context_parts.append(
                f"[Sursa: {title}, Pag. {page}]\n{doc}"
            )

            # Deduplicam sursele in panoul lateral
            source_key = f"{source}:{page}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append({
                    "title":     title,
                    "source":    source,
                    "page":      page,
                    "category":  category,
                    "relevance": relevance,
                })

        context = "\n\n---\n\n".join(context_parts)
        return {"context": context, "sources": sources, "rag_used": True}

    except Exception as e:
        logger.error(f"Eroare query RAG: {e}")
        return {"context": "", "sources": [], "rag_used": False}


def get_rag_stats() -> dict:
    """Returneaza starea curenta a motorului RAG."""
    return {
        "ready":       _rag_state["ready"],
        "chunk_count": _rag_state["chunk_count"],
        "model":       EMBED_MODEL if _rag_state["ready"] else None,
        "error":       _rag_state["error"],
    }


# ── Utilitar intern ────────────────────────────────────────────────────────────
def _short_title(source: str) -> str:
    """Extrage un titlu lizibil din calea fisierului."""
    basename = os.path.basename(source)
    name, _ = os.path.splitext(basename)
    name = name.replace("_", " ").replace("-", " ")
    return name[:80] if len(name) > 80 else name
