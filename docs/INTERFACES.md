# Interfaces

This document defines the project-owned interface contracts used to keep implementation changes and test validation aligned with `docs/requirements/REQUIREMENTS.md`.

`docs/requirements/REQUIREMENTS.md` remains the source of truth. When an interface changes because product behavior, architecture, configuration, persistence, or external integration behavior changes, update the relevant requirement first, then update this file, then update implementation and tests.

## Interface Status

- `implemented`: Present in the current codebase and covered by existing modules.
- `planned`: Required by active requirements but not yet implemented.
- `test-double-required`: Concrete external behavior must be replaceable by fake, stub, or in-memory implementations for tests.

## Contract Rules

- Interface contracts must use domain-compatible models from `domain.models` or API schemas from `backend.api.schemas` unless a requirement explicitly introduces a new model.
- Internal logic must depend on project-owned interfaces instead of concrete external providers.
- Side-effecting or non-deterministic behavior must be injectable, persistable where needed, and testable with controlled fake implementations.
- Resource API tests should validate request schema, success, not-found, invalid-state, and unsupported-provider paths.

Related requirements: `REQ-ARCH-004`, `REQ-ARCH-005`, `REQ-TEST-001`, `REQ-TEST-003`, `REQ-TEST-004`, `REQ-TEST-006`, `REQ-DOC-001`.

## HTTP Resource API

Base API module: `backend.api.main`

Schema module: `backend.api.schemas`

### IF-HTTP-001 Health

Status: `implemented`

Requirements: `REQ-API-001`

| Method | Path | Request | Success response | Errors |
| --- | --- | --- | --- | --- |
| `GET` | `/health` | none | `{"status": "ok"}` | none expected |

### IF-HTTP-002 Application Overview

Status: `implemented`

Requirements: `REQ-WF-004`, `REQ-API-001`

| Method | Path | Request | Success response | Errors |
| --- | --- | --- | --- | --- |
| `GET` | `/overview` | none | Object with `active_workflow_example`, `supported_input_formats`, `available_workflow_plugins`, `available_exporters`, `export_targets`, and `api_resources` | none expected |

The overview response is the discovery contract for workflow manifests, exporter definitions, and available resource paths.

### IF-HTTP-003 Documents

Status: `implemented`

Requirements: `REQ-PARSE-001`, `REQ-PARSE-003`, `REQ-API-001`, `REQ-STORAGE-001`

| Method | Path | Request | Success response | Errors |
| --- | --- | --- | --- | --- |
| `POST` | `/documents` | `UploadDocumentRequest` | `201 DocumentDetailResponse` | `400` for unsupported or invalid source input |
| `GET` | `/documents` | none | `list[DocumentSummaryResponse]` | none expected |
| `GET` | `/documents/{document_id}` | path `document_id` | `DocumentDetailResponse` | `404` for unknown document |

`UploadDocumentRequest` fields:

| Field | Type | Required | Validation |
| --- | --- | --- | --- |
| `filename` | `str` | yes | minimum length 1 |
| `content` | `str` | yes | may be empty; empty parsed TXT yields warnings |
| `source_type` | `str | null` | no | defaults from filename extension |
| `title` | `str | null` | no | defaults from filename stem |
| `document_id` | `str | null` | no | generated when omitted |

`DocumentSummaryResponse` fields: `document_id`, `filename`, `title`, `source_type`, `created_at`, `block_count`, `warnings`.

`DocumentDetailResponse` extends `DocumentSummaryResponse` with `has_parsed_content`.

### IF-HTTP-004 Runs

Status: `implemented`

Requirements: `REQ-WF-001`, `REQ-WF-002`, `REQ-GEN-001`, `REQ-API-001`, `REQ-STORAGE-001`

| Method | Path | Request | Success response | Errors |
| --- | --- | --- | --- | --- |
| `POST` | `/runs` | `CreateRunRequest` | `201 RunDetailResponse` | `400` for empty documents, unknown documents, unsupported workflow, invalid workflow config, or missing parsed content |
| `GET` | `/runs` | none | `list[RunSummaryResponse]` | none expected |
| `GET` | `/runs/{run_id}` | path `run_id` | `RunDetailResponse` | `404` for unknown run |
| `GET` | `/runs/{run_id}/cards` | path `run_id` | `list[RunCardResponse]` | `404` for unknown run |

