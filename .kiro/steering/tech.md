# Tech Stack

## Language & Runtime

- Python (3.11+)
- Virtual environment at `.venv/`

## Frameworks & Libraries

- **FastAPI** (>=0.115, <1.0) — Backend REST API
- **Pydantic** (>=2.8, <3.0) — Domain models and request/response schemas
- **Uvicorn** (>=0.30, <1.0) — ASGI server
- **pytest** (>=8.3, <9.0) — Test framework (dev dependency)
- **httpx** (>=0.28, <1.0) — HTTP test client (dev dependency)
- **LangGraph** — Planned workflow runtime for graph-based plugin execution

## Infrastructure

- Docker Compose for local development
- Backend container: FastAPI on port 8000
- Frontend container: Uvicorn serving web UI on port 8501
- In-memory storage (no database yet)

## Common Commands

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Install dev dependencies into .venv
make install-dev

# Start full stack (backend + frontend)
docker compose up --build

# Run CLI directly
python -m frontend.cli generate path/to/notes.txt --plugin-id basic_text_workflow --csv-output cards.csv
```

## API Server

- Entry point: `backend.api.main:app`
- Run locally: `uvicorn backend.api.main:app --reload`

## Testing

- Test runner: pytest via `.venv/bin/python -m pytest`
- Test directories: `tests/unit/`, `tests/integration/`, `tests/api/`, `tests/e2e/`
- Tests use in-memory fakes for repositories and external interfaces
- Fixtures use minimal representative data, not production-like datasets

## Package

- Installed as editable package (`pip install -e ".[dev]"`)
- Entry point: `anki-card-maker` CLI command
