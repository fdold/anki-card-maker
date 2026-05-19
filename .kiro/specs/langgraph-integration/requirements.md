# Requirements Document

## Introduction

This feature integrates LangGraph directly as the workflow runtime for graph-based plugin execution in the Anki Card Maker project. Workflow plugins build native LangGraph `StateGraph` instances using LangGraph's API, with a Pydantic-based `RuntimeState` model serving as the graph's state schema. A `RunService` orchestrates execution, observes LangGraph's native event stream, and emits normalized events. A `WorkflowPluginModel` serves as the UI contract — declaring plugin capabilities, exposing run status, progress, and pending interactions to the frontend and API layer. The integration preserves the existing one-plugin-per-run constraint while enabling durable, observable, and resumable graph execution with human-in-the-loop support.

## Glossary

- **Runtime_State**: A project-owned, serializable Pydantic model used directly as LangGraph's state schema, representing the complete execution state of a workflow run including inputs, intermediate results, generated artifacts, errors, and pending interactions.
- **Checkpoint**: A persisted snapshot of Runtime_State managed by LangGraph's native checkpointer at each super-step boundary, enabling pause, resume, retry, and recovery.
- **Runtime_Event**: A project-owned normalized event emitted by RunService while observing LangGraph execution, representing operation lifecycle, state changes, generated artifacts, interaction requests, or failures.
- **Event_Sink**: The destination for Runtime_Events, decoupling event production from consumption and enabling test observation.
- **Interaction_Request**: A structured, serializable request emitted when a workflow graph uses LangGraph's native `interrupt()` function to pause for user input.
- **Runtime_Context**: The injectable container of external capability interfaces (LLM via LangChain BaseChatModel, OCR, embedding, etc.) provided to graph nodes during execution.
- **Graph_Node**: A single named operation within a LangGraph StateGraph that receives Runtime_State and Runtime_Context, performs work, and returns updated Runtime_State.
- **Workflow_Plugin**: A user-selectable plugin that defines the document-to-card processing pipeline, now optionally expressible as a native LangGraph StateGraph via a `build_graph()` method.
- **RunService**: The backend service that orchestrates workflow execution, invokes LangGraph's compiled graph, observes execution, and emits Runtime_Events.
- **RunView**: The UI-facing representation of a running graph execution, exposing status, progress, completed nodes, pending interactions, and generated artifacts to the frontend and API layer.
- **WorkflowPluginModel**: The declarative model that serves as the UI contract for a workflow plugin — declaring capabilities, supported operations, and interaction points without wrapping LangGraph internals.
- **StateGraph**: LangGraph's native graph builder class used directly by plugins to define nodes, edges, and conditional routing.

## Requirements

### Requirement 1: Serializable Runtime State as LangGraph State Schema

**User Story:** As a developer, I want workflow execution state represented by a project-owned Pydantic model that LangGraph uses directly as its state schema, so that state is serializable, inspectable, and type-safe without translation layers.

#### Acceptance Criteria

1. THE Runtime_State SHALL be a Pydantic model containing source input references, extracted blocks, parsed content, generated card candidates, operation metadata, errors, and pending Interaction_Requests.
2. THE Runtime_State SHALL include an explicit schema_version field.
3. WHEN Runtime_State is serialized to JSON and then deserialized, THE RunService SHALL produce an equivalent Runtime_State object (round-trip property).
4. THE Runtime_State SHALL be domain-compatible, using existing domain model types (ParsedContent, CardCandidate, SourceReference) where applicable.
5. THE Runtime_State SHALL be used directly as the LangGraph StateGraph state schema without intermediate translation.

### Requirement 2: Checkpointed Durable Execution via LangGraph Checkpointer

**User Story:** As a user, I want long-running workflow executions to survive interruptions, so that slow model calls, OCR processing, or my own review steps do not lose completed work.

#### Acceptance Criteria

