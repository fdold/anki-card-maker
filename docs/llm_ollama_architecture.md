# LLM and Ollama Integration Target Structure

## Purpose

This document defines the target structure for integrating centrally managed LLM
access into the project, starting with Ollama running in dedicated Docker
containers.

The goal is not to couple workflows directly to Ollama. The goal is to add a
provider-neutral model layer that workflow plugins can use through a stable
execution context while keeping prompts and card logic inside the plugins.

## Design Rules

- All prompt text stays inside `plugins/`.
- Workflow plugins remain user-selectable and own their own config schema.
- Model access is centrally managed in `backend/models/`.
- Ollama is the first provider, not the only possible provider.
- Model outputs must be validated before they become `CardCandidate` or `RunCard`.
- Source traceability remains anchored in parsed blocks and segments, not in raw
  provider output.
- Invocation metadata should be referenceable for debugging and later comparison.
- Docker Compose remains the primary local runtime path.

## Target Repository Structure

The target structure for the LLM layer should look like this:

```text
backend/
  api/
    main.py
    schemas.py
  models/
    __init__.py
    base.py
    gateway.py
    registry.py
    settings.py
    providers/
      __init__.py
      base.py
      ollama.py
  services/
    run_service.py
    improvement_service.py
plugins/
  base.py
  workflows/
    basic_text_workflow.py
    ollama_text_workflow.py
docker/
  backend.Dockerfile
  model_profiles.dev.json
docs/
  architecture.md
  plugins.md
  llm_ollama_architecture.md
tests/
  unit/
    test_model_settings.py
    test_model_registry.py
    test_model_gateway.py
    test_ollama_provider.py
    test_ollama_text_workflow.py
    test_run_service_model_context.py
    test_improvement_service_model_context.py
```

## Module Responsibilities

### `backend/models/base.py`

This module becomes the provider-neutral model contract layer.

Recommended core types:

- `ModelMessage`
  - normalized chat message with `role` and `content`
- `ModelGenerationOptions`
  - provider-neutral generation settings such as `temperature`, `top_p`,
    `seed`, `max_output_tokens`, `stop`
- `ModelProfile`
  - centrally configured model target with:
    - `profile_id`
    - `provider`
    - `model_name`
    - `base_url`
    - `timeout_seconds`
    - `default_options`
    - `supports_structured_output`
- `ModelRequest`
  - normalized request passed through the gateway
  - includes `profile_id`, `purpose`, `messages`, `options`, `metadata`
- `ModelUsage`
  - token or evaluation counters when available
- `ModelResponse`
  - normalized provider response with:
    - `provider`
    - `model_name`
    - `content`
    - `raw_payload`
    - `usage`
    - `latency_ms`
    - `finish_reason`
- `ModelInvocationRecord`
  - debug and traceability summary for one provider call
- `ModelProviderError`
  - provider or transport level failure
- `ModelResponseValidationError`
  - structured parsing or schema validation failure

This file should stay generic and must not contain Ollama-specific HTTP logic.

### `backend/models/providers/base.py`

This module defines the provider interface.

Recommended shape:

- `ModelProvider`
  - abstract provider contract
  - `generate(profile, request) -> ModelResponse`
  - optional `healthcheck(profile) -> bool`

Responsibilities:

- define the contract that all providers must implement
- isolate provider-specific request execution behind one stable interface

### `backend/models/providers/ollama.py`

This module implements the Ollama provider adapter.

Responsibilities:

- translate `ModelRequest` into Ollama API calls
- support chat-style prompts
- support structured JSON output mode where available
- map Ollama failures into `ModelProviderError`
- keep raw provider payload available in `ModelResponse`
- avoid plugin logic and avoid card-specific parsing

Expected external dependency:

- runtime HTTP client support, most likely `httpx`

### `backend/models/settings.py`

This module owns central model profile configuration loading.

Recommended responsibilities:

- load model profiles from a dedicated config file or environment variable
- validate that each profile has:
  - provider
  - model name
  - reachable base URL format
  - timeout and default generation options
- provide development defaults for local Compose setups

