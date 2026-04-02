# AGENTS.md

## Purpose

Build a modular application that turns documents into **high-quality Anki flashcards**.

The system must let users upload source files, run a selectable **card-generation workflow plugin**, inspect generated cards with source references, improve results iteratively, and export or sync them to **Anki**.

This project is not a generic learning platform. Its primary purpose is to generate **useful, learnable, Anki-compatible cards** from documents.

---

## Primary Goals

When making decisions, optimize in this order:

1. **Card quality and learning usefulness**
2. **Traceability to source text**
3. **Modular workflow architecture**
4. **Extensibility across models, prompts, and methods**
5. **Stable Anki-compatible output**
6. **User control and iterative improvement**
7. **Clean Docker-based reproducibility**

---

## Core Product Direction

This system should support:

- Uploading source documents
- Converting them into a standardized internal representation
- Running exactly **one active card-generation workflow plugin** per generation run
- Producing card suggestions with source linkage
- Letting users review, accept, reject, or improve cards
- Exporting to Anki-compatible formats early
- Supporting **direct Anki integration** as a required final capability

The product must remain **traceable, modular, and experiment-friendly**.

---

## What “Plugin” Means in This Project

In this project, a **plugin** is a formal processing unit.

The most important plugin type is a **workflow plugin**:

- A workflow plugin defines the main process that turns standardized input data into flashcards.
- For each generation run, **exactly one user-selected workflow plugin** is active.
- A workflow plugin may internally call other helper plugins, tools, models, or procedures.
- General product features are **not** plugins unless they are part of document-to-card processing.

Important distinction:

- **Card-generating plugins** create cards and are user-selectable.
- **Helper plugins** do not create final cards directly and may only be used internally by other plugins.

---

## Hard Constraints

- The project must be implemented in **Python**.
- The project must run in **Docker** and be managed primarily through **Docker Compose**.
- The architecture must stay modular.
- Card-generation prompts must exist **only inside plugin structures**.
- Standardized `domain` models must be used across the system.
- Avoid project-wide refactors unless directly necessary for the current task.
- Do not build generic platform features that weaken the Anki focus.
- Do not tightly couple the system to one model provider or one prompting strategy.

---

## Technical Architecture

### Required high-level structure

The project should be split into:

- `frontend/` — user interface
- `backend/` — API, services, orchestration, pipeline, storage, exporters
- `domain/` — shared internal models and schemas
- `plugins/` — workflow plugins and other formal processing plugins
- `tests/` — unit, integration, API, and end-to-end tests
- `docker/` — Docker-related files
- `docs/` — architecture and plugin documentation

### Expected repository layout

- `frontend/`
- `backend/`
- `backend/api/`
- `backend/services/`
- `backend/pipeline/`
- `backend/pipeline/parsers/`
- `backend/exporters/`
- `backend/storage/`
- `domain/`
- `plugins/`
- `tests/`
- `docker/`
- `docs/`

### Separation rules

Keep these separated:

- UI logic
- API logic
- pipeline logic
- parsing
- workflow execution
- model access
- export/integration logic
- shared domain models

Do not mix them casually.

---

## Domain Model Rules

Use shared standardized models for core entities such as:

- document
- parsed content
- segment/chunk
- card candidate
- final card
- revision/improvement result
- validation result
- exportable Anki card

Rules:

- New core flows must use standardized domain models.
- Do not introduce local ad-hoc structures when a shared domain model should exist.
- Plugins must accept and return valid domain-compatible structures.
- Internal representations may vary inside a plugin, but the plugin must map cleanly back to standard domain objects.

---

## Model and Method Integration Rules

Models and reusable processing methods must be **centrally managed by the project**.

Plugins may use them, but should not reinvent provider-specific integration.

Support should remain open for:

- local models such as **Ollama**
- external API-based models such as **ChatGPT**
- non-LLM methods such as **spaCy** or other NLP/ML components
- hybrid pipelines combining multiple approaches

Rules:

- Plugins may use one or more centrally provided models or methods.
- A plugin may explicitly require a specific model or method.
- New model adapters should be addable **without rewriting existing plugins**.
- Model outputs must be validated before continuing.
- Relevant prompt outputs or model results should be referenceable for debugging and comparison.

