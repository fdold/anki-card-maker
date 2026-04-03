import logging
from dataclasses import dataclass

from backend.exporters.csv_exporter import export_cards_to_csv
from backend.services.document_service import DocumentService
from backend.services.run_service import RunService
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import ExportableAnkiCard, GenerationRun, ParsedContent

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DocumentGenerationResult:
    parsed_content: ParsedContent
    generation_run: GenerationRun
    exportable_cards: list[ExportableAnkiCard]

    def to_csv(self) -> str:
        return export_cards_to_csv(self.exportable_cards)


def generate_cards_from_document_input(
    *,
    content: str,
    workflow_plugin_id: str,
    source_type: str,
    filename: str,
    title: str | None = None,
    document_id: str | None = None,
    workflow_config: dict[str, object] | None = None,
) -> DocumentGenerationResult:
    document_repository = InMemoryDocumentRepository()
    run_repository = InMemoryRunRepository()
    document_service = DocumentService(document_repository=document_repository)
    run_service = RunService(
        document_repository=document_repository,
        run_repository=run_repository,
    )
    stored_document = document_service.upload_document(
        filename=filename,
        content=content,
        source_type=source_type,
        title=title,
        document_id=document_id,
    )
    generation_run = run_service.create_run(
        document_ids=[stored_document.document_id],
        workflow_plugin_id=workflow_plugin_id,
        workflow_config=workflow_config,
    )

    exportable_cards = [
        ExportableAnkiCard(front=card.front, back=card.back, tags=card.tags)
        for card in generation_run.cards
    ]
    if stored_document.parsed_content is None:
        raise ValueError(
            f"Document '{stored_document.document_id}' is missing parsed content."
        )
    return DocumentGenerationResult(
        parsed_content=stored_document.parsed_content,
        generation_run=generation_run,
        exportable_cards=exportable_cards,
    )