`CreateRunRequest` fields:

| Field | Type | Required | Validation |
| --- | --- | --- | --- |
| `document_ids` | `list[str]` | yes | minimum length 1 |
| `workflow_plugin_id` | `str` | yes | minimum length 1; must resolve to a workflow plugin |
| `workflow_config` | `dict[str, object]` | no | validated by selected workflow plugin config model |

`RunSummaryResponse` fields: `run_id`, `plugin_id`, `document_ids`, `status`, `workflow_config`, `warnings`, `card_count`, `created_at`, `updated_at`, `completed_at`.

`RunDetailResponse` extends `RunSummaryResponse` with `document_id`.

`RunCardResponse` fields: `card_id`, `run_id`, `front`, `back`, `source`, `tags`, `workflow_plugin_id`, `original_front`, `original_back`, `status`, `rating`, `created_at`, `updated_at`.

### IF-HTTP-005 Improvements

Status: `implemented`

Requirements: `REQ-IMPROVE-001`, `REQ-IMPROVE-002`, `REQ-API-001`

| Method | Path | Request | Success response | Errors |
| --- | --- | --- | --- | --- |
| `POST` | `/runs/{run_id}/improvements` | `ApplyImprovementsRequest` | `RunDetailResponse` | `400` for unknown run, unsupported action, invalid action payload, unknown card, or unsupported plugin refinement |
| `GET` | `/runs/{run_id}/improvements` | path `run_id` | `list[ImprovementRecordResponse]` | `404` for unknown run |

`ApplyImprovementsRequest` fields:

| Field | Type | Required | Validation |
| --- | --- | --- | --- |
| `actions` | `list[ImprovementActionRequest]` | no | defaults to empty list |

`ImprovementActionRequest` fields:

| Field | Type | Applies to |
| --- | --- | --- |
| `action_type` | `str` | all actions; must map to `ImprovementActionType` |
| `card_id` | `str | null` | `edit_card`, `delete_card`, `rate_card`, optional single target for `prompt_refine_selected` |
| `card_ids` | `list[str]` | multi-card target for `prompt_refine_selected` |
| `front` | `str | null` | optional replacement for `edit_card` |
| `back` | `str | null` | optional replacement for `edit_card` |
| `rating` | `str | null` | required for `rate_card` and `rate_run`; values `good`, `mixed`, `bad` |
| `prompt` | `str | null` | required for `prompt_refine_selected` and `prompt_refine_all` |

Supported action values: `edit_card`, `delete_card`, `rate_card`, `rate_run`, `prompt_refine_selected`, `prompt_refine_all`.

`ImprovementRecordResponse` fields: `record_id`, `run_id`, `action_type`, `card_id`, `applied_at`, `summary`.

### IF-HTTP-006 Exports

Status: `implemented`

Requirements: `REQ-EXPORT-001`, `REQ-EXPORT-002`, `REQ-API-001`, `REQ-STORAGE-001`

| Method | Path | Request | Success response | Errors |
| --- | --- | --- | --- | --- |
| `POST` | `/runs/{run_id}/exports` | `CreateExportRequest` | `201 ExportResponse` | `400` for unknown run, unsupported exporter, or non-exportable selected card |
| `GET` | `/exports/{export_id}` | path `export_id` | `ExportResponse` | `404` for unknown export |
| `GET` | `/exports/{export_id}/download` | path `export_id` | raw artifact content with artifact `media_type` and `Content-Disposition` filename | `404` for unknown export |

`CreateExportRequest` fields:

| Field | Type | Required | Validation |
| --- | --- | --- | --- |
| `exporter_id` | `str` | yes | minimum length 1; must resolve to an exporter |
| `card_ids` | `list[str]` | no | empty means all non-deleted run cards |

