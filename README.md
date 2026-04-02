# anki-card-maker

Modular Python application for turning documents into Anki-compatible flashcards.

## Project Structure

- `frontend/` UI placeholder for later review and plugin selection
- `backend/` API, services, pipeline, parsers, exporters, storage, model integrations
- `domain/` shared Pydantic domain models
- `plugins/` workflow and helper plugins
- `tests/` unit, integration, API, and E2E tests
- `docker/` Dockerfiles
- `docs/` architecture and plugin documentation

## Quick Start

```bash
docker compose up --build
```

API-Endpunkte:

- `GET /health`
- `GET /overview`

## Current Status

The repository now contains a clean initial foundation with:

- FastAPI entry point
- centralized domain models
- TXT parser as the first stable input format
- first workflow plugin scaffold
- CSV exporter for early Anki compatibility
- baseline tests for parser, workflow, and export
