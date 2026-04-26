# Requirements

Prompt classification for this initialization: new requirement, project context only.
Prompt classification for the latest update: new architectural requirements for LangGraph-backed workflow plugin execution.

Sources reviewed:
- `prompt-001`: User request to initialize a requirements file for the current project.
- `doc-agents-001`: `AGENTS.md`
- `doc-readme-001`: `README.md`
- `doc-architecture-001`: `docs/architecture.md`
- `doc-plugins-001`: `docs/plugins.md`
- `doc-frontend-001`: `frontend/README.md`
- `code-domain-001`: `domain/models.py`
- `code-plugins-001`: `plugins/base.py`
- `code-basic-workflow-001`: `plugins/workflows/basic_text_workflow.py`
- `test-index-001`: current `tests/unit/test_*.py` selectors reviewed during initialization
- `prompt-002`: User request to integrate the parsing process into workflow plugins.
- `prompt-003`: User request to make extraction/parsing dynamic inside workflow plugins and optionally involve the user during extraction.
- `prompt-004`: User request to make workflow-plugin information changes traceable in the web interface through a mind-map-like dynamic information filesystem.
- `prompt-005`: User request to model all external functionality accessed by the system as interfaces so external functionality and internal logic remain separated and internal logic can be tested without external sources.
- `prompt-006`: User request that the web interface can be designed in Figma to allow simple prototyping.
- `prompt-007`: User request to add additional requirements for effective tests.
- `prompt-008`: User request to create requirements that allow a smooth LangGraph integration for dynamic workflow plugins, model orchestration, feature extraction, user interaction, and external model integration.
- `langgraph-doc-001`: LangGraph overview documentation describing LangGraph as a low-level orchestration framework and runtime for long-running, stateful workflows with durable execution, streaming, and human-in-the-loop support.
- `langgraph-doc-002`: LangGraph durable execution documentation describing checkpointed pause, resume, recovery, and deterministic/idempotent workflow design.
- `langgraph-doc-003`: LangGraph interrupt reference describing resumable graph interruptions for human-in-the-loop workflows.

## REQ-ARCH-001

```yaml
id: REQ-ARCH-001
status: active
type: constraint
parent: null
children: []
statement: The project SHALL be implemented in Python.
rationale: The project hard constraints define Python as the implementation language.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-ARCH-002

```yaml
id: REQ-ARCH-002
status: active
type: constraint
parent: null
children: []
statement: The project SHALL run in Docker Compose.
rationale: Docker-based reproducibility is a primary project constraint.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-readme-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-ARCH-003

```yaml
id: REQ-ARCH-003
status: active
type: constraint
parent: null
children: []
statement: The project SHALL keep frontend, backend, domain, plugin, test, Docker, and documentation modules separated.
rationale: The architecture requires clear module boundaries for maintainability and extensibility.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-readme-001
    confidence: high
  - kind: doc
    ref: doc-architecture-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-ARCH-004

```yaml
id: REQ-ARCH-004
status: active
type: interface
parent: null
children: []
statement: All external functionality accessed by the system SHALL be represented behind explicit interfaces.
rationale: Explicit interfaces create a uniform boundary between external dependencies and internal logic.
source:
  - kind: prompt
    ref: prompt-005
    confidence: high
tests: []
conflicts_with: []
```

## REQ-ARCH-005

```yaml
id: REQ-ARCH-005
status: active
type: constraint
parent: null
children: []
statement: Internal logic SHALL depend on external functionality through the explicit interfaces rather than concrete external implementations.
rationale: Interface-based dependencies keep internal behavior isolated from external implementation details.
source:
  - kind: prompt
    ref: prompt-005
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-001

```yaml
id: REQ-TEST-001
status: active
type: non-functional
parent: null
children: []
statement: Internal logic tests SHALL be able to run with fake or in-memory implementations of external interfaces without accessing external sources.
rationale: Tests for internal logic must remain deterministic and independent from external systems.
source:
  - kind: prompt
    ref: prompt-005
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-002

```yaml
id: REQ-TEST-002
status: active
type: non-functional
parent: null
children: []
statement: Core domain, parsing, workflow, improvement, export, and storage logic SHALL be covered by automated unit tests.
rationale: Core behavior should be verifiable without relying on manual checks or full application startup.
source:
  - kind: prompt
    ref: prompt-007
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-003