`ExportResponse` fields: `export_id`, `run_id`, `exporter_id`, `card_ids`, `filename`, `media_type`, `status`, `created_at`, `completed_at`, `card_count`.

### IF-HTTP-007 Legacy Endpoint Exclusion

Status: `implemented`

Requirements: `REQ-API-002`

The backend API must not expose a legacy one-shot document generation endpoint. Clients must use the resource flow: upload document, create run, inspect cards or improvements, create export, download export.

## Frontend Proxy API

Module: `frontend.web`

Status: `implemented`

Requirements: `REQ-FRONTEND-002`

The browser frontend exposes proxy routes under `/api/*` that delegate to the backend resource API through `frontend.api_client`.

| Frontend route | Backend interface |
| --- | --- |
| `GET /api/health` | `GET /health` |
| `GET /api/overview` | `GET /overview` |
| `GET /api/documents` | `GET /documents` |
| `POST /api/documents` | `POST /documents` |
| `GET /api/documents/{document_id}` | `GET /documents/{document_id}` |
| `GET /api/runs` | `GET /runs` |
| `POST /api/runs` | `POST /runs` |
| `GET /api/runs/{run_id}` | `GET /runs/{run_id}` |
| `GET /api/runs/{run_id}/cards` | `GET /runs/{run_id}/cards` |
| `GET /api/runs/{run_id}/improvements` | `GET /runs/{run_id}/improvements` |
| `POST /api/runs/{run_id}/improvements` | `POST /runs/{run_id}/improvements` |
| `POST /api/runs/{run_id}/exports` | `POST /runs/{run_id}/exports` |
| `GET /api/exports/{export_id}` | `GET /exports/{export_id}` |
| `GET /api/exports/{export_id}/download` | `GET /exports/{export_id}/download` |

Proxy error behavior:

- Backend JSON error details should be reduced to the backend `detail` value when present.
- Backend HTTP status codes should be preserved when available.
- Backend reachability failures should be exposed as `502`.
- Invalid proxy JSON request bodies should return `400`.

## Frontend API Client

Module: `frontend.api_client`

Status: `implemented`

Requirements: `REQ-FRONTEND-001`, `REQ-FRONTEND-002`

The frontend API client is the Python client contract for CLI and web proxy code.

| Function | Contract |
| --- | --- |
| `get_health(api_base_url)` | Returns backend health dict. |
| `get_overview(api_base_url)` | Returns discovery overview dict. |
| `upload_document(api_base_url, payload)` | Calls `POST /documents`; returns document dict. |
| `list_documents(api_base_url)` | Calls `GET /documents`; returns document list. |
| `get_document(api_base_url, document_id)` | Calls `GET /documents/{document_id}`. |
| `create_run(api_base_url, payload)` | Calls `POST /runs`; returns run dict. |
| `list_runs(api_base_url)` | Calls `GET /runs`; returns run list. |
| `get_run(api_base_url, run_id)` | Calls `GET /runs/{run_id}`. |
| `list_run_cards(api_base_url, run_id)` | Calls `GET /runs/{run_id}/cards`. |
| `apply_improvements(api_base_url, run_id, payload)` | Calls `POST /runs/{run_id}/improvements`. |
| `list_improvements(api_base_url, run_id)` | Calls `GET /runs/{run_id}/improvements`. |
| `create_export(api_base_url, run_id, payload)` | Calls `POST /runs/{run_id}/exports`. |
| `get_export(api_base_url, export_id)` | Calls `GET /exports/{export_id}`. |
| `download_export(api_base_url, export_id, media_type="text/csv")` | Calls `GET /exports/{export_id}/download`; returns text content. |
| `generate_cards_from_document(api_base_url, payload)` | Compatibility client flow that uploads a document, creates a run, creates a CSV export, and downloads CSV content. |

Client errors must raise `ApiClientError` with message, optional `status_code`, and optional raw `details`.

## Domain Model Interfaces

Module: `domain.models`

Status: `implemented`

Requirements: `REQ-DOMAIN-001`, `REQ-DOMAIN-002`, `REQ-CARD-001`, `REQ-TRACE-001`

