# Plugins

## Workflow plugins

Workflow plugins are user-selectable and define the main document-to-card process.
Exactly one workflow plugin should be active for each generation run.

## Current starter plugin

- `basic_text_workflow`: starter workflow for normalized TXT inputs.
  It currently supports generation plus prompt-driven refinement for selected or all cards in a run.

## Rules

- Prompts must live inside plugin structures only.
- Plugins must accept and return domain-compatible data.
- Helper plugins are internal and are not user-selectable.
- Workflow plugins may expose supported improvement operations through their manifests.