```yaml
id: REQ-TEST-003
status: active
type: non-functional
parent: null
children: []
statement: Automated tests for internal logic SHALL use controlled inputs for time, randomness, model responses, network clients, and external service responses.
rationale: The test suite must produce stable results across local, Docker, and CI environments.
source:
  - kind: prompt
    ref: prompt-007
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-004

```yaml
id: REQ-TEST-004
status: active
type: non-functional
parent: null
children: []
statement: Each external interface SHALL provide at least one fake, stub, or in-memory implementation usable by automated tests.
rationale: Interface boundaries are only useful for testing when replaceable implementations exist.
source:
  - kind: prompt
    ref: prompt-007
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-005

```yaml
id: REQ-TEST-005
status: active
type: non-functional
parent: null
children: []
statement: Each workflow plugin SHALL have automated tests for its manifest, configuration validation, supported input handling, successful execution path, and failure path.
rationale: Plugins are independently selectable execution units and need isolated verification.
source:
  - kind: prompt
    ref: prompt-007
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-006

```yaml
id: REQ-TEST-006
status: active
type: non-functional
parent: null
children: []
statement: Resource API tests SHALL verify request validation, successful responses, not-found responses, and invalid-state responses for each exposed resource.
rationale: The API is the shared contract for frontend, CLI, and external clients.
source:
  - kind: prompt
    ref: prompt-007
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-007

```yaml
id: REQ-TEST-007
status: active
type: non-functional
parent: null
children: []
statement: Export tests SHALL verify generated artifact content, metadata, selected-card filtering, deleted-card exclusion, and unsupported exporter handling.
rationale: Export correctness directly affects Anki import behavior.
source:
  - kind: prompt
    ref: prompt-007
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-008

```yaml
id: REQ-TEST-008
status: active
type: non-functional
parent: null
children: []
statement: Test fixtures SHALL use minimal representative documents, cards, runs, and plugin configurations instead of broad production-like datasets.
rationale: Small fixtures keep failures readable and make behavior-specific tests easier to maintain.
source:
  - kind: prompt
    ref: prompt-007
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-009

```yaml
id: REQ-TEST-009
status: active
type: non-functional
parent: null
children: []
statement: Every active requirement that defines executable behavior SHALL either reference an automated test or explicitly document why automated coverage is not currently feasible.
rationale: Requirement traceability should reveal real coverage gaps instead of hiding them.
source:
  - kind: prompt
    ref: prompt-007
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TEST-010

```yaml
id: REQ-TEST-010
status: active
type: non-functional
parent: null
children: []
statement: Workflow runtime tests SHALL cover graph construction, deterministic state transitions, conditional routing, checkpoint restore, interrupt/resume behavior, normalized event emission, failure categorization, and execution with fake external interfaces.
rationale: LangGraph-backed workflow execution introduces resumable branching behavior that must remain verifiable without relying on live external services.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-001
    confidence: high
  - kind: doc
    ref: langgraph-doc-002
    confidence: high
  - kind: doc
    ref: langgraph-doc-003
    confidence: high
tests: []
conflicts_with: []
```

## REQ-DOMAIN-001

```yaml
id: REQ-DOMAIN-001
status: active
type: functional
parent: null
children: []
statement: The system SHALL define standardized domain models for documents, parsed content, source references, card candidates, run cards, improvement actions, generation runs, and export artifacts.
rationale: Shared models keep plugins, services, API resources, and exporters aligned.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: code
    ref: code-domain-001
    confidence: high
tests:
  - id: TST-DOMAIN-001
    path: tests/unit/test_domain_models.py::test_stored_document_can_embed_parsed_content_metadata
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-DOMAIN-002
    path: tests/unit/test_domain_models.py::test_run_card_tracks_original_and_current_card_content
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-DOMAIN-003
    path: tests/unit/test_domain_models.py::test_generation_run_supports_multiple_documents_and_status_tracking
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-DOMAIN-002

