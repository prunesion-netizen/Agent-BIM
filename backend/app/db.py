"""
db.py — SQLAlchemy engine, session factory, Base, și get_db() dependency.

Suportă PostgreSQL (producție) și SQLite (development local).
Setează DATABASE_URL în .env sau folosește SQLite implicit.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# Default: SQLite local în backend/data/agent_bim.db
_DEFAULT_SQLITE = "sqlite:///" + str(
    Path(__file__).resolve().parent.parent / "data" / "agent_bim.db"
)

DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_SQLITE)

_is_sqlite = DATABASE_URL.startswith("sqlite")

_engine_kwargs: dict = {}
if _is_sqlite:
    # SQLite nu suportă pool_pre_ping; necesită check_same_thread=False
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yield o sesiune SQLAlchemy, commit/rollback automat."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