Recommended configuration approach:

- local Compose mounts `docker/model_profiles.dev.json`
- backend reads the file path from an env var such as
  `ANKI_CARD_MAKER_MODEL_PROFILES_FILE`
- production can later override this through env or mounted secrets

This keeps model wiring flexible without scattering container addresses across
plugins or services.

### `backend/models/registry.py`

This module becomes the central lookup layer for configured model profiles.

Recommended functions:

- `list_model_profiles()`
- `get_model_profile(profile_id)`
- `build_model_gateway()`

Responsibilities:

- resolve `profile_id` to a validated `ModelProfile`
- create provider instances and wire them into the gateway
- keep provider selection out of plugin code

### `backend/models/gateway.py`

This module exposes the single API that the rest of the backend should use.

Recommended responsibilities:

- resolve `profile_id` through the registry
- merge request options with profile defaults
- call the selected provider
- validate structured output into a supplied Pydantic response model
- collect `ModelInvocationRecord`s for the current run

Recommended public methods:

- `generate_text(...) -> ModelResponse`
- `generate_structured(..., response_model=...) -> ParsedModelResult`

This is the place where provider transport ends and application-safe validated
output begins.

## Plugin Integration Contract

### `plugins/base.py`

The workflow plugin interface should be extended with a workflow execution
context rather than letting plugins create provider clients themselves.

Recommended addition:

- `WorkflowExecutionContext`
  - `run_id`
  - `models`
  - optional logger or metadata collector

Recommended workflow signatures:

```python
def generate_cards(
    self,
    parsed_content: ParsedContent,
    config: WorkflowPluginConfigT,
    context: WorkflowExecutionContext,
) -> list[CardCandidate]:
    ...

def apply_improvement(
    self,
    request: WorkflowImprovementRequest,
    config: WorkflowPluginConfigT,
    context: WorkflowExecutionContext,
) -> list[RunCard]:
    ...
```

Why this matters:

- plugins stay modular
- prompts stay in plugins
- provider access becomes uniform
- tests can inject a fake gateway without mocking raw HTTP

### `plugins/workflows/ollama_text_workflow.py`

This should become the first real LLM-driven workflow plugin.

Recommended config fields:

- `generator_model_profile`
- `improver_model_profile`
- `max_cards`
- `max_blocks`
- `temperature`
- plugin-specific strategy controls such as question style or dedup settings

Recommended internal structure:

- define plugin-owned prompt templates inside the plugin module
- define plugin-owned Pydantic response models for structured output validation
- process parsed blocks in a traceable block-by-block or small-batch manner
- map validated output into `CardCandidate`
- preserve source linkage from the input block that produced each candidate

The baseline `basic_text_workflow` should remain as a non-LLM reference
workflow.

## Service Wiring

### `backend/services/run_service.py`

Target behavior:

- receive a prebuilt `ModelGateway`
- create a `WorkflowExecutionContext` for each run
- pass the context into the selected workflow plugin
- collect model invocation summaries produced during the run

This is the right place to own run-scoped execution context. It should not own
provider-specific code.

### `backend/services/improvement_service.py`

Target behavior:

- use the same `ModelGateway`
- create the same execution context shape for prompt refinement actions
- keep improvement and initial generation on one shared model infrastructure

This avoids a second ad-hoc LLM path for improvements.

### `backend/api/main.py`

Initial composition can stay simple:

- build model settings and gateway during app startup
- inject the gateway into `RunService` and `ImprovementService`

No new general-purpose dependency injection framework is required for the first
implementation step.

## Domain and Traceability

The current shared domain models already cover documents, parsed content, card
candidates, run cards, and generation runs. For LLM support, traceability should
be added carefully.

Recommended addition in `domain/models.py`:

- `RunModelInvocation`
  - minimal summary meant for runs and API responses
  - includes:
    - `invocation_id`
    - `profile_id`
    - `provider`
    - `model_name`
    - `purpose`
    - `status`
    - `latency_ms`
    - `error_message`

Recommended addition to `GenerationRun`:

- `model_invocations: list[RunModelInvocation] = Field(default_factory=list)`

