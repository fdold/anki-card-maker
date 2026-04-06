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

Danach stehen Backend und eine Web-UI direkt bereit.
Ollama wird im Compose-Setup nun in einem eigenen Container gestartet.
Ein einmaliger Init-Service zieht beim Compose-Start automatisch alle in
`docker/model_profiles.dev.json` konfigurierten Ollama-Modelle fuer
`ollama-default`, bevor das Backend startet.

Das Development-Backend liest seine Model-Profile aus
`docker/model_profiles.dev.json`. Standardmaessig sind dort aktuell die Profile
`ollama_generation_default` und `ollama_improvement_default` fuer
`qwen3:8b` hinterlegt.
Beim ersten Start kann dieser Schritt deutlich laenger dauern, weil das Modell
zuerst heruntergeladen wird. Den Fortschritt kannst du bei Bedarf mitverfolgen:

```bash
docker compose logs -f ollama-init
```

Der `ollama-init`-Service gibt dabei Status- und Fortschrittszeilen aus, waehrend
das Modell geladen wird.
Während längerer Ollama-Generierungen loggen Backend und Workflow jetzt zudem
den Start der Anfrage, den aktuellen Dokument-/Block-Status und den Abschluss
der Modellantwort.

Web-UI im Browser:

```bash
open http://localhost:8501
```

Die Web-UI nutzt denselben Frontend-API-Client wie die CLI und deckt die vorhandenen FastAPI-Aktionen fuer Uploads, Run-Erstellung, Kartenansicht, Improvements und Exporte ab.

TXT-Workflow per CLI testen:

```bash
python -m frontend.cli generate path/to/notes.txt --plugin-id basic_text_workflow --csv-output cards.csv
```

Nach Installation funktioniert auch der Konsolenbefehl:

```bash
anki-card-maker generate path/to/notes.txt --api-url http://localhost:8000 --plugin-id basic_text_workflow
```

Die CLI liegt im `frontend/` und spricht nur mit dem Backend-API-Endpoint.
Parserwahl, TXT-Segmentierung, Workflow-Ausfuehrung und Export liegen im Backend.
Die Browser-UI laeuft ebenfalls im `frontend/` und spricht ueber einen kleinen Frontend-Proxy mit denselben Backend-Ressourcen.
Die CLI nutzt intern jetzt denselben Ressourcen-Flow wie die API:
Dokument hochladen, Run erzeugen, Export erstellen und Ergebnis herunterladen.
Der alte Kurzaufruf `anki-card-maker path/to/file.txt` bleibt als Abkuerzung fuer `generate` erhalten.

Wichtige CLI-Befehle:

```bash
anki-card-maker overview
anki-card-maker upload path/to/notes.txt
anki-card-maker documents
anki-card-maker document <document-id>
anki-card-maker create-run <document-id> --plugin basic_text_workflow
anki-card-maker runs
anki-card-maker run <run-id>
anki-card-maker cards <run-id>
anki-card-maker improve <run-id> --action rate_run --rating good
anki-card-maker improve <run-id> --action prompt_refine_selected --target-card-id <card-id> --prompt "Keep it a question"
anki-card-maker improvements <run-id>
anki-card-maker create-export <run-id> --exporter csv
anki-card-maker export <export-id>
anki-card-maker download-export <export-id> --output cards.csv
anki-card-maker generate path/to/notes.txt --csv-output cards.csv
```

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
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "biology.txt",
    "content": "Cells are the basic unit of life.\n\nDNA stores genetic information."
  }'
```

Anschliessend einen Run erzeugen:

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["<document-id>"],
    "workflow_plugin_id": "basic_text_workflow",
    "workflow_config": {
      "max_cards": 10
    }
  }'
```

Und den Export erstellen:

```bash
curl -X POST http://localhost:8000/runs/<run-id>/exports \
  -H "Content-Type: application/json" \
  -d '{
    "exporter_id": "csv"
  }'
```

API-Endpunkte:

- `GET /health`
- `GET /overview`
- `POST /documents`
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /runs`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/cards`
- `POST /runs/{run_id}/exports`
- `GET /exports/{export_id}`
- `GET /exports/{export_id}/download`

Der Endpoint `GET /overview` zeigt jetzt auch die geladenen
`available_model_profiles`, sofern das Backend mit einer Model-Profile-Datei
konfiguriert wurde.

## Docker Test Flow

Beispieltexte liegen in `test-data/samples/`.
CSV-Exporte kannst du in `test-data/exports/` ablegen.

Alles starten:

```bash
docker compose up --build
```

Falls du pruefen willst, welche Modelle nach dem Init verfuegbar sind:

```bash
docker compose exec ollama-default ollama list
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

Browser-UI im Compose-Setup:

```bash
open http://localhost:8501
```

Dort koennen Dokumente hochgeladen, Runs erzeugt, Improvements angewendet und CSV-Exporte erstellt sowie heruntergeladen werden.
Wenn eine Ollama-Generierung länger dauert, sind die hilfreichsten Logs meist:

```bash
docker compose logs -f backend ollama-default
```

## Current Status

The repository now contains a clean initial foundation with:

- FastAPI entry point
- centralized domain models
- TXT parser as the first stable input format
- first workflow plugin scaffold
- run-based document generation and card review foundation
- workflow-driven and generic card improvement operations
- exporter-based CSV flow for early Anki compatibility
- baseline tests for parser, workflow, review, and export
