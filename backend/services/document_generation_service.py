import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from backend.exporters.csv_exporter import export_cards_to_csv
from backend.services.registry import get_parser_for_source_type, get_workflow_plugin
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
    parser = get_parser_for_source_type(source_type)
    workflow = get_workflow_plugin(workflow_plugin_id)
    resolved_document_id = document_id or str(uuid4())
    resolved_title = title or Path(filename).stem

    logger.info(
        "Parsing document '%s' as source_type '%s'",
        resolved_title,
        source_type,
    )
    parsed_content = parser(
        document_id=resolved_document_id,
        title=resolved_title,
        text=content,
    )

    logger.info(
        "Generating cards with workflow '%s'",
        workflow.manifest.plugin_id,
    )
    config = workflow.config_model.model_validate(workflow_config or {})
    cards = workflow.generate_cards(parsed_content, config)

    exportable_cards = [
        ExportableAnkiCard(front=card.front, back=card.back, tags=card.tags)
        for card in cards
    ]
    generation_run = GenerationRun(
        run_id=str(uuid4()),
        plugin_id=workflow.manifest.plugin_id,
        document_id=parsed_content.document.document_id,
        cards=cards,
        warnings=list(parsed_content.warnings),
    )

    logger.info(
        "Finished generation run %s with %s cards",
        generation_run.run_id,
        len(generation_run.cards),
    )
    return DocumentGenerationResult(
        parsed_content=parsed_content,
        generation_run=generation_run,
        exportable_cards=exportable_cards,
    )
