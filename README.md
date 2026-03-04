# Agent BIM Romania

Full-stack web application for BIM (Building Information Modeling) management in Romania, built around **ISO 19650** standards.

AI-powered BEP generation, verification, and project management with Claude API integration.

## Features

### Core BIM Management
- **BEP Generation** — AI-generated BIM Execution Plans with DOCX export
- **BEP Verification** — Automated BEP vs Model verification with detailed reports
- **Chat Expert BIM** — Conversational AI assistant for BIM standards questions
- **Agent BIM** — Autonomous AI agent with 27 tools, SSE streaming, conversation history

### ISO 19650 Compliance Suite
- **ISO Compliance Dashboard** — Parts 1/2/3/5 scoring with checks and recommendations
- **EIR Generator** — Exchange Information Requirements per ISO 19650-2
- **TIDP/MIDP Delivery Plan** — Task Information Delivery Plan with progress tracking
- **RACI Matrix** — Interactive responsibility matrix (tasks x roles)
- **LOIN Matrix** — Level of Information Need per element/phase (BS EN 17412-1)
- **Handover Checklist** — As-built handover checklist per ISO 19650-3
- **CDE Workflow** — Common Data Environment state management (WIP/Shared/Published/Archived)
- **Clash Management** — Interdisciplinary clash detection and resolution
- **KPI Dashboard** — Key Performance Indicators with overall scoring
- **COBie Validator** — Upload and validate COBie XLSX, generate templates
- **Security Classification** — Information security plan per ISO 19650-5

### Platform Features
- **JWT Authentication** — Register/login with 3 roles (admin, bim_manager, viewer)
- **Project Management** — CRUD projects with inline editing
- **IFC Viewer** — 3D model viewer (web-ifc-three)
- **IFC Import** — Upload IFC files with auto-generated model summaries
- **Dashboard** — Project overview with health scores and status distribution

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.13, FastAPI, SQLAlchemy, Alembic |
| **Frontend** | React 19, TypeScript, Vite |
| **AI** | Claude API (claude-sonnet-4-6) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **RAG** | ChromaDB + sentence-transformers (legacy) |
| **3D Viewer** | three.js, web-ifc, web-ifc-three |

## Architecture

```
frontend/          React + Vite + TypeScript (port 3002)
  src/
    components/    30+ components (Dashboard, AgentChat, ISO panels...)
    contexts/      AuthProvider, ProjectProvider
    hooks/         useAgentChat (SSE streaming)

backend/           FastAPI (port 8000)
  app/
    api/           20 routers, 57 API routes
    models/        19 SQLAlchemy tables
    schemas/       Pydantic models + converters
    services/      Business logic (generators, validators, AI client)
    repositories/  Database CRUD operations
  alembic/         Database migrations (001-007)
```

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 22+
- Anthropic API key

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and JWT_SECRET
python -m uvicorn app.main:app --port 8000 --reload
```

Database tables are auto-created on startup (SQLite by default).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3002

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `DATABASE_URL` | DB connection string (default: sqlite:///data/agent_bim.db) | No |
| `JWT_SECRET` | Secret for JWT token signing | Yes |
| `JWT_ALGORITHM` | JWT algorithm (default: HS256) | No |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry (default: 30) | No |

## Deploy

### Docker Compose

```bash
cp backend/.env.example backend/.env
# Edit .env with your API key
docker compose up -d
```

Services: PostgreSQL (port 5432) + Backend (port 8000) + Frontend (port 80)

### Render.com

Connect the repo on Render dashboard. The `render.yaml` blueprint auto-configures:
- **agent-bim-api** — Python web service (free tier)
- **agent-bim-frontend** — Static site with API rewrites (free tier)
- **agent-bim-db** — PostgreSQL (free tier)

Set `ANTHROPIC_API_KEY` manually in the Render dashboard.

## API Documentation

With the backend running, open http://localhost:8000/docs for interactive Swagger UI.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, get JWT tokens |
| GET | `/api/projects` | List all projects |
| POST | `/api/projects/{id}/generate-bep` | Generate BEP document |
| GET | `/api/projects/{id}/export-bep-docx` | Export BEP as DOCX |
| POST | `/api/projects/{id}/verify-bep-model` | Verify BEP vs model |
| POST | `/api/projects/{id}/agent-chat` | Agent BIM (SSE) |
| POST | `/api/chat-expert` | Chat Expert BIM |
| GET | `/api/projects/{id}/iso-compliance` | ISO 19650 compliance |
| POST | `/api/projects/{id}/generate-eir` | Generate EIR |
| POST | `/api/projects/{id}/generate-tidp` | Generate delivery plan |
| POST | `/api/projects/{id}/generate-raci` | Generate RACI matrix |
| GET | `/api/projects/{id}/kpis` | KPI dashboard |
| POST | `/api/projects/{id}/validate-cobie` | Validate COBie XLSX |

## License

Private repository.