Domain models are the stable in-process contract across services, plugins, parsers, exporters, repositories, and API builders.

| Model | Purpose |
| --- | --- |
| `SourceReference` | Optional page, section, chapter, and position provenance. |
| `Document` | Normalized document identity, title, and source type. |
| `TextBlock` | Ordered parsed text plus source reference. |
| `ParsedContent` | Document plus parsed text blocks and warnings. |
| `StoredDocument` | Uploaded source content, parsed content, metadata, and creation time. |
| `PluginManifest` | Discoverable plugin metadata and configuration schema. |
| `CardCandidate` | Plugin-produced card before it is attached to a run. |
| `RunCard` | Persisted card state with original/current content, status, rating, tags, source, and timestamps. |
| `ImprovementAction` | Domain representation of a requested card/run improvement. |
| `ImprovementBatch` | Run-scoped list of improvement actions. |
| `ImprovementRecord` | Auditable applied improvement history item. |
| `WorkflowImprovementRequest` | Plugin refinement request containing selected cards and prompt. |
| `ExportableAnkiCard` | Exporter input containing front, back, and tags only. |
| `ExportArtifact` | Stored export metadata and content. |
| `GenerationRun` | Run state, selected plugin, document ids, cards, warnings, and improvement history. |

Literal values:

| Alias | Values |
| --- | --- |
| `CardStatus` | `active`, `edited`, `deleted`, `accepted`, `rejected` |
| `CardRating` | `good`, `mixed`, `bad` |
| `RunStatus` | `pending`, `running`, `completed`, `failed` |
| `ExportStatus` | `pending`, `completed`, `failed` |
| `ImprovementActionType` | `edit_card`, `delete_card`, `rate_card`, `rate_run`, `prompt_refine_selected`, `prompt_refine_all` |

## Workflow Plugin Interface

Module: `plugins.base`

Status: `implemented`; graph-capable extensions are `planned`

Requirements: `REQ-WF-001`, `REQ-WF-002`, `REQ-WF-003`, `REQ-WF-004`, `REQ-WF-005`, `REQ-WF-006`, `REQ-WF-007`, `REQ-RUNTIME-001`, `REQ-RUNTIME-002`, `REQ-RUNTIME-008`

Current abstract interface:

```python
class WorkflowPlugin(Generic[WorkflowPluginConfigT]):
    base_manifest: PluginManifest
    config_model: type[WorkflowPluginConfigT]

    @property
    def manifest(self) -> PluginManifest: ...

    def generate_cards(
        self,
        parsed_content: ParsedContent,
        config: WorkflowPluginConfigT,
    ) -> list[CardCandidate]: ...

    def apply_improvement(
        self,
        request: WorkflowImprovementRequest,
        config: WorkflowPluginConfigT,
    ) -> list[RunCard]: ...
```

Contract:

- `manifest` must include plugin id, name, plugin type, description, supported input types, supported operations, and JSON schema from `config_model`.
- `config_model` must validate plugin-specific workflow configuration.
- `generate_cards` must return domain-compatible `CardCandidate` objects with source references and `workflow_plugin_id`.
- Plugin prompts must live inside plugin structures.
- `apply_improvement` may reject unsupported operations with a clear error.
- A generation run must execute exactly one selected workflow plugin.

Planned graph-capable workflow plugin contracts:

- Define named workflow operations, transitions, conditional routing, and supported operations.
- Accept a project-owned runtime context containing injected external interfaces.
- Emit project-owned runtime events rather than LangGraph-native event objects.
- Represent user-assisted extraction as resumable runtime interruptions.

## Parser Interface

Module: `backend.pipeline.parsers.txt_parser`

Status: `implemented` for TXT; workflow-owned extraction/parsing is `planned`

Requirements: `REQ-PARSE-001`, `REQ-PARSE-002`, `REQ-PARSE-003`, `REQ-WF-005`, `REQ-GEN-001`

Current TXT parser contract:

```python
def parse_txt_document(document_id: str, title: str, text: str) -> ParsedContent: ...
```

Contract:

