from pydantic import BaseModel

from backend.models import ModelGateway, ModelSettings
from backend.services.improvement_service import ImprovementService
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import (
    GenerationRun,
    ImprovementAction,
    ImprovementBatch,
    PluginManifest,
    RunCard,
    WorkflowImprovementRequest,
)
from plugins.base import WorkflowExecutionContext, WorkflowPlugin


class ContextWorkflowConfig(BaseModel):
    pass


class ContextCapturingImprovementWorkflow(WorkflowPlugin[ContextWorkflowConfig]):
    config_model = ContextWorkflowConfig
    base_manifest = PluginManifest(
        plugin_id="context_improvement_workflow",
        name="Context Improvement Workflow",
        plugin_type="workflow",
        description="Captures improvement context.",
        supported_input_types=["txt"],
        supported_operations=["prompt_refine_selected"],
    )

    def __init__(self) -> None:
        self.received_context: WorkflowExecutionContext | None = None

    def generate_cards(self, parsed_content, config, context=None):
        raise NotImplementedError

    def apply_improvement(
        self,
        request: WorkflowImprovementRequest,
        config: ContextWorkflowConfig,
        context: WorkflowExecutionContext | None = None,
    ) -> list[RunCard]:
        self.received_context = context
        return [
            card.model_copy(update={"back": f"{card.back} Improved.", "status": "edited"})
            for card in request.cards
        ]


def test_improvement_service_passes_workflow_execution_context(monkeypatch) -> None:
    workflow = ContextCapturingImprovementWorkflow()
    model_gateway = ModelGateway(settings=ModelSettings(), providers={})
    run_repository = InMemoryRunRepository()
    improvement_service = ImprovementService(
        run_repository=run_repository,
        model_gateway=model_gateway,
    )
    run = GenerationRun(
        run_id="run-1",
        plugin_id=workflow.manifest.plugin_id,
        document_id="doc-1",
        document_ids=["doc-1"],
        workflow_config={},
        cards=[
            RunCard(
                card_id="card-1",
                run_id="run-1",
                front="Question",
                back="Answer",
                source={"section": "Biology", "position": 0},
                workflow_plugin_id=workflow.manifest.plugin_id,
                original_front="Question",
                original_back="Answer",
            )
        ],
    )
    run_repository.save(run)

    monkeypatch.setattr(
        "backend.services.improvement_service.get_workflow_plugin",
        lambda _plugin_id: workflow,
    )
    updated_run = improvement_service.apply_improvements(
        ImprovementBatch(
            run_id=run.run_id,
            actions=[
                ImprovementAction(
                    action_type="prompt_refine_selected",
                    card_ids=["card-1"],
                    prompt="Improve this answer",
                )
            ],
        )
    )

    assert workflow.received_context is not None
    assert workflow.received_context.run_id == run.run_id
    assert workflow.received_context.models is model_gateway
    assert updated_run.cards[0].back == "Answer Improved."