1. THE RunService SHALL configure LangGraph's native checkpointer when compiling the StateGraph, using MemorySaver for tests and a persistent checkpointer for production.
2. WHEN a workflow execution is resumed from a checkpoint, THE RunService SHALL invoke LangGraph with the existing thread_id so that execution continues from the last completed super-step without re-executing previously completed nodes.
3. IF a Graph_Node fails with a recoverable error, THEN THE RunService SHALL allow retry from the last successful checkpoint without losing prior completed state.
4. IF a Graph_Node fails with a terminal error, THEN THE RunService SHALL mark the run as failed, persist the failure in Runtime_State, and emit a terminal failure Runtime_Event.
5. THE RunService SHALL use LangGraph's MemorySaver for automated tests and a persistent saver implementation for production deployments.

### Requirement 3: Human-in-the-Loop via LangGraph Interrupt

**User Story:** As a user, I want the workflow to pause and ask me for input when automated extraction cannot proceed, so that I can provide descriptions or make decisions without losing workflow progress.

#### Acceptance Criteria

1. WHEN a Graph_Node determines that user input is required, THE Graph_Node SHALL call LangGraph's native `interrupt()` function with a structured Interaction_Request payload.
2. THE Interaction_Request SHALL include a request type, a human-readable prompt, structured response schema, and the originating node identifier.
3. WHEN a structured user response is submitted for a pending Interaction_Request, THE RunService SHALL resume execution using LangGraph's `Command(resume=...)` with the user response.
4. IF a user response does not conform to the declared response schema, THEN THE RunService SHALL reject the response with a validation error without advancing execution.
5. WHILE an Interaction_Request is pending, THE RunView SHALL report the run status as paused and expose the pending request through the backend API.

### Requirement 4: Normalized Runtime Events from LangGraph Observation

**User Story:** As a frontend developer, I want workflow progress exposed through normalized project-owned events, so that the web interface can observe execution without coupling to LangGraph event formats.

#### Acceptance Criteria

1. THE RunService SHALL emit Runtime_Events for operation start, operation completion, state updates, generated card candidates, Interaction_Requests, recoverable failures, terminal failures, and run completion by observing LangGraph execution.
2. THE Runtime_Event SHALL include a timestamp, event type, originating node identifier, and event-specific payload.
3. THE Event_Sink SHALL provide an in-memory implementation that collects events for test assertions.
4. WHEN a Runtime_Event is emitted, THE Event_Sink SHALL receive the event without blocking graph execution.

### Requirement 5: Injectable External Capabilities via Runtime Context

**User Story:** As a developer, I want graph nodes to access external capabilities (LLM, OCR, embedding) only through injected interfaces, so that workflow logic remains testable with fake implementations while leveraging LangChain's native model features.

#### Acceptance Criteria

1. THE Runtime_Context SHALL provide typed access to external capability interfaces required by graph nodes.
2. WHEN a Graph_Node requires an LLM capability, THE Graph_Node SHALL obtain a LangChain BaseChatModel instance from Runtime_Context, enabling native LangChain features (streaming, tool calling, structured output) while remaining injectable.
3. WHEN a Graph_Node requires a non-LLM external capability (OCR, embedding), THE Graph_Node SHALL obtain the capability from Runtime_Context through a project-owned interface.
4. THE Runtime_Context SHALL accept fake or in-memory implementations of all external capability interfaces for automated testing, including FakeChatModel instances for LLM testing.
5. IF a Graph_Node requests a capability that is not registered in Runtime_Context, THEN THE RunService SHALL raise a configuration error before execution begins.

### Requirement 6: Deterministic and Idempotent Node Design

**User Story:** As a developer, I want graph nodes designed for deterministic or idempotent execution at runtime boundaries, so that checkpoint resume and retry do not produce duplicate side effects.

#### Acceptance Criteria

1. THE RunService SHALL execute each Graph_Node with the Runtime_State snapshot from the preceding checkpoint as input, ensuring repeated execution of the same node with the same input produces equivalent output.
2. WHEN a Graph_Node performs side-effecting work through an external capability interface, THE Graph_Node SHALL record the operation result in Runtime_State so that retries can detect and skip already-completed side effects.
3. THE RunService SHALL document idempotency expectations for each external capability interface in Runtime_Context.