- Return `ParsedContent` with a `Document(source_type="txt")`.
- Split meaningful text into ordered `TextBlock` entries.
- Preserve `SourceReference(section=title or "Document", position=index)`.
- Return a warning when input text is empty after trimming.

Planned workflow-owned parsing contract:

- Source-file extraction and parsing must move behind selected workflow plugin execution or its runtime layer.
- Unsupported source types must be rejected by the selected workflow plugin or orchestration layer.
- User-assisted extraction requests must be explicit, serializable, and resumable.

## Exporter Interface

Module: `backend.services.registry.ExporterDefinition`

Status: `implemented`

Requirements: `REQ-EXPORT-001`, `REQ-EXPORT-002`

Current exporter definition:

```python
@dataclass(frozen=True, slots=True)
class ExporterDefinition:
    exporter_id: str
    media_type: str
    file_extension: str
    export: Callable[[list[ExportableAnkiCard]], str]
```

Contract:

- Exporters receive only `list[ExportableAnkiCard]`.
- Default Anki CSV export includes `front`, `back`, and `tags`.
- Default Anki exports do not include source references.
- Export services must exclude deleted cards and reject selected card ids that are not exportable.

Implemented exporter:

| Exporter id | Media type | Extension | Function |
| --- | --- | --- | --- |
| `csv` | `text/csv` | `csv` | `backend.exporters.csv_exporter.export_cards_to_csv` |

## Repository Interfaces

Modules: `backend.storage.document_repository`, `backend.storage.run_repository`, `backend.storage.export_repository`

Status: `implemented`; persistent storage variants are `planned`

Requirements: `REQ-STORAGE-001`, `REQ-TEST-004`

Current in-memory repository contracts:

| Repository | Methods | Stored model |
| --- | --- | --- |
| `InMemoryDocumentRepository` | `save(document)`, `get(document_id)`, `list()`, `update(document)` | `StoredDocument` |
| `InMemoryRunRepository` | `save(run)`, `get(run_id)`, `list()`, `update(run)` | `GenerationRun` |
| `InMemoryExportRepository` | `save(export_artifact)`, `get(export_id)`, `list()` | `ExportArtifact` |

Contract:

- `get` returns the stored model or `None` for missing ids.
- `list` returns stored models.
- `update` must reject unknown ids where the repository supports updates.
- Repositories are the persistence boundary for uploaded documents, generation runs, and export artifacts.
- Future persistent repositories must preserve these behavioral contracts and be replaceable with in-memory fakes in tests.

## Registry Interface

Module: `backend.services.registry`

Status: `implemented`; dynamic registration is `planned`

Requirements: `REQ-WF-004`, `REQ-API-001`, `REQ-ERROR-001`

| Function | Contract |
| --- | --- |
| `list_workflow_plugins()` | Returns available workflow plugin instances. |
| `get_workflow_plugin(plugin_id)` | Returns matching workflow plugin or raises `ValueError`. |
| `list_exporters()` | Returns available exporter definitions. |
| `get_exporter(exporter_id)` | Returns matching exporter definition or raises `ValueError`. |
| `get_parser_for_source_type(source_type)` | Returns matching parser callable or raises `ValueError`. |
| `create_application_overview()` | Returns API discovery data for overview responses. |

Registry lookup failures should remain debuggable and must not leak concrete provider details into domain models.

## Service Interfaces

Modules: `backend.services.*`

Status: `implemented`

Requirements: `REQ-API-001`, `REQ-DOMAIN-002`, `REQ-STORAGE-001`, `REQ-ERROR-001`

| Service | Public methods | Contract |
| --- | --- | --- |
| `DocumentService` | `upload_document`, `get_document`, `list_documents` | Stores uploaded documents and parsed content. |
| `RunService` | `create_run`, `get_run`, `list_runs` | Validates documents and workflow config, executes selected workflow, stores completed runs. |
| `ImprovementService` | `apply_improvements` | Applies generic card/run improvements and workflow-driven prompt refinements. |
| `ExportService` | `create_export`, `get_export` | Creates and stores export artifacts from non-deleted cards. |

