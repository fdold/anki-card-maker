# Project Structure

```
anki-card-maker/
├── backend/                  # Backend application
│   ├── api/                  # FastAPI routes and request/response schemas
│   │   ├── main.py           # App factory and route definitions
│   │   └── schemas.py        # API request/response Pydantic models
│   ├── exporters/            # Output format exporters (CSV)
│   ├── models/               # Central model/provider integrations
│   │   └── providers/        # External model provider adapters
│   ├── pipeline/             # Processing pipeline components
│   │   └── parsers/          # Document parsers (txt_parser)
│   ├── services/             # Business logic services
│   │   ├── document_service.py
│   │   ├── run_service.py
│   │   ├── improvement_service.py
│   │   ├── export_service.py
│   │   └── registry.py       # Plugin/exporter discovery
│   └── storage/              # Repository layer (in-memory)
├── domain/                   # Shared Pydantic domain models
│   └── models.py             # All domain types (Document, RunCard, etc.)
├── frontend/                 # UI layer (CLI + Web)
│   ├── cli.py                # CLI client using api_client
│   ├── web.py                # Web UI server (Uvicorn, static files)
│   ├── api_client.py         # Shared HTTP client for backend API
│   └── static/               # HTML/JS/CSS for browser UI
├── plugins/                  # Plugin system
│   ├── base.py               # Base plugin classes and interfaces
│   ├── workflows/            # Workflow plugins (user-selectable)
│   │   └── basic_text_workflow.py
│   └── helpers/              # Internal helper plugins (not user-selectable)
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── api/                  # API resource tests
│   └── e2e/                  # End-to-end tests
├── docker/                   # Dockerfiles
├── docs/                     # Documentation
│   ├── architecture.md
│   ├── plugins.md
│   ├── INTERFACES.md
│   └── requirements/
│       └── REQUIREMENTS.md   # Canonical requirements (source of truth)
├── test-data/                # Sample inputs and export outputs
├── docker-compose.yml
├── Makefile
└── AGENTS.md                 # AI agent working rules
```

## Module Boundaries

- **domain/** — Shared models only. No business logic, no imports from backend/frontend/plugins.
- **backend/** — API, services, storage, pipeline. Depends on domain and plugins.
- **frontend/** — CLI and web UI. Communicates with backend only via HTTP API.
- **plugins/** — Workflow and helper plugins. Depends on domain. Must not import from backend services directly.
- **tests/** — Mirrors source structure. Uses fakes/stubs for external interfaces.

## Key Conventions

- API schemas live in `backend/api/schemas.py`, separate from domain models
- Storage uses the repository pattern (`backend/storage/`)
- Services orchestrate domain logic (`backend/services/`)
- Plugins define their own config schemas and manifests
- Frontend never imports backend internals — always goes through the HTTP API

## Interface Contracts

Full interface definitions live in `docs/INTERFACES.md`. Key boundaries:

### HTTP Resource API (`backend.api.main`)
- `GET /health`, `GET /overview`
- `POST /documents`, `GET /documents`, `GET /documents/{id}`
- `POST /runs`, `GET /runs`, `GET /runs/{id}`, `GET /runs/{id}/cards`
- `POST /runs/{id}/improvements`, `GET /runs/{id}/improvements`
- `POST /runs/{id}/exports`, `GET /exports/{id}`, `GET /exports/{id}/download`

No legacy one-shot generation endpoint. Clients must use the resource flow: upload → run → export → download.

### Workflow Plugin Interface (`plugins.base.WorkflowPlugin`)
- Exposes `manifest` (PluginManifest), `config_model`, `generate_cards()`, `apply_improvement()`
- Plugins own their prompts, extraction strategy, and config schema
- One plugin per generation run

### Repository Interface (`backend.storage.*`)
- `save()`, `get()`, `list()`, `update()` pattern
- `get()` returns model or `None`
- In-memory implementations now; persistent variants planned
- Must be replaceable with fakes in tests

### Exporter Interface (`backend.services.registry.ExporterDefinition`)
- Receives `list[ExportableAnkiCard]` (front, back, tags only)
- Currently: CSV exporter (`text/csv`)

### Frontend Proxy (`frontend.web`)
- All `/api/*` routes proxy to backend with same paths
- Preserves backend status codes; returns 502 on backend unreachable

### Planned Interfaces (not yet implemented)
- Workflow runtime (LangGraph-backed, project-owned abstraction)
- Information graph (user-facing extracted content representation)
- External capability interfaces (LLM, OCR, embedding, ML — all behind injectable interfaces with test doubles)
