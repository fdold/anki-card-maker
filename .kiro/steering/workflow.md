# Working Rules

## Source of Truth

Use `docs/requirements/REQUIREMENTS.md` as the single source of truth for all product, architecture, domain, plugin, parsing, export, testing, and implementation requirements.

Do not duplicate or restate project requirements elsewhere. If a requirement is missing, outdated, ambiguous, or contradicted by code or user input, update `docs/requirements/REQUIREMENTS.md` first, then implement against it.

## Development Rules

- Read the relevant requirements before making changes.
- Keep changes small, focused, and commit-sized.
- Respect the module boundaries and constraints defined in the requirements.
- Prefer existing project patterns over new abstractions.
- Do not introduce broad refactors unless directly required by the current task.
- Preserve user changes already present in the working tree.
- Add or update tests for changed core behavior whenever feasible.
- Update documentation or requirements when behavior, interfaces, configuration, or architecture changes.
- Keep Docker and Docker Compose workflows working unless the task explicitly changes them.

## Requirement Handling

- Treat requirement IDs in `docs/requirements/REQUIREMENTS.md` as the canonical references for decisions.
- When implementing a feature or fix, identify the relevant requirement IDs and keep the change aligned with them.
- If requirements conflict, stop and resolve the conflict in the requirements document before implementing.
- If the user gives a new requirement, record it in `docs/requirements/REQUIREMENTS.md`.

## Definition of Done

A task is done only when the implementation, tests, documentation, and requirements remain consistent with `docs/requirements/REQUIREMENTS.md`.