Service errors currently use `ValueError` for invalid inputs and unsupported state; API routes translate those failures into HTTP errors.

## Workflow Runtime Interface

Status: `planned`, `test-double-required`

Requirements: `REQ-RUNTIME-001` through `REQ-RUNTIME-010`, `REQ-TEST-010`, `REQ-TRACE-003`

The project-owned workflow runtime interface is the boundary between services/plugins and LangGraph or any future workflow engine.

Planned contract:

- Execute one selected workflow plugin per generation run.
- Accept serializable workflow state with schema version.
- Support graph construction, named operations, transitions, and conditional routing.
- Support checkpointed pause, resume, retry, recovery, and state invalidation or migration.
- Translate user-assisted workflow steps into explicit interaction requests.
- Emit normalized project-owned events for operation start/completion, state updates, information graph deltas, card candidates, interaction requests, failures, and run completion.
- Categorize failures as extraction, parsing, plugin, model, validation, export, recoverable runtime, or terminal runtime failures.
- Keep LangGraph-specific objects out of backend API schemas, domain models, and frontend contracts.

Expected test doubles:

- In-memory runtime for deterministic operation execution.
- Fake checkpoint store.
- Fake event sink.
- Fake user-interaction responder.

## Information Graph Interface

Status: `planned`

Requirements: `REQ-TRACE-002`, `REQ-TRACE-003`, `REQ-TRACE-004`, `REQ-TRACE-005`, `REQ-TRACE-006`, `REQ-TRACE-007`, `REQ-RUNTIME-007`

The information graph is the user-facing representation of extracted content, relationships, source references, and workflow changes. It is separate from the workflow execution graph.

Planned contract:

- Persist graph nodes for extracted blocks and nested extracted information.
- Persist graph edges for hierarchy and relationships.
- Include source references and optional highlighted portions on terminal text nodes.
- Expose state updates through backend API interfaces for live frontend observation.
- Let the browser frontend render a selectable mind-map-like view.
- Selecting a non-terminal node navigates deeper; selecting a terminal node opens detail text with source references.

## External Capability Interfaces

Status: `planned`, `test-double-required`

Requirements: `REQ-ARCH-004`, `REQ-ARCH-005`, `REQ-RUNTIME-008`, `REQ-RUNTIME-009`, `REQ-TEST-001`, `REQ-TEST-003`, `REQ-TEST-004`

All external functionality used by workflow operations must be accessed through project-owned interfaces injected into runtime context or services.

Planned interface families:

| Capability | Interface purpose | Test double expectation |
| --- | --- | --- |
| LLM/model providers | Generate or refine structured content from prompts and inputs. | Deterministic fake model responses. |
| OCR/image extraction | Extract text or structure from images or PDFs. | Fixture-backed fake extraction results and failures. |
| Embedding/vector search | Produce embeddings and retrieve related content. | Deterministic fake vectors and search results. |
| Feature extraction | Compute workflow-selected features from source content. | Fixture-backed feature outputs. |
| Clustering/regression/ML | Run model-based analysis steps. | Controlled fake predictions and errors. |
| Network clients | Access remote services. | Fake client with scripted responses and failures. |
| Time/randomness/id generation | Provide non-deterministic values. | Controlled clock, random, and id providers. |
| Checkpoint/event stores | Persist workflow state and events. | In-memory stores. |

External interfaces must define structured inputs, structured outputs, error categories, retry behavior where relevant, and idempotency expectations for durable execution.

## Test Validation Checklist

Use this checklist when changing an interface:

- Identify the relevant `REQ-*` ids before implementation.
- Update `docs/requirements/REQUIREMENTS.md` first when behavior or architecture changes.
- Update this file when request/response shapes, model fields, plugin methods, repository methods, exporter behavior, runtime events, or external capability boundaries change.
- Add or update unit tests for changed core behavior.
- Add or update resource API tests for endpoint contract changes.
- Add or update fake, stub, or in-memory implementations for each external interface.
- Verify unsupported inputs and invalid states fail through the documented error path.
- Verify Docker and Docker Compose workflows still start the documented surfaces.
