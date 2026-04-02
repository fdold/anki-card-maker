# Architecture

## Current foundation

The repository is organized into dedicated modules for API, services, pipeline, parsers,
exporters, storage, domain models, and plugins.

## Initial workflow path

1. A TXT document is normalized by `backend/pipeline/parsers/txt_parser.py`.
2. A single workflow plugin generates card candidates from `ParsedContent`.
3. Exporters map accepted cards into Anki-compatible output formats such as CSV.

## Notes

- Card-generation logic belongs in `plugins/workflows/`.
- Shared schemas live in `domain/`.
- Central model/provider integrations belong in `backend/models/`.

