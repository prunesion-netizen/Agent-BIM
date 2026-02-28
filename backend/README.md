# Agent BIM Romania — Backend (FastAPI)

Backend API pentru management BIM conform ISO 19650.

## Structura

```
backend/
  app/
    main.py              # FastAPI app, CORS, routere
    ai_client.py         # Interfață Claude API (call_llm, call_llm_chat_expert)
    api/
      bep.py             # POST /api/generate-bep
      chat.py            # POST /api/chat-expert
    schemas/
      project_context.py # ProjectContext, BimTeamRole, SoftwareItem (Pydantic)
    services/
      bep_generator.py   # Logica de generare BEP
      chat_expert.py     # Logica Chat Expert BIM
    models/              # (rezervat pentru ORM/DB)
  requirements.txt
  .env.example
```

## Pornire server

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # completează ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

## Endpoints

| Metoda | Endpoint            | Descriere                          |
|--------|--------------------|------------------------------------|
| GET    | /healthcheck       | Status server                      |
| POST   | /api/generate-bep  | Generează BEP din ProjectContext   |
| POST   | /api/chat-expert   | Chat Expert BIM                    |

## Documentație API

Deschide http://localhost:8000/docs pentru Swagger UI.
