"""
Alembic env.py — Configurare runtime pentru migrări.

Citește DATABASE_URL din .env (sau fallback SQLite) și folosește
modelele SQLAlchemy pentru auto-generarea migrărilor.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

# Adaugă directorul backend/ în sys.path pentru import-uri app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

# Alembic Config
config = context.config

# Folosește DATABASE_URL din .env, sau fallback SQLite (identic cu db.py)
_DEFAULT_SQLITE = "sqlite:///" + str(
    Path(__file__).resolve().parent.parent / "data" / "agent_bim.db"
)
database_url = os.getenv("DATABASE_URL", _DEFAULT_SQLITE)
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import modelele pentru auto-generare
from app.db import Base  # noqa: E402
from app.models.sql_models import (  # noqa: E402, F401
    ProjectModel,
    ProjectContextModel,
    GeneratedDocumentModel,
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Rulează migrările în mod offline (generează SQL fără conexiune)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Rulează migrările în mod online (cu conexiune la DB)."""
    url = config.get_main_option("sqlalchemy.url")
    is_sqlite = url.startswith("sqlite")

    connect_args = {"check_same_thread": False} if is_sqlite else {}
    connectable = create_engine(
        url, poolclass=pool.NullPool, connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite,  # batch mode necesar pentru ALTER pe SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
