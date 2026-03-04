"""
conftest.py — Fixtures pentru teste backend Agent BIM.

Foloseste SQLite in-memory cu StaticPool pentru a partaja conexiunea.
"""

import os

# Override env BEFORE any app import
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"

import pytest  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Single shared in-memory SQLite engine (StaticPool = same connection for all)
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable WAL + foreign keys for SQLite
@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Patch app.db BEFORE importing the app
import app.db  # noqa: E402
app.db.engine = _test_engine
app.db.SessionLocal = sessionmaker(bind=_test_engine)

# Force import all models
import app.models.sql_models  # noqa: E402, F401

from app.db import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

TestingSession = sessionmaker(bind=_test_engine)


def _override_get_db():
    db = TestingSession()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Recreaza tabelele inainte de fiecare test."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def client():
    """TestClient FastAPI."""
    return TestClient(fastapi_app)


@pytest.fixture
def db_session():
    """Sesiune DB directa pentru setup test data."""
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_headers(client):
    """Inregistreaza un user si returneaza headers cu token."""
    res = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project_id(client, auth_headers):
    """Creeaza un proiect de test si returneaza ID-ul."""
    res = client.post("/api/projects", json={
        "name": "Test Project",
        "code": "TST01",
        "client_name": "Test Client",
        "project_type": "building",
    }, headers=auth_headers)
    return res.json()["id"]
