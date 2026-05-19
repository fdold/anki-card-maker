# Product Overview

Anki Card Maker is a modular Python application that converts documents into Anki-compatible flashcards.

## Core Workflow

1. User uploads a source document (currently TXT supported)
2. A generation run executes a selected workflow plugin that handles extraction, parsing, and card generation
3. Generated cards can be reviewed, rated, and refined through improvement actions
4. Cards are exported to Anki-compatible formats (currently CSV)

## Key Concepts

- **Documents**: Uploaded source material stored with parsed content
- **Runs**: A single execution of a workflow plugin against one or more documents, producing traceable cards
- **Cards**: Generated flashcards with front/back content, source references, status, and ratings
- **Workflow Plugins**: User-selectable processing units that define the full document-to-card pipeline
- **Improvements**: Actions that modify cards after generation (edit, delete, rate, prompt-refine)
- **Exports**: Anki-compatible output artifacts (CSV) generated from a run's cards

## Design Principles

- Each run uses exactly one workflow plugin
- Cards preserve source references for traceability
- Prompts and generation logic live inside plugins only
- All external functionality is accessed through explicit interfaces
- Internal logic is testable without external dependencies

## Source of Truth

`docs/requirements/REQUIREMENTS.md` is the canonical reference for all product, architecture, and implementation requirements. Update it before implementing changes.