```yaml
id: REQ-DOMAIN-002
status: active
type: constraint
parent: null
children: []
statement: Core document-to-card flows SHALL use standardized domain-compatible structures across workflow-owned extraction, parsing, workflow execution, review, improvement, and export.
rationale: Domain-compatible flow boundaries preserve traceability while allowing the active workflow plugin to own extraction and parsing strategy.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-architecture-001
    confidence: high
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests:
  - id: TST-DOMAIN-004
    path: tests/unit/test_txt_workflow_service.py::test_generate_cards_from_document_input_returns_traceable_cards
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-DOMAIN-005
    path: tests/unit/test_export_service.py::test_export_service_creates_csv_export_from_run_cards
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-PARSE-001

```yaml
id: REQ-PARSE-001
status: active
type: functional
parent: null
children: []
statement: The selected workflow plugin SHALL support TXT as the first stable source document input format.
rationale: TXT remains the earliest stable input format while extraction and parsing responsibility belong to the active workflow plugin.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-readme-001
    confidence: high
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests:
  - id: TST-PARSE-001
    path: tests/unit/test_txt_parser.py::test_parse_txt_document_creates_single_block
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-PARSE-002
    path: tests/unit/test_txt_parser.py::test_parse_txt_document_splits_paragraphs_into_blocks
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-PARSE-003
    path: tests/unit/test_document_service.py::test_document_service_uploads_and_parses_txt_document
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-PARSE-002

```yaml
id: REQ-PARSE-002
status: active
type: functional
parent: null
children: []
statement: The selected workflow plugin SHALL convert TXT input into parsed content with meaningful ordered text blocks and source references.
rationale: Workflow-owned extraction and parsing let each card-generation method choose the extraction strategy while preserving standardized parsed content.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-architecture-001
    confidence: high
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests:
  - id: TST-PARSE-004
    path: tests/unit/test_txt_parser.py::test_parse_txt_document_creates_single_block
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-PARSE-005
    path: tests/unit/test_txt_parser.py::test_parse_txt_document_splits_paragraphs_into_blocks
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-PARSE-003

```yaml
id: REQ-PARSE-003
status: active
type: functional
parent: null
children: []
statement: The selected workflow plugin or its orchestration layer SHALL reject uploaded source files whose file type is not supported by the selected workflow plugin.
rationale: Unsupported inputs must fail clearly while allowing workflow plugins to define their own supported extraction inputs.
source:
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
  - kind: test
    ref: tests/unit/test_document_service.py::test_document_service_rejects_unknown_source_type
    confidence: high
  - kind: test
    ref: tests/unit/test_txt_workflow_service.py::test_generate_cards_from_document_input_rejects_unknown_source_type
    confidence: high
tests:
  - id: TST-PARSE-006
    path: tests/unit/test_document_service.py::test_document_service_rejects_unknown_source_type
    kind: unit
    match: explicit
    coverage: full
  - id: TST-PARSE-007
    path: tests/unit/test_txt_workflow_service.py::test_generate_cards_from_document_input_rejects_unknown_source_type
    kind: unit
    match: explicit
    coverage: full
conflicts_with: []
```

## REQ-WF-001

```yaml
id: REQ-WF-001
status: active
type: functional
parent: null
children: []
statement: Each generation run SHALL execute exactly one selected workflow plugin.
rationale: Workflow plugins are the primary extraction, parsing, and card-generation processing units.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-plugins-001
    confidence: high
  - kind: doc
    ref: doc-architecture-001
    confidence: high
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests:
  - id: TST-WF-001
    path: tests/unit/test_run_service.py::test_run_service_creates_run_from_stored_documents
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-WF-002
    path: tests/unit/test_api_resources.py::test_runs_endpoints_create_run_and_expose_cards
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-WF-002

```yaml
id: REQ-WF-002
status: active
type: interface
parent: null
children: []
statement: Each workflow plugin SHALL define and expose its own validatable configuration schema.
rationale: Plugin-specific configuration preserves extensibility without forcing a central config shape.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: code
    ref: code-plugins-001
    confidence: high
tests:
  - id: TST-WF-003
    path: tests/unit/test_basic_text_workflow.py::test_basic_text_workflow_exposes_its_own_config_schema
    kind: unit
    match: explicit
    coverage: partial
conflicts_with: []
```