---

## Workflow Plugin Rules

Workflow plugins are the core of the project.

A workflow plugin:

- defines the main path from standardized input data to final cards
- may include segmentation, prompting, scoring, filtering, deduplication, revision, or improvement
- may use multiple internal steps
- may use helper plugins internally
- may support multiple card types
- must expose a clear configuration surface
- must remain traceable

Rules:

- Exactly **one active workflow plugin** is selected per card-generation run.
- Workflow plugins must be user-selectable in the interface.
- Workflow plugin configuration must be explicit, structured, and validatable.
- Each workflow plugin must define and own its **own configuration model/schema**.
- Do **not** introduce a central shared workflow-plugin config that all plugins are forced to use.
- General application code may expose or validate a selected plugin's schema, but the config fields themselves belong to that plugin.
- Workflow plugins must not bypass domain models.
- Workflow plugins must not rely on hidden global state.
- Workflow plugins must not scatter prompt logic into general application code.
- Workflow plugins may return cards plus structured metadata or quality information.
- Only card-generating workflow plugins are directly selectable by users.

---

## Parsing Rules

Parsing exists to convert different source files into a common internal document format.

Early general parsing should be **minimal but good**, not overly opinionated.

Rules:

- Parsing should preserve meaningful text blocks and document structure where possible.
- Preserve or derive page, section, and chapter references when available.
- Preserve layout/formatting only when it is meaningfully relevant.
- Parsing should not pre-implement card-generation logic.
- Parsing problems should be marked or warned about, but early versions may still continue processing.
- TXT is the first stable input format.
- PDF support comes later.
- EPUB support comes later than PDF.
- OCR is a valuable future feature, but should not dominate the early implementation.

---

## Segmentation Rules

Global preprocessing should not enforce a heavy segmentation strategy.

The main segmentation strategy belongs to the active workflow plugin.

Rules:

- General preprocessing should provide neutral usable input, not a strong global chunking opinion.
- Workflow plugins may use semantic, rule-based, model-based, hybrid, or multi-stage segmentation.
- Workflow plugins are free to choose their segmentation strategy as long as they return valid domain results.
- Segment metadata should preserve or reference source, order, section, and chapter where possible.
- Heuristics like token or length limits may be used, but should be defined inside plugins, not as rigid project-wide behavior.

---

## Card Quality Rules

These are **guidelines for plugin design**, not a global hardcoded generation algorithm.

The system should aim for cards that are:

- useful for learning
- atomic
- short but correct
- derived as directly as possible from the material
- not trivial
- not redundant
- information-dense enough to cover the important material without flooding the learner with low-value cards

Rules:

- Prefer one clear knowledge unit per card.
- Make cards as short as possible without losing correctness or clarity.
- Prefer cards grounded in the source material.
- Avoid trivial, duplicate, or near-duplicate cards.
- Different plugins may use different card strategies as long as they still support good learning outcomes.

---

## Source and Traceability Rules

Traceability is a core requirement.

Rules:

- Each card should preserve a meaningful link to the original source text whenever possible.
- Source reference may be coarse; it does not need perfect sentence-level precision.
- Preserve page, section, chapter, position, or segment linkage where possible.
- Relevant intermediate results should be referenceable when useful.
- Traceability applies not only to initial generation but also to filtering, improvement, and regeneration.
- Internal metadata about plugin or method usage may be stored for comparison and debugging.
- User-facing traceability should prioritize source relation over internal implementation details.

Do **not** export source references into Anki by default.

---

## Export and Anki Rules

Anki is the primary target.

Rules:

- Internal card models should stay relatively close to Anki structure.
- Plugins may use richer intermediate structures internally, but final results must map cleanly to Anki-compatible cards.
- Early export should focus on reliable **CSV** output.
- **Direct Anki integration is required in the final product**.
- Export and Anki integration logic must live in dedicated backend modules.
- Tags are part of the standard card model.
- Source traceability is important inside the system but is not part of normal Anki export.
- Plugins must not produce outputs that undermine later export or Anki integration.

---

## Working Rules for Codex

When changing this repository:

- Work in **small, commit-sized steps**.
- Prefer minimal clean changes over broad refactors.
- Respect the existing module boundaries.
- Do not introduce project-wide structure changes without strong direct need.
- Keep workflow logic in plugins.
- Keep general system behavior in regular project code.
- Keep prompts for card generation inside plugins only.
- Use standardized domain models.
- Keep API contracts clear and stable.
- Keep Docker/Compose working.
- Document any new plugin config, env var, interface, or important architectural change.
- Favor solutions that improve card quality, traceability, and maintainability.

---

## Refactoring Policy

Refactoring is allowed only when it clearly supports the current task.

Avoid:

- broad repo-wide rewrites
- premature generic abstraction
- moving logic across layers without necessity
- introducing architecture that is not yet needed

Prefer:

- module-by-module improvement
- local cleanup tied to current implementation work
- stable interfaces over broad internal churn

---

## Testing Requirements

Testing is required as part of normal development.

Rules:

- New core logic should not be introduced without appropriate tests whenever feasible.
- Test domain models and validation logic.
- Test parsers with **real example files**.
- Test plugins for valid input handling, valid output structure, and stable interface behavior.
- Plugin tests should focus on structure and validity, not subjective content quality.
- Validate model outputs and prompt outputs before they are trusted.
- Test export behavior for Anki-compatible output.
- Cover important end-to-end flows from document to exportable card.
- Keep future plugin comparison and evaluation in mind, even if full analytics comes later.
- Direct Anki integration tests are welcome when feasible, but should not dominate early development.

Plugins may define their own extra tests, but that is encouraged rather than mandatory.

---

## Logging and Error Handling

The system must be debuggable.

Rules:

- Log important steps such as file intake, parsing result, selected workflow plugin, validation, card generation result, export, and integration steps.
- Distinguish clearly between parser errors, plugin errors, model errors, and validation errors.
- Do not silently swallow errors.
- On partial failure, continue when still possible and mark the problem.
- On critical failure that prevents valid results, abort that run cleanly.
- Technical logs should be much more detailed than user-facing UI feedback.
- Runs should be referenceable for later debugging.
- Bad model outputs should usually be marked and retried when possible.
- Uncertain results should be visibly marked in the interface so the user can decide whether to keep or reject them.

---

## Definition of Done

A task is only done when:

- it solves the intended problem cleanly
- it fits the architecture
- it respects domain models and stable interfaces
- it follows workflow-plugin rules when card generation is involved
- relevant validation and tests were added or updated
- logging and error behavior were handled appropriately
- warnings or uncertainty are surfaced when relevant
- documentation was updated where needed
- Docker/Compose is not silently broken
- no obvious dead paths, half-built placeholders, or incompatible data flows remain
- the result is integrated cleanly, not merely partially present

Large placeholder structures do **not** count as done.

---

## Preferred Implementation Order

Follow this order unless there is a strong reason not to:

1. Create clean project structure
2. Stabilize Docker and Docker Compose
3. Define shared domain models and validation
4. Implement core workflow-plugin architecture early
5. Build backend API and service structure
6. Implement file intake and minimal normalization
7. Support TXT as first stable input format
8. Implement first full card-generation workflow plugin
9. Stabilize card model and CSV export
10. Implement direct Anki integration
11. Add PDF support
12. Build initial UI
13. Add UI review and improvement interactions
14. Add more workflow plugins and model adapters
15. Add EPUB support
16. Add comparison/statistics tooling later

---

## Non-Goals for Early Development

Do not prioritize these early:

- generic learning platform features
- multi-user architecture
- account systems before Anki-driven need exists
- fine-tuning or model training infrastructure
- large-scale distributed deployment
- cloud-first architecture
- statistics or experiment dashboards before the main product works

---

## Decision Rules When Unsure

If multiple solutions are plausible, choose the one that:

1. most improves **card quality**
2. best respects the **workflow plugin architecture**
3. uses standardized **domain models**
4. best supports the **Anki target workflow**
5. best preserves **traceability and debuggability**
6. strengthens the stable core flow from document to card
7. keeps **Docker/Compose** healthy
8. avoids unnecessary large refactors
9. is easier to test and integrate cleanly
10. makes later plugin, model, or integration extension easier
