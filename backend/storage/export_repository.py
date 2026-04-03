from domain.models import ExportArtifact


class InMemoryExportRepository:
    """Temporary repository until persistent export storage is introduced."""

    def __init__(self) -> None:
        self._exports: dict[str, ExportArtifact] = {}

    def save(self, export_artifact: ExportArtifact) -> None:
        self._exports[export_artifact.export_id] = export_artifact

    def get(self, export_id: str) -> ExportArtifact | None:
        return self._exports.get(export_id)

    def list(self) -> list[ExportArtifact]:
        return list(self._exports.values())