## REQ-WF-003

```yaml
id: REQ-WF-003
status: active
type: constraint
parent: null
children: []
statement: Card-generation prompts SHALL exist only inside plugin structures.
rationale: Prompt ownership belongs to plugins so generation methods remain modular and comparable.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-plugins-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-WF-004

```yaml
id: REQ-WF-004
status: active
type: interface
parent: null
children: []
statement: User-selectable workflow plugins SHALL expose manifests that identify plugin id, name, plugin type, description, supported input types, supported operations, extraction capabilities, and configuration schema.
rationale: Manifests let the API and UI discover available card-generation workflows and their supported extraction behavior.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: code
    ref: code-domain-001
    confidence: high
  - kind: code
    ref: code-plugins-001
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests:
  - id: TST-WF-004
    path: tests/unit/test_basic_text_workflow.py::test_basic_text_workflow_exposes_its_own_config_schema
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-WF-005
    path: tests/unit/test_api_resources.py::test_overview_exposes_workflows_exporters_and_api_resources
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-WF-005

```yaml
id: REQ-WF-005
status: active
type: functional
parent: null
children: []
statement: Each workflow plugin SHALL perform source-file extraction and parsing inside its workflow execution rather than through a separate global parsing step.
rationale: Extraction and parsing strategy are part of the selected document-to-card workflow and should vary by plugin without weakening shared domain boundaries.
source:
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests:
  - id: TST-WF-006
    path: tests/unit/test_txt_workflow_service.py::test_generate_cards_from_document_input_uses_parser_segmentation
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-WF-006

```yaml
id: REQ-WF-006
status: active
type: functional
parent: null
children: []
statement: Each workflow plugin SHALL be able to choose dynamically among plugin-defined extraction strategies for a supported uploaded source file.
rationale: Different workflows and file contents may require text extraction, image extraction, machine-learning extraction, user-assisted extraction, or future plugin-defined methods.
source:
  - kind: prompt
    ref: prompt-003
    confidence: high
tests: []
conflicts_with: []
```

## REQ-WF-007

```yaml
id: REQ-WF-007
status: active
type: interface
parent: null
children: []
statement: Workflow plugins SHALL be able to include optional user-assisted extraction requests when plugin-defined automated extraction strategies cannot decode a required portion of a source file.
rationale: Some source content, such as an undecodable image in a PDF, may require the user to provide a description during extraction without making user involvement mandatory for every workflow.
source:
  - kind: prompt
    ref: prompt-003
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-001

```yaml
id: REQ-RUNTIME-001
status: active
type: constraint
parent: null
children: []
statement: Workflow plugin execution SHALL be mediated through a project-owned workflow runtime abstraction, with LangGraph supported as the primary runtime implementation for graph-based workflow execution.
rationale: A project-owned runtime boundary lets workflow plugins use LangGraph's orchestration capabilities without making backend services, API resources, domain models, or tests depend directly on LangGraph internals.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-002

```yaml
id: REQ-RUNTIME-002
status: active
type: interface
parent: null
children: []
statement: Each graph-capable workflow plugin SHALL define its processing as named workflow operations with explicit transitions, conditional routing, and declared supported operations while preserving the rule that each generation run executes exactly one selected workflow plugin.
rationale: Graph-defined operations allow dynamic extraction, parsing, model selection, feature extraction, clustering, regression, validation, and card-generation paths while keeping plugin selection and responsibility clear.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-003

```yaml
id: REQ-RUNTIME-003
status: active
type: interface
parent: null
children: []
statement: Workflow runtime state SHALL be represented by project-owned, serializable, domain-compatible models that include source input references, extracted blocks, parsed content, information graph state or deltas, generated card candidates, operation metadata, errors, and pending user interaction requests when present.
rationale: Project-owned state keeps LangGraph execution compatible with persistence, API responses, tests, exports, and future runtime implementations.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-001
    confidence: high
  - kind: doc
    ref: langgraph-doc-002
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-004

```yaml
id: REQ-RUNTIME-004
status: active
type: non-functional
parent: null
children: []
statement: The workflow runtime SHALL support durable execution for long-running workflow runs, including checkpointed pause, resume, retry, and recovery without losing completed workflow state, source references, generated artifacts, or pending user interaction context.
rationale: Dynamic document-to-card workflows may involve slow model calls, OCR, user assistance, and multi-step processing that must survive interruptions.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-002
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-005

