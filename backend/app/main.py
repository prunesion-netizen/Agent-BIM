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
    """Rulează Alembic upgrade head la startup."""
    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations applied successfully.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations()
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
from app.api import projects  # noqa: E402
from app.api import bep  # noqa: E402
from app.api import chat  # noqa: E402
from app.api import verifier  # noqa: E402
from app.api import bep_verification  # noqa: E402

app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(bep.router, prefix="/api", tags=["BEP Generator"])
app.include_router(chat.router, prefix="/api", tags=["Chat Expert"])
app.include_router(verifier.router, prefix="/api", tags=["BEP Verifier"])
app.include_router(bep_verification.router, prefix="/api", tags=["BEP Verification"])
