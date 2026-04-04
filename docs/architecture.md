# Architecture

## Current foundation

The repository is organized into dedicated modules for API, services, pipeline, parsers,
exporters, storage, domain models, and plugins.

## Current workflow path

1. A document is uploaded through `/documents` and normalized by `backend/pipeline/parsers/txt_parser.py`.
2. A run is created through `/runs`, which selects exactly one workflow plugin and generates traceable run cards.
3. Generated cards are exposed through `/runs/{run_id}/cards`.
4. Generic or workflow-driven improvements can update the stored cards attached to the run.
5. Exporters map the current non-deleted run cards into Anki-compatible output formats such as CSV.

## API shape

The backend now follows a resource-oriented API:

- `documents` for uploaded source material
- `runs` for workflow executions on selected documents
- `cards` as run-scoped generated card state
- `exports` as exporter-generated artifacts created from a run

The old one-shot generation endpoint is no longer part of the backend API.

## Notes

- Card-generation logic belongs in `plugins/workflows/`.
- Shared schemas live in `domain/`.
- Central model/provider integrations belong in `backend/models/`.
- Exporters stay dedicated backend modules and should not contain workflow logic.
- The frontend CLI now uses the same multi-step API flow as the backend resources.
- The target structure for centrally managed LLM and Ollama integration is
  documented in `docs/llm_ollama_architecture.md`.
