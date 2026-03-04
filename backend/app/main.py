"""
Agent BIM Romania — FastAPI Backend
Punct de intrare principal. Configurare CORS, rutare, healthcheck.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


def _run_migrations() -> None:
    """Rulează Alembic upgrade head la startup (sau create_all pentru SQLite)."""
    from app.db import DATABASE_URL, engine

    if DATABASE_URL.startswith("sqlite"):
        # SQLite — creează direct tabelele din modele (skip Alembic)
        from app.db import Base
        import app.models.sql_models  # noqa: F401 — înregistrează modelele
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite: all tables created via create_all().")
    else:
        alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations applied successfully.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations()

    # Pre-încarcă ChromaDB + SentenceTransformer în background
    from app.services.standards_search import warmup
    warmup()

    yield


app = FastAPI(
    title="Agent BIM Romania API",
    description="Backend API pentru management BIM conform ISO 19650",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",   # Vite dev (configured port)
        "http://127.0.0.1:3002",
        "http://localhost:5173",   # Vite dev default
        "http://localhost:5000",   # Flask legacy UI
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Healthcheck ───────────────────────────────────────────────────────────────
@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok", "service": "agent-bim-romania"}


# ── Routere ───────────────────────────────────────────────────────────────────
from app.api import auth  # noqa: E402
from app.api import projects  # noqa: E402
from app.api import bep  # noqa: E402
from app.api import chat  # noqa: E402
from app.api import verifier  # noqa: E402
from app.api import bep_verification  # noqa: E402
from app.api import projects_dashboard  # noqa: E402
from app.api import model_import  # noqa: E402
from app.api import agent  # noqa: E402
from app.api import cde  # noqa: E402
from app.api import eir  # noqa: E402
from app.api import deliverables  # noqa: E402
from app.api import raci  # noqa: E402
from app.api import loin  # noqa: E402
from app.api import operational  # noqa: E402
from app.api import security  # noqa: E402
from app.api import clashes  # noqa: E402
from app.api import kpis  # noqa: E402
from app.api import compliance  # noqa: E402
from app.api import cobie  # noqa: E402

app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(projects_dashboard.router, prefix="/api", tags=["Projects Dashboard"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(bep.router, prefix="/api", tags=["BEP Generator"])
app.include_router(chat.router, prefix="/api", tags=["Chat Expert"])
app.include_router(verifier.router, prefix="/api", tags=["BEP Verifier"])
app.include_router(bep_verification.router, prefix="/api", tags=["BEP Verification"])
app.include_router(model_import.router, prefix="/api", tags=["Model Import"])
app.include_router(agent.router, prefix="/api", tags=["Agent BIM"])
app.include_router(cde.router, prefix="/api", tags=["CDE Workflow"])
app.include_router(eir.router, prefix="/api", tags=["EIR/AIR"])
app.include_router(deliverables.router, prefix="/api", tags=["TIDP/MIDP"])
app.include_router(raci.router, prefix="/api", tags=["RACI Matrix"])
app.include_router(loin.router, prefix="/api", tags=["LOIN Matrix"])
app.include_router(operational.router, prefix="/api", tags=["Handover"])
app.include_router(security.router, prefix="/api", tags=["Security"])
app.include_router(clashes.router, prefix="/api", tags=["Clash Management"])
app.include_router(kpis.router, prefix="/api", tags=["KPI Tracking"])
app.include_router(compliance.router, prefix="/api", tags=["ISO Compliance"])
app.include_router(cobie.router, prefix="/api", tags=["COBie Validator"])
