"""
Agent BIM Romania — FastAPI Backend
Punct de intrare principal. Configurare CORS, rutare, healthcheck.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Agent BIM Romania API",
    description="Backend API pentru management BIM conform ISO 19650",
    version="0.1.0",
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
from app.api import bep  # noqa: E402
from app.api import chat  # noqa: E402

app.include_router(bep.router, prefix="/api", tags=["BEP Generator"])
app.include_router(chat.router, prefix="/api", tags=["Chat Expert"])
