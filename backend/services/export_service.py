import logging
from uuid import uuid4

from backend.services.registry import get_exporter
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.export_repository import InMemoryExportRepository
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import ExportArtifact, ExportableAnkiCard, RunCard, utc_now

logger = logging.getLogger(__name__)


class ExportService:
    def __init__(
        self,
        *,
        run_repository: InMemoryRunRepository,
        export_repository: InMemoryExportRepository | None = None,
        document_repository: InMemoryDocumentRepository | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._export_repository = export_repository or InMemoryExportRepository()
        self._document_repository = document_repository

    def create_export(
        self,
        *,
        run_id: str,
        exporter_id: str,
        card_ids: list[str] | None = None,
    ) -> ExportArtifact:
        run = self._run_repository.get(run_id)
        if run is None:
            raise ValueError(f"Unknown run: {run_id}")

        exporter = get_exporter(exporter_id)
        selected_cards = self._get_exportable_cards(run.cards, card_ids or [])
        exportable_cards = [
            ExportableAnkiCard(front=card.front, back=card.back, tags=list(card.tags))
            for card in selected_cards
        ]
        content = exporter.export(exportable_cards)
        completed_at = utc_now()
        export_artifact = ExportArtifact(
            export_id=str(uuid4()),
            run_id=run.run_id,
            exporter_id=exporter.exporter_id,
            card_ids=[card.card_id for card in selected_cards],
            filename=self._build_filename(run.document_id, run.run_id, exporter.file_extension),
            media_type=exporter.media_type,
            content=content,
            status="completed",
            created_at=completed_at,
            completed_at=completed_at,
        )
        self._export_repository.save(export_artifact)
        logger.info(
            "Created export %s for run %s with exporter '%s'",
            export_artifact.export_id,
            run.run_id,
            exporter.exporter_id,
        )
        return export_artifact

    def get_export(self, export_id: str) -> ExportArtifact | None:
        return self._export_repository.get(export_id)

    def _get_exportable_cards(
        self,
        cards: list[RunCard],
        requested_card_ids: list[str],
    ) -> list[RunCard]:
        exportable_cards = [card for card in cards if card.status != "deleted"]
        if not requested_card_ids:
            return exportable_cards

        selected_cards: list[RunCard] = []
        exportable_by_id = {card.card_id: card for card in exportable_cards}
        for card_id in requested_card_ids:
            try:
                selected_cards.append(exportable_by_id[card_id])
            except KeyError as exc:
                raise ValueError(f"Card '{card_id}' is not exportable.") from exc
        return selected_cards

    def _build_filename(
        self,
        document_id: str | None,
        run_id: str,
        file_extension: str,
    ) -> str:
        if document_id is not None and self._document_repository is not None:
            stored_document = self._document_repository.get(document_id)
            if stored_document is not None:
                return f"{stored_document.title}.{file_extension}"
        return f"run-{run_id}.{file_extension}"
