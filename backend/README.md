# Agent BIM Romania — Backend (FastAPI)

Backend API for BIM management with ISO 19650 compliance.

## Stack

- **FastAPI** + Uvicorn
- **SQLAlchemy** ORM (SQLite dev / PostgreSQL prod)
- **Alembic** migrations
- **Claude API** (anthropic SDK) for AI features
- **JWT** authentication (python-jose + bcrypt)

## Structure

```
app/
  main.py                 # FastAPI app, CORS, 20 routers
  ai_client.py            # Claude API singleton
  db.py                   # SQLAlchemy engine + session
  api/                    # 20 API routers (57 routes)
    auth.py               # JWT register/login/refresh/me
    agent.py              # Autonomous agent with SSE
    bep.py                # BEP generation + export
    chat.py               # Chat Expert BIM
    projects.py           # Project CRUD
    compliance.py         # ISO 19650 compliance check
    eir.py, raci.py, ...  # ISO 19650 modules
  models/
    sql_models.py         # 19 SQLAlchemy tables
  schemas/                # Pydantic models
  services/               # Business logic
  repositories/           # Database CRUD
alembic/                  # Migrations 001-007
```

## Run

```bash
pip install -r requirements.txt
cp .env.example .env      # set ANTHROPIC_API_KEY + JWT_SECRET
python -m uvicorn app.main:app --port 8000 --reload
```

## API Docs

http://localhost:8000/docs (Swagger UI)
