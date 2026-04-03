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

Danach stehen Backend und ein CLI-Container direkt bereit.

TXT-Workflow per CLI testen:

```bash
python -m frontend.cli path/to/notes.txt --plugin-id basic_text_workflow --csv-output cards.csv
```

Nach Installation funktioniert auch der Konsolenbefehl:

```bash
anki-card-maker path/to/notes.txt --api-url http://localhost:8000 --plugin-id basic_text_workflow
```

Die CLI liegt im `frontend/` und spricht nur mit dem Backend-API-Endpoint. Parserwahl, TXT-Segmentierung und Workflow-Ausfuehrung liegen im Backend.
Der CSV-Export wird vollstaendig im Backend erzeugt und von der API direkt zurueckgegeben.

## Local Testing

Die lokale Testumgebung nutzt die Projekt-`.venv`. Damit Tests nicht von einem globalen Python abhaengen, verwende:

```bash
make test
```

Nur die Unit-Tests:

```bash
make test-unit
```

Falls die virtuelle Umgebung bereits existiert, aber die Dev-Abhaengigkeiten fehlen:

```bash
make install-dev
```

Dokumente direkt ueber die API im Container verarbeiten:

```bash
curl -X POST http://localhost:8000/generate/document \
  -H "Content-Type: application/json" \
  -H "Accept: text/csv" \
  -d '{
    "filename": "biology.txt",
    "content": "Cells are the basic unit of life.\n\nDNA stores genetic information.",
    "workflow_plugin_id": "basic_text_workflow",
    "workflow_config": {
      "max_cards": 10
    }
  }' -o biology.csv
```

API-Endpunkte:

- `GET /health`
- `GET /overview`
- `POST /generate/document`

## Docker Test Flow

Beispieltexte liegen in `test-data/samples/`.
CSV-Exporte kannst du in `test-data/exports/` ablegen.

Alles starten:

```bash
docker compose up --build
```

Dann die CLI direkt im Frontend-Container verwenden:

```bash
docker compose exec frontend anki-card-maker \
  /app/test-data/samples/biology_basics.txt \
  --api-url http://backend:8000 \
  --plugin basic_text_workflow \
  --output-type csv \
  --csv-output /app/test-data/exports/biology_basics.csv
```

Export pruefen:

```bash
cat test-data/exports/biology_basics.csv
```

## Current Status

The repository now contains a clean initial foundation with:

- FastAPI entry point
- centralized domain models
- TXT parser as the first stable input format
- first workflow plugin scaffold
- CSV exporter for early Anki compatibility
- baseline tests for parser, workflow, and export
