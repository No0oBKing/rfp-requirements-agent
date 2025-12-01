# RFPAgentic

Multi-agent FastAPI + Streamlit app for extracting and managing RFP requirements, with PostgreSQL persistence and LLM-backed agents.

## Prerequisites
- Python 3.13+
- PostgreSQL (or use docker-compose)
- OpenAI API key for LLM agents

## Environment Variables
Create a `.env` with at least:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rfp_agentic
OPENAI_API_KEY=sk-...
OPENAI_MODEL=openai:gpt-4o
LOGFIRE_SERVICE_NAME=rfp-agentic
LOGFIRE_SEND_TO_LOGFIRE=false
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET=change_me
JWT_ALGORITHM=HS256
```
Optional: set `API_URL` in the Streamlit environment to point UI to the API (defaults to http://localhost:8000/api).

## Install
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Database Setup
Ensure PostgreSQL is running and `DATABASE_URL` is reachable. Then apply migrations:
```bash
alembic upgrade head
```

## Run (local)
- API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Streamlit UI: in another shell, `streamlit run ui/app.py --server.port 8501`

Login to the UI with the admin credentials (default admin/admin123), upload a PDF/DOCX, analyze, and review requirements.

## Docker Compose (DB only provided)
`docker-compose.yml` currently starts Postgres. 

## Auth
JWT Bearer with a fixed admin user (no signup). Obtain a token via `POST /api/auth/login` with JSON `{ "username": "admin", "password": "admin123" }` (or your env overrides). Include `Authorization: Bearer <token>` on API calls. UI handles this via a login form.

## Notes
- Exports include only accepted items (`is_accepted == True`).
- Prompts are in `app/prompts/*.py` and referenced by agents.
- Logging uses logfire; set `LOGFIRE_SEND_TO_LOGFIRE=false` to avoid auth.
