# Frontend

The frontend currently provides a CLI for the backend's resource-based API.

Available commands:

- `generate <input-file>` uploads a TXT file, creates a run, creates a CSV export, and prints or writes it.
- `overview` prints backend overview metadata.
- `upload <input-file>` uploads a TXT document and prints the stored document metadata.
- `documents` lists uploaded documents.
- `document <document-id>` fetches a single document.
- `create-run <document-id> [<document-id> ...]` creates a workflow run for existing documents.
- `runs` lists workflow runs.
- `run <run-id>` fetches a single run.
- `cards <run-id>` lists cards for a run.
- `improve <run-id>` applies one improvement action to a run.
- `improvements <run-id>` lists the improvement history for a run.
- `create-export <run-id>` creates an export artifact for a run.
- `export <export-id>` fetches export metadata.
- `download-export <export-id>` downloads an export artifact.

The shortcut `anki-card-maker path/to/file.txt` is kept as a convenience alias for `generate`.
