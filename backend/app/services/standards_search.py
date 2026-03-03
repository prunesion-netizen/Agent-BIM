"""
standards_search.py — Wrapper peste ChromaDB pentru căutarea în standarde BIM.

Folosit de tool-ul agent `search_bim_standards`.
Dacă ChromaDB nu este disponibil, returnează rezultate din cunoștințe hardcodate.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Calea către directorul ChromaDB
_CHROMA_DB_PATH = str(
    Path(__file__).resolve().parent.parent.parent.parent / "chroma_db"
)

_client = None
_collection = None
_embed_model = None
_initialized = False
_initializing = False

_EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def _init_chroma():
    """Inițializează clientul ChromaDB (lazy, o singură dată)."""
    global _client, _collection, _embed_model, _initialized, _initializing

    if _initialized:
        return

    if _initializing:
        return

    _initializing = True

    try:
        import chromadb
        from sentence_transformers import SentenceTransformer

        logger.info("Se încarcă modelul SentenceTransformer...")
        _embed_model = SentenceTransformer(_EMBED_MODEL_NAME)
        logger.info("Model SentenceTransformer încărcat.")

        _client = chromadb.PersistentClient(path=_CHROMA_DB_PATH)
        _collection = _client.get_collection(name="bim_knowledge")
        logger.info(
            f"ChromaDB inițializat: colecție 'bim_knowledge' "
            f"cu {_collection.count()} documente"
        )
    except ImportError:
        logger.warning(
            "chromadb sau sentence-transformers nu este instalat. "
            "Tool-ul search_bim_standards va folosi cunoștințe hardcodate."
        )
    except Exception as e:
        logger.warning(f"Eroare la inițializarea ChromaDB: {e}")
    finally:
        _initialized = True
        _initializing = False


def warmup():
    """Pre-încarcă modelul la startup (apelat din lifespan)."""
    import threading

    def _bg():
        logger.info("Warmup: pre-încărcare ChromaDB + SentenceTransformer...")
        _init_chroma()
        logger.info("Warmup complet.")

    threading.Thread(target=_bg, daemon=True).start()


def search_standards(query: str, n_results: int = 5) -> list[dict]:
    """
    Caută în baza de date de standarde BIM.

    Args:
        query: Textul de căutare
        n_results: Numărul maxim de rezultate

    Returns:
        Listă de dict-uri cu: text, source, relevance_score
    """
    _init_chroma()

    if _collection is not None and _embed_model is not None:
        try:
            query_embedding = _embed_model.encode([query]).tolist()
            results = _collection.query(
                query_embeddings=query_embedding,
                n_results=min(n_results, 10),
            )

            output = []
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for i, doc in enumerate(documents):
                meta = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 0
                output.append({
                    "text": doc[:1000],  # limităm lungimea
                    "source": meta.get("source", "Standard BIM"),
                    "category": meta.get("category", ""),
                    "relevance_score": round(1 - distance, 3) if distance else 0,
                })

            return output
        except Exception as e:
            logger.warning(f"Eroare la căutare ChromaDB: {e}")

    # Fallback: cunoștințe hardcodate
    return _fallback_search(query, n_results)


def _fallback_search(query: str, n_results: int = 5) -> list[dict]:
    """Returnează cunoștințe hardcodate relevante dacă ChromaDB nu e disponibil."""
    q = query.lower()
    results = []

    standards_kb = [
        {
            "keywords": ["iso 19650", "19650-1", "concepte", "principii"],
            "text": (
                "SR EN ISO 19650-1:2019 — Organizarea și digitalizarea informațiilor "
                "referitoare la clădiri și lucrări de inginerie civilă, inclusiv "
                "modelarea informațiilor clădirii (BIM). Partea 1: Concepte și principii. "
                "Definește cadrul general pentru managementul informațiilor pe durata "
                "ciclului de viață al activelor construite."
            ),
            "source": "SR EN ISO 19650-1:2019",
        },
        {
            "keywords": ["19650-2", "livrare", "faza de livrare", "bep"],
            "text": (
                "SR EN ISO 19650-2:2021 — Partea 2: Faza de livrare a activelor. "
                "Specifică cerințele pentru managementul informațiilor în faza de proiectare "
                "și execuție. Include procesele de: numire, mobilizare, producție colaborativă "
                "a informațiilor și livrarea modelului informațional al proiectului (PIM)."
            ),
            "source": "SR EN ISO 19650-2:2021",
        },
        {
            "keywords": ["19650-3", "operațional", "operare", "mentenanță"],
            "text": (
                "SR EN ISO 19650-3:2021 — Partea 3: Faza operațională a activelor. "
                "Definește cerințele pentru managementul informațiilor în faza de operare "
                "și mentenanță, inclusiv modelul informațional al activului (AIM)."
            ),
            "source": "SR EN ISO 19650-3:2021",
        },
        {
            "keywords": ["lod", "loi", "nivel", "detaliu", "informare", "17412"],
            "text": (
                "BS EN 17412-1:2021 — Building Information Modelling. "
                "Level of Information Need. Definește cadrul pentru specificarea "
                "nivelului de informare necesar (geometrie, informații, documentație) "
                "pentru schimbul de informații în proiecte BIM."
            ),
            "source": "BS EN 17412-1:2021",
        },
        {
            "keywords": ["cde", "mediu comun", "date", "environment"],
            "text": (
                "Common Data Environment (CDE) — Mediu comun de date conform ISO 19650. "
                "Structură cu 4 zone: Work In Progress (WIP), Shared, Published, Archived. "
                "Asigură un flux unic al informațiilor cu control al reviziilor "
                "și trasabilitate completă."
            ),
            "source": "ISO 19650-1 / CDE Framework",
        },
        {
            "keywords": ["rtc", "referențial", "tehnic", "construcții", "România"],
            "text": (
                "RTC 8 — Referențial tehnic privind proiectarea construcțiilor. "
                "RTC 9 — Referențial tehnic privind execuția lucrărilor de construcții. "
                "Aceste referențiale naționale completează cadrul normativ european "
                "și definesc cerințe specifice pentru proiecte din România."
            ),
            "source": "RTC 8, RTC 9 — România",
        },
        {
            "keywords": ["clash", "detecție", "coliziune", "coordonare"],
            "text": (
                "Clash Detection — Procesul de identificare a interferențelor geometrice "
                "între modelele BIM ale diferitelor discipline. Tipuri: hard clash "
                "(intersecție fizică), soft clash (spațiu insuficient), workflow clash "
                "(conflict de programare). Toleranțe tipice: 10-25mm pentru faza DDE."
            ),
            "source": "BIM Coordination Best Practices",
        },
        {
            "keywords": ["ifc", "format", "schimb", "interoperabilitate"],
            "text": (
                "IFC (Industry Foundation Classes) — Standard deschis ISO 16739 "
                "pentru schimbul de date BIM. Versiuni principale: IFC 2x3 (legacy), "
                "IFC 4 (actual), IFC 4.3 (infrastructură). Asigură interoperabilitate "
                "între software-uri BIM diferite (Revit, ArchiCAD, Tekla, etc.)."
            ),
            "source": "ISO 16739 / buildingSMART",
        },
    ]

    for entry in standards_kb:
        if any(kw in q for kw in entry["keywords"]):
            results.append({
                "text": entry["text"],
                "source": entry["source"],
                "relevance_score": 0.85,
            })

    # Dacă nu am găsit nimic specific, returnăm primele 3
    if not results:
        results = [
            {
                "text": e["text"],
                "source": e["source"],
                "relevance_score": 0.5,
            }
            for e in standards_kb[:3]
        ]

    return results[:n_results]
