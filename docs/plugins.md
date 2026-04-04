# Plugins

## Workflow plugins

Workflow plugins are user-selectable and define the main document-to-card process.
Exactly one workflow plugin should be active for each generation run.

## Current workflow plugins

- `basic_text_workflow`: starter workflow for normalized TXT inputs.
  It currently supports generation plus prompt-driven refinement for selected or all cards in a run.
- `ollama_text_workflow`: structured LLM workflow for normalized TXT inputs.
  It uses centrally configured Ollama model profiles and keeps prompts inside the
  plugin. Its config currently includes:
  - `generator_model_profile`
  - `improver_model_profile`
  - `max_cards`
  - `max_blocks`
  - `max_cards_per_block`
  - `temperature`
  - `card_style`

## Rules

- Prompts must live inside plugin structures only.
- Plugins must accept and return domain-compatible data.
- Helper plugins are internal and are not user-selectable.
- Workflow plugins may expose supported improvement operations through their manifests.