```yaml
id: REQ-RUNTIME-005
status: active
type: interface
parent: null
children: []
statement: User-assisted workflow steps SHALL be represented as explicit resumable workflow interruptions that are translated into backend API interaction requests and can be resumed with structured user responses from the web interface.
rationale: Human-in-the-loop extraction and review must remain observable, persistable, and resumable instead of relying on blocking calls inside workflow logic.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-003
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-006

```yaml
id: REQ-RUNTIME-006
status: active
type: interface
parent: null
children: []
statement: Workflow runtime progress SHALL be exposed through project-owned workflow events that normalize operation start, operation completion, state updates, information graph deltas, generated card candidates, user interaction requests, recoverable failures, terminal failures, and run completion.
rationale: Normalized events let the web interface observe LangGraph-backed workflows without coupling UI behavior to LangGraph event formats.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-007

```yaml
id: REQ-RUNTIME-007
status: active
type: constraint
parent: null
children: []
statement: The system SHALL keep the workflow execution graph separate from the user-facing information graph; execution graph structure may be exposed for debugging, while the information graph remains the canonical user-facing representation of extracted content, relationships, source references, and workflow changes to information.
rationale: LangGraph models process control flow, while the product's mind-map-like information graph models extracted knowledge for users.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-008

```yaml
id: REQ-RUNTIME-008
status: active
type: constraint
parent: null
children: []
statement: Workflow operations that call LLMs, machine-learning models, OCR, feature extraction, clustering, regression, embedding, storage, network, or other external functionality SHALL access those capabilities only through explicit project interfaces injected into the workflow runtime context.
rationale: Runtime graph nodes must remain testable, replaceable, and isolated from concrete external providers while allowing plugins to orchestrate diverse processing methods.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-009

```yaml
id: REQ-RUNTIME-009
status: active
type: non-functional
parent: null
children: []
statement: Workflow graph operations SHALL be designed to be deterministic or idempotent at runtime boundaries, and non-deterministic or side-effecting work SHALL be isolated behind explicit operations whose inputs, outputs, errors, and retry behavior can be persisted and tested.
rationale: Durable workflow resume and retry behavior is reliable only when repeated execution cannot duplicate side effects or silently change completed work.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-002
    confidence: high
tests: []
conflicts_with: []
```

## REQ-RUNTIME-010

```yaml
id: REQ-RUNTIME-010
status: active
type: non-functional
parent: null
children: []
statement: Persisted workflow runtime state SHALL include an explicit schema version and migration or invalidation strategy for paused, checkpointed, or resumable workflow runs.
rationale: Long-running and resumable workflows may outlive code or model changes, so saved state must remain understandable or fail clearly.
source:
  - kind: prompt
    ref: prompt-008
    confidence: high
  - kind: doc
    ref: langgraph-doc-002
    confidence: medium
tests: []
conflicts_with: []
```

## REQ-GEN-001

```yaml
id: REQ-GEN-001
status: active
type: functional
parent: null
children: []
statement: The system SHALL create traceable card candidates from TXT input by having the selected workflow plugin perform extraction, parsing, and card generation.
rationale: The core product value is document-to-Anki-card generation with source linkage.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-architecture-001
    confidence: high
  - kind: code
    ref: code-basic-workflow-001
    confidence: high
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests:
  - id: TST-GEN-001
    path: tests/unit/test_basic_text_workflow.py::test_basic_text_workflow_generates_traceable_cards
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-GEN-002
    path: tests/unit/test_txt_workflow_service.py::test_generate_cards_from_document_input_returns_traceable_cards
    kind: unit
    match: explicit
    coverage: partial
conflicts_with: []
```

## REQ-TRACE-001

