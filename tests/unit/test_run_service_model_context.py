from pydantic import BaseModel

from backend.models import ModelGateway, ModelSettings
from backend.services.document_service import DocumentService
from backend.services.run_service import RunService
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import CardCandidate, ParsedContent, PluginManifest
from plugins.base import WorkflowExecutionContext, WorkflowPlugin


class ContextWorkflowConfig(BaseModel):
    pass


class ContextCapturingWorkflow(WorkflowPlugin[ContextWorkflowConfig]):
    config_model = ContextWorkflowConfig
    base_manifest = PluginManifest(
        plugin_id="context_workflow",
        name="Context Workflow",
        plugin_type="workflow",
        description="Captures the workflow execution context.",
        supported_input_types=["txt"],
    )

    def __init__(self) -> None:
        self.received_context: WorkflowExecutionContext | None = None

    def generate_cards(
        self,
        parsed_content: ParsedContent,
        config: ContextWorkflowConfig,
        context: WorkflowExecutionContext | None = None,
    ) -> list[CardCandidate]:
        self.received_context = context
        first_block = parsed_content.blocks[0]
        return [
            CardCandidate(
                front="Question",
                back=first_block.text,
                source=first_block.source,
                workflow_plugin_id=self.manifest.plugin_id,
            )
        ]


def test_run_service_passes_workflow_execution_context(monkeypatch) -> None:
    workflow = ContextCapturingWorkflow()
    model_gateway = ModelGateway(settings=ModelSettings(), providers={})
    document_repository = InMemoryDocumentRepository()
    run_repository = InMemoryRunRepository()
    document_service = DocumentService(document_repository=document_repository)
    run_service = RunService(
        document_repository=document_repository,
        run_repository=run_repository,
        model_gateway=model_gateway,
    )

    monkeypatch.setattr("backend.services.run_service.get_workflow_plugin", lambda _plugin_id: workflow)
    stored_document = document_service.upload_document(
        filename="biology.txt",
        content="Cells are the basic unit of life.",
        document_id="doc-1",
    )

    generation_run = run_service.create_run(
        document_ids=[stored_document.document_id],
        workflow_plugin_id=workflow.manifest.plugin_id,
    )

    assert workflow.received_context is not None
    assert workflow.received_context.run_id == generation_run.run_id
    assert workflow.received_context.models is model_gateway