Important boundary:

- full transport request and raw provider payload stay in `backend/models/`
- shared run-safe summaries may be exposed through `domain/models.py`

This keeps debug data available without turning the shared domain model into a
provider transport dump.

## Docker and Runtime Topology

Ollama should run in dedicated containers, separate from the backend.

Recommended local Compose topology:

- `backend`
- `frontend`
- `ollama-default`
- optional `ollama-heavy` later for larger or slower models

Recommended Compose responsibilities:

- backend talks to Ollama only through configured `base_url`s in model profiles
- each Ollama service gets its own named volume for model data
- model selection belongs to `model_profiles.dev.json`, not hardcoded service
  logic in Python modules

Recommended first development profile example:

```json
[
  {
    "profile_id": "ollama_generation_default",
    "provider": "ollama",
    "model_name": "qwen3:8b",
    "base_url": "http://ollama-default:11434",
    "timeout_seconds": 120,
    "supports_structured_output": true,
    "default_options": {
      "temperature": 0.2
    }
  },
  {
    "profile_id": "ollama_improvement_default",
    "provider": "ollama",
    "model_name": "qwen3:8b",
    "base_url": "http://ollama-default:11434",
    "timeout_seconds": 120,
    "supports_structured_output": true,
    "default_options": {
      "temperature": 0.1
    }
  }
]
```

The first implementation can point both profiles to one Ollama container. The
structure should still assume that different profiles may later target different
containers or models.

## End-to-End Flow

The target runtime flow should be:

1. A document is uploaded and parsed into `ParsedContent`.
2. A run is created with one selected workflow plugin and plugin-owned config.
3. `RunService` creates a `WorkflowExecutionContext`.
4. The workflow plugin calls `context.models.generate_structured(...)`.
5. The gateway resolves the model profile and calls the Ollama provider.
6. The provider returns a normalized `ModelResponse`.
7. The gateway validates the structured output into plugin-owned response models.
8. The workflow maps validated output into `CardCandidate`.
9. `RunService` stores `RunCard`s plus run-scoped invocation summaries.
10. Improvement flows reuse the same model gateway and context.

## Testing Structure

The existing repository uses a flat `tests/unit/` layout. The new LLM-related
tests should follow that style rather than introducing a large new test tree.

Recommended unit test coverage:

- `test_model_settings.py`
  - model profile file loading and validation
- `test_model_registry.py`
  - profile lookup and provider wiring
- `test_model_gateway.py`
  - option merging, structured parsing, invocation recording
- `test_ollama_provider.py`
  - request mapping, transport error handling, response normalization
- `test_ollama_text_workflow.py`
  - plugin config validation, structured output mapping, source linkage
- `test_run_service_model_context.py`
  - run execution passes context and stores invocation summaries
- `test_improvement_service_model_context.py`
  - improvement path reuses the same gateway contract

Later integration tests can verify the Compose setup against a running Ollama
container, but that should come after the unit-tested core path exists.

## Initial Implementation Slices

To keep the work in small, commit-sized steps, implementation should follow this
order:

1. Expand `backend/models/base.py` into the neutral model contract layer.
2. Add `settings.py`, `registry.py`, `gateway.py`, and `providers/base.py`.
3. Add the Ollama provider adapter in `providers/ollama.py`.
4. Extend `plugins/base.py` with `WorkflowExecutionContext`.
5. Wire `RunService` and `ImprovementService` to use a shared `ModelGateway`.
6. Add the first `ollama_text_workflow` plugin with structured output validation.
7. Extend run traceability with run-safe invocation summaries.
8. Add Compose configuration and development model profile config.
9. Add unit tests for the model layer and the new workflow plugin.

## Non-Goals For The First LLM Slice

The first LLM integration should explicitly avoid:

- embedding provider clients directly in workflow plugins
- a shared global workflow config schema for all plugins
- document-wide one-shot prompting as the default strategy
- a complex background queue before the synchronous path works
- exposing raw source references in Anki export
- coupling the project to Ollama-specific structures outside `backend/models/`