```yaml
id: REQ-TRACE-001
status: active
type: functional
parent: null
children: []
statement: Each generated card SHALL preserve a meaningful source reference to the originating source text whenever possible.
rationale: Source traceability is one of the primary product goals.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: code
    ref: code-domain-001
    confidence: high
tests:
  - id: TST-TRACE-001
    path: tests/unit/test_basic_text_workflow.py::test_basic_text_workflow_generates_traceable_cards
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-TRACE-002
    path: tests/unit/test_txt_workflow_service.py::test_generate_cards_from_document_input_returns_traceable_cards
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-TRACE-002

```yaml
id: REQ-TRACE-002
status: active
type: functional
parent: null
children: []
statement: The system SHALL persist an inspectable information graph for each workflow-plugin extraction process, including extracted blocks, hierarchical relationships, source references, and workflow-plugin changes to extracted information.
rationale: Users need to observe how the selected workflow plugin structures and changes information during extraction.
source:
  - kind: prompt
    ref: prompt-004
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TRACE-003

```yaml
id: REQ-TRACE-003
status: active
type: interface
parent: null
children: []
statement: The backend API SHALL expose workflow-plugin extraction state updates so the web interface can follow information changes during a running extraction process.
rationale: Live observability requires the frontend to receive incremental extraction state instead of only final parsed content.
source:
  - kind: prompt
    ref: prompt-004
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TRACE-004

```yaml
id: REQ-TRACE-004
status: active
type: interface
parent: null
children: []
statement: The browser frontend SHALL allow users to view workflow-plugin extraction results as a selectable mind map representation.
rationale: A mind map gives users an understandable overview of dynamically extracted information blocks.
source:
  - kind: prompt
    ref: prompt-004
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TRACE-005

```yaml
id: REQ-TRACE-005
status: active
type: interface
parent: null
children: []
statement: Each extracted block shown in the mind map SHALL display a title derived from or assigned to that block.
rationale: Titles make extracted blocks scannable without forcing users to open every block.
source:
  - kind: prompt
    ref: prompt-004
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TRACE-006

```yaml
id: REQ-TRACE-006
status: active
type: interface
parent: null
children: []
statement: Selecting an extracted block in the mind map SHALL either navigate to a deeper mind map for nested extracted information or open a detail view for terminal extracted text.
rationale: Users need to move through the extraction structure like a dynamic information filesystem.
source:
  - kind: prompt
    ref: prompt-004
    confidence: high
tests: []
conflicts_with: []
```

## REQ-TRACE-007

```yaml
id: REQ-TRACE-007
status: active
type: interface
parent: null
children: []
statement: The extracted text detail view SHALL display the extracted text, important highlighted portions when available, and the source references associated with that extracted text.
rationale: Detail inspection should preserve both semantic emphasis and source traceability.
source:
  - kind: prompt
    ref: prompt-004
    confidence: high
tests: []
conflicts_with: []
```

## REQ-CARD-001

```yaml
id: REQ-CARD-001
status: active
type: functional
parent: null
children: []
statement: Stored run cards SHALL retain original content, current content, status, rating, tags, workflow plugin id, and source reference.
rationale: Review and improvement workflows require auditable card state.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: code
    ref: code-domain-001
    confidence: high
tests:
  - id: TST-CARD-001
    path: tests/unit/test_domain_models.py::test_run_card_tracks_original_and_current_card_content
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-IMPROVE-001

```yaml
id: REQ-IMPROVE-001
status: active
type: functional
parent: null
children: []
statement: The system SHALL allow users to edit cards, delete cards, rate cards, and rate runs.
rationale: Users need direct control over generated card quality.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: code
    ref: code-domain-001
    confidence: high
tests:
  - id: TST-IMPROVE-001
    path: tests/unit/test_improvement_service.py::test_improvement_service_applies_edit_delete_and_rating_actions
    kind: unit
    match: explicit
    coverage: full
  - id: TST-IMPROVE-002
    path: tests/unit/test_api_resources.py::test_improvement_endpoints_apply_actions_and_list_history
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-IMPROVE-002

```yaml
id: REQ-IMPROVE-002
status: active
type: functional
parent: null
children: []
statement: The system SHALL support workflow-driven prompt refinement for selected cards and all active cards in a run.
rationale: Plugin-owned refinement lets users improve cards while preserving workflow architecture.
source:
  - kind: doc
    ref: doc-plugins-001
    confidence: high
  - kind: code
    ref: code-basic-workflow-001
    confidence: high
