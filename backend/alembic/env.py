"""
Alembic env.py — Configurare runtime pentru migrări.

Citește DATABASE_URL din .env și folosește modelele SQLAlchemy
pentru auto-generarea migrărilor.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Adaugă directorul backend/ în sys.path pentru import-uri app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

# Alembic Config
config = context.config

# Suprascrie URL-ul din alembic.ini cu cel din .env (dacă există)
database_url = os.getenv("DATABASE_URL")
if database_url:
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
