import json

from backend.models import ModelGateway, ModelProfile, ModelResponse, ModelSettings
from backend.models.providers.base import ModelProvider
from backend.services.improvement_service import ImprovementService
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import GenerationRun, ImprovementAction, ImprovementBatch, RunCard
from plugins.workflows.ollama_text_workflow import OllamaTextWorkflowPlugin


class SequenceProvider(ModelProvider):
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)

    def generate(self, profile, request) -> ModelResponse:
        return ModelResponse(
            provider=profile.provider,
            model_name=profile.model_name,
            content=self._responses.pop(0),
            latency_ms=60,
        )


def test_improvement_service_appends_model_invocation_summaries(monkeypatch) -> None:
    provider = SequenceProvider(
        [
            json.dumps(
                {
                    "cards": [
                        {
                            "card_id": "card-1",
                            "front": "What are cells?",
                            "back": "Cells are the smallest basic units of life.",
                            "tags": ["clarified"],
                        }
                    ]
                }
            )
        ]
    )
    model_gateway = ModelGateway(
        settings=ModelSettings(
            profiles=[
                ModelProfile(
                    profile_id="ollama_generation_default",
                    provider="ollama",
                    model_name="qwen3:8b",
                    base_url="http://ollama-default:11434",
                    supports_structured_output=True,
                ),
                ModelProfile(
                    profile_id="ollama_improvement_default",
                    provider="ollama",
                    model_name="qwen3:8b",
                    base_url="http://ollama-default:11434",
                    supports_structured_output=True,
                ),
            ]
        ),
        providers={"ollama": provider},
    )
    workflow = OllamaTextWorkflowPlugin()
    run_repository = InMemoryRunRepository()
    improvement_service = ImprovementService(
        run_repository=run_repository,
        model_gateway=model_gateway,
    )
    run_repository.save(
        GenerationRun(
            run_id="run-1",
            plugin_id=workflow.manifest.plugin_id,
            document_id="doc-1",
            document_ids=["doc-1"],
            workflow_config={},
            cards=[
                RunCard(
                    card_id="card-1",
                    run_id="run-1",
                    front="What are cells?",
                    back="Cells are the basic unit of life.",
                    source={"section": "Biology", "position": 0},
                    tags=["generated", "ollama", "txt"],
                    workflow_plugin_id=workflow.manifest.plugin_id,
                    original_front="What are cells?",
                    original_back="Cells are the basic unit of life.",
                )
            ],
        )
    )

    monkeypatch.setattr(
        "backend.services.improvement_service.get_workflow_plugin",
        lambda _plugin_id: workflow,
    )
    updated_run = improvement_service.apply_improvements(
        ImprovementBatch(
            run_id="run-1",
            actions=[
                ImprovementAction(
                    action_type="prompt_refine_selected",
                    card_ids=["card-1"],
                    prompt="Make this more precise",
                )
            ],
        )
    )

    assert len(updated_run.model_invocations) == 1
    assert updated_run.model_invocations[0].profile_id == "ollama_improvement_default"
    assert updated_run.model_invocations[0].purpose == "card_improvement"