tests:
  - id: TST-IMPROVE-003
    path: tests/unit/test_basic_text_workflow.py::test_basic_text_workflow_can_apply_prompt_refinement
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-IMPROVE-004
    path: tests/unit/test_improvement_service.py::test_improvement_service_applies_plugin_refinement_to_selected_cards
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-IMPROVE-005
    path: tests/unit/test_improvement_service.py::test_improvement_service_applies_plugin_refinement_to_all_active_cards
    kind: unit
    match: explicit
    coverage: partial
conflicts_with: []
```

## REQ-EXPORT-001

```yaml
id: REQ-EXPORT-001
status: active
type: functional
parent: null
children: []
statement: The system SHALL export current non-deleted run cards to Anki-compatible CSV containing front, back, and tags.
rationale: Reliable CSV export is the early Anki-compatible output path.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: doc
    ref: doc-architecture-001
    confidence: high
tests:
  - id: TST-EXPORT-001
    path: tests/unit/test_csv_exporter.py::test_export_cards_to_csv_writes_anki_headers
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-EXPORT-002
    path: tests/unit/test_export_service.py::test_export_service_creates_csv_export_from_run_cards
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-EXPORT-003
    path: tests/unit/test_export_service.py::test_export_service_skips_deleted_cards_and_supports_selected_exports
    kind: unit
    match: explicit
    coverage: full
conflicts_with: []
```

## REQ-EXPORT-002

```yaml
id: REQ-EXPORT-002
status: active
type: constraint
parent: null
children: []
statement: Normal Anki exports SHALL NOT include source references by default.
rationale: Source traceability is important inside the system but should not clutter default Anki output.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
tests:
  - id: TST-EXPORT-004
    path: tests/unit/test_csv_exporter.py::test_export_cards_to_csv_writes_anki_headers
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-EXPORT-003

```yaml
id: REQ-EXPORT-003
status: active
type: functional
parent: null
children: []
statement: The final product SHALL support direct Anki integration.
rationale: Direct Anki integration is a required final capability for the product.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
tests: []
conflicts_with: []
```

## REQ-API-001

```yaml
id: REQ-API-001
status: active
type: interface
parent: null
children: []
statement: The backend API SHALL expose resource-oriented endpoints for documents, runs, run-scoped cards, improvements, and exports.
rationale: The resource API supports upload, generation, review, improvement, and export as inspectable steps.
source:
  - kind: doc
    ref: doc-readme-001
    confidence: high
  - kind: doc
    ref: doc-architecture-001
    confidence: high
tests:
  - id: TST-API-001
    path: tests/unit/test_api_resources.py::test_documents_endpoints_store_and_return_uploaded_documents
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-API-002
    path: tests/unit/test_api_resources.py::test_runs_endpoints_create_run_and_expose_cards
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-API-003
    path: tests/unit/test_api_resources.py::test_improvement_endpoints_apply_actions_and_list_history
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-API-004
    path: tests/unit/test_api_resources.py::test_export_endpoints_create_describe_and_download_exports
    kind: unit
    match: explicit
    coverage: partial
conflicts_with: []
```

## REQ-API-002

```yaml
id: REQ-API-002
status: active
type: interface
parent: null
children: []
statement: The backend API SHALL NOT expose the legacy one-shot document generation endpoint.
rationale: The API uses resource-oriented document, run, card, improvement, and export resources instead.
source:
  - kind: doc
    ref: doc-architecture-001
    confidence: high
tests:
  - id: TST-API-005
    path: tests/unit/test_api_resources.py::test_legacy_generate_document_endpoint_is_no_longer_available
    kind: unit
    match: explicit
    coverage: full
conflicts_with: []
```

## REQ-FRONTEND-001

