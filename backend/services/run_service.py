import logging
from uuid import uuid4

from backend.models import ModelGateway, ModelInvocationRecord, build_model_gateway
from backend.services.registry import get_workflow_plugin
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import (
    GenerationRun,
    RunCard,
    RunModelInvocation,
    StoredDocument,
    utc_now,
)
from plugins.base import WorkflowExecutionContext

logger = logging.getLogger(__name__)


class RunService:
    def __init__(
        self,
        *,
        document_repository: InMemoryDocumentRepository,
        run_repository: InMemoryRunRepository | None = None,
        model_gateway: ModelGateway | None = None,
    ) -> None:
        self._document_repository = document_repository
        self._run_repository = run_repository or InMemoryRunRepository()
        self._model_gateway = model_gateway or build_model_gateway()

    def create_run(
        self,
        *,
        document_ids: list[str],
        workflow_plugin_id: str,
        workflow_config: dict[str, object] | None = None,
    ) -> GenerationRun:
        if not document_ids:
            raise ValueError("At least one document must be provided for a run.")

        workflow = get_workflow_plugin(workflow_plugin_id)
        stored_documents = [self._get_required_document(document_id) for document_id in document_ids]
        now = utc_now()
        generation_run = GenerationRun(
            run_id=str(uuid4()),
            plugin_id=workflow.manifest.plugin_id,
            document_id=stored_documents[0].document_id,
            document_ids=[document.document_id for document in stored_documents],
            status="running",
            workflow_config=workflow_config or {},
            created_at=now,
            updated_at=now,
        )
        self._run_repository.save(generation_run)

        logger.info(
            "Starting generation run %s with workflow '%s' for %s documents",
            generation_run.run_id,
            workflow.manifest.plugin_id,
            len(stored_documents),
        )
        config = workflow.config_model.model_validate(workflow_config or {})
        self._model_gateway.consume_invocations()
        context = WorkflowExecutionContext(
            run_id=generation_run.run_id,
            models=self._model_gateway,
            metadata={"workflow_plugin_id": workflow.manifest.plugin_id},
        )

        generated_cards: list[RunCard] = []
        warnings: list[str] = []
        for stored_document in stored_documents:
            if stored_document.parsed_content is None:
                raise ValueError(
                    f"Document '{stored_document.document_id}' is missing parsed content."
                )
            warnings.extend(stored_document.parsed_content.warnings)
            cards = workflow.generate_cards(
                stored_document.parsed_content,
                config,
                context,
            )
            for card in cards:
                generated_cards.append(
                    RunCard(
                        card_id=str(uuid4()),
                        run_id=generation_run.run_id,
                        front=card.front,
                        back=card.back,
                        source=card.source,
                        tags=list(card.tags),
                        workflow_plugin_id=card.workflow_plugin_id,
                        original_front=card.front,
                        original_back=card.back,
                    )
                )
        model_invocations = self._to_run_model_invocations(
            self._model_gateway.consume_invocations()
        )

        completed_at = utc_now()
        completed_run = generation_run.model_copy(
            update={
                "cards": generated_cards,
                "warnings": warnings,
                "model_invocations": model_invocations,
                "status": "completed",
                "updated_at": completed_at,
                "completed_at": completed_at,
            }
        )
        self._run_repository.update(completed_run)

        logger.info(
            "Finished generation run %s with %s cards",
            completed_run.run_id,
            len(completed_run.cards),
        )
        return completed_run

    def get_run(self, run_id: str) -> GenerationRun | None:
        return self._run_repository.get(run_id)

    def list_runs(self) -> list[GenerationRun]:
        return self._run_repository.list()

    def _get_required_document(self, document_id: str) -> StoredDocument:
        stored_document = self._document_repository.get(document_id)
        if stored_document is None:
            raise ValueError(f"Unknown document: {document_id}")
        return stored_document

    @staticmethod
    def _to_run_model_invocations(
        invocations: list[ModelInvocationRecord],
    ) -> list[RunModelInvocation]:
        return [
            RunModelInvocation(
                invocation_id=str(uuid4()),
                profile_id=invocation.profile_id,
                provider=invocation.provider,
                model_name=invocation.model_name,
                purpose=invocation.purpose,
                status=invocation.status,
                latency_ms=invocation.latency_ms,
                error_message=invocation.error_message,
            )
            for invocation in invocations
        ]
