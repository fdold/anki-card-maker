# anki-card-maker

Modulare Python-Anwendung zur Umwandlung von Dokumenten in Anki-kompatible Lernkarten.

## Projektstruktur

- `frontend/` UI-Platzhalter fuer spaetere Review- und Plugin-Auswahl
- `backend/` API, Services, Pipeline, Parser, Exporter, Storage, Model-Integrationen
- `domain/` gemeinsame Pydantic-Domain-Modelle
- `plugins/` Workflow- und Helper-Plugins
- `tests/` Unit-, Integrations-, API- und E2E-Tests
- `docker/` Dockerfiles
- `docs/` Architektur- und Plugin-Dokumentation

## Schnellstart

```bash
docker compose up --build
```

API-Endpunkte:

- `GET /health`
- `GET /overview`

## Entwicklungsstand

Das Repository enthaelt jetzt ein sauberes Grundgeruest mit:

- FastAPI-Startpunkt
- zentralen Domain-Modellen
- TXT-Parser als erste stabile Eingabeform
- erstem Workflow-Plugin-Grundgeruest
- CSV-Exporter fuer fruehe Anki-Kompatibilitaet
- Basis-Tests fuer Parser, Workflow und Export