### Requirement 7: State Schema Versioning and Migration

**User Story:** As a developer, I want persisted workflow state to include a schema version, so that paused or checkpointed runs can be migrated or invalidated when the state model changes.

#### Acceptance Criteria

1. THE Runtime_State SHALL include a schema_version field that identifies the state model version.
2. WHEN the RunService loads a checkpoint with a schema_version older than the current version, THE RunService SHALL attempt migration using registered migration functions.
3. IF migration is not possible for a given schema_version, THEN THE RunService SHALL mark the run as failed with a clear migration error and emit a terminal failure Runtime_Event.

### Requirement 8: Graph-Capable Plugin Interface with Direct LangGraph Usage

**User Story:** As a plugin developer, I want to define my workflow as a native LangGraph StateGraph, so that I can use LangGraph's full API for graph composition while maintaining backward compatibility with existing synchronous plugins.

#### Acceptance Criteria

1. THE Workflow_Plugin interface SHALL support an optional `build_graph()` method that returns a native LangGraph StateGraph when the plugin is graph-capable.
2. WHEN a workflow plugin provides a `build_graph()` method, THE RunService SHALL compile and execute the returned StateGraph using LangGraph's native compilation with the configured checkpointer.
3. WHEN a workflow plugin does not provide a `build_graph()` method, THE RunService SHALL execute the plugin through the existing synchronous generate_cards and apply_improvement interface.
4. THE RunService SHALL preserve backward compatibility with all existing workflow plugins that do not define a `build_graph()` method.
5. THE Workflow_Plugin SHALL declare its graph nodes, conditional routing, entry node, and terminal nodes within the `build_graph()` method using LangGraph's native StateGraph API.

### Requirement 9: Failure Categorization

**User Story:** As a developer, I want workflow failures categorized by origin, so that the system can distinguish recoverable from terminal errors and provide actionable diagnostics.

#### Acceptance Criteria

1. THE RunService SHALL categorize failures into extraction, parsing, model, validation, external capability, recoverable runtime, and terminal runtime categories by catching exceptions raised during LangGraph execution.
2. WHEN a failure occurs, THE Runtime_Event SHALL include the failure category, originating node, error message, and whether the failure is recoverable.
3. IF a failure is categorized as recoverable, THEN THE RunService SHALL allow retry from the last successful checkpoint.
4. IF a failure is categorized as terminal, THEN THE RunService SHALL mark the run as failed and prevent further execution or retry.

### Requirement 10: Execution Graph Separation from Information Graph

**User Story:** As a developer, I want the workflow execution graph kept separate from the user-facing information graph, so that internal control flow does not pollute the user's content representation.

#### Acceptance Criteria

1. THE RunService SHALL maintain execution graph structure (nodes, transitions, execution order) separately from the information graph (extracted content, relationships, source references).
2. WHEN a Graph_Node produces information graph updates, THE Graph_Node SHALL emit those updates as structured deltas in Runtime_State rather than modifying the execution graph structure.
3. WHERE debugging is enabled, THE RunService SHALL expose execution graph structure and node execution history for diagnostic purposes without merging execution data into the information graph.

### Requirement 11: Workflow Plugin Model as UI Contract

**User Story:** As a frontend developer, I want a declarative plugin model that exposes workflow capabilities, run status, progress, and pending interactions to the UI, so that the frontend can render workflow state without knowledge of LangGraph internals.

#### Acceptance Criteria

1. THE WorkflowPluginModel SHALL declare the plugin's supported operations, required inputs, and configurable parameters as a serializable manifest.
2. THE RunView SHALL expose the current run status (running, paused, completed, failed), list of completed nodes, current node, and percentage progress to the API layer.
3. WHILE an Interaction_Request is pending, THE RunView SHALL include the pending interaction details (prompt, response schema, originating node) so the frontend can render an input form.
4. WHEN a run completes, THE RunView SHALL include the generated card candidates and any errors encountered during execution.
5. THE WorkflowPluginModel SHALL be independent of LangGraph types, exposing only project-owned Pydantic models to the API and frontend layers.