```yaml
id: REQ-FRONTEND-001
status: active
type: interface
parent: null
children: []
statement: The CLI SHALL use the backend resource flow to upload a document, create a run, create an export, and download the result.
rationale: The CLI should exercise the same backend contract as other clients.
source:
  - kind: doc
    ref: doc-readme-001
    confidence: high
  - kind: doc
    ref: doc-frontend-001
    confidence: high
tests:
  - id: TST-FRONTEND-001
    path: tests/unit/test_cli.py::test_cli_generate_command_writes_csv
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-FRONTEND-002
    path: tests/unit/test_frontend_api_client.py::test_generate_cards_from_document_calls_api
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-FRONTEND-002

```yaml
id: REQ-FRONTEND-002
status: active
type: interface
parent: null
children: []
statement: The browser frontend SHALL support document upload, run creation, card inspection, improvements, export creation, export inspection, and export download through backend API proxy routes.
rationale: The browser UI provides the user-facing workflow over the same resource API.
source:
  - kind: doc
    ref: doc-readme-001
    confidence: high
  - kind: doc
    ref: doc-frontend-001
    confidence: high
tests:
  - id: TST-FRONTEND-003
    path: tests/unit/test_frontend_web.py::test_web_index_serves_html
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-FRONTEND-004
    path: tests/unit/test_frontend_web.py::test_web_proxy_routes_delegate_to_frontend_api_client
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-FRONTEND-003

```yaml
id: REQ-FRONTEND-003
status: active
type: interface
parent: null
children: []
statement: The browser frontend SHALL be designable in Figma to support simple web interface prototyping.
rationale: Figma-based design enables quick iteration on web interface concepts before implementation.
source:
  - kind: prompt
    ref: prompt-006
    confidence: high
tests: []
conflicts_with: []
```

## REQ-STORAGE-001

```yaml
id: REQ-STORAGE-001
status: active
type: functional
parent: null
children: []
statement: The backend SHALL persist and retrieve uploaded documents, generation runs, and export artifacts through dedicated storage repositories.
rationale: Resource flows need inspectable stored state for review, improvement, and export.
source:
  - kind: doc
    ref: doc-readme-001
    confidence: medium
  - kind: test
    ref: tests/unit/test_storage_repositories.py
    confidence: high
tests:
  - id: TST-STORAGE-001
    path: tests/unit/test_storage_repositories.py::test_document_repository_saves_lists_and_updates_documents
    kind: unit
    match: explicit
    coverage: partial
  - id: TST-STORAGE-002
    path: tests/unit/test_storage_repositories.py::test_run_repository_saves_lists_and_updates_runs
    kind: unit
    match: explicit
    coverage: partial
conflicts_with: []
```

## REQ-ERROR-001

```yaml
id: REQ-ERROR-001
status: active
type: non-functional
parent: null
children: []
statement: The system SHALL distinguish workflow extraction errors, workflow parsing errors, plugin errors, model errors, validation errors, and export errors in debuggable failure handling.
rationale: Clear failure categories are required for iterative document-to-card debugging when extraction and parsing occur inside workflow plugins.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests:
  - id: TST-ERROR-001
    path: tests/unit/test_api_resources.py::test_document_and_run_detail_endpoints_return_404_for_missing_resources
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-ERROR-002
    path: tests/unit/test_api_resources.py::test_export_endpoints_validate_unknown_resources_and_exporters
    kind: unit
    match: inferred
    coverage: partial
  - id: TST-ERROR-003
    path: tests/unit/test_api_resources.py::test_improvement_endpoints_validate_bad_requests
    kind: unit
    match: inferred
    coverage: partial
conflicts_with: []
```

## REQ-LOG-001

```yaml
id: REQ-LOG-001
status: active
type: non-functional
parent: null
children: []
statement: The system SHALL log important file intake, selected workflow plugin, workflow extraction, workflow parsing, user-assisted extraction requests, validation, card generation, export, and integration steps.
rationale: Run-level observability is required for debugging and comparison when extraction and parsing are workflow-owned.
source:
  - kind: doc
    ref: doc-agents-001
    confidence: high
  - kind: prompt
    ref: prompt-002
    confidence: high
  - kind: prompt
    ref: prompt-003
    confidence: high
tests: []
conflicts_with: []
```
