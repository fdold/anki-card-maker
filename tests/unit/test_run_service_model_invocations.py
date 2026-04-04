import json

from backend.models import ModelGateway, ModelProfile, ModelResponse, ModelSettings
from backend.models.providers.base import ModelProvider
from backend.services.document_service import DocumentService
from backend.services.run_service import RunService
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.run_repository import InMemoryRunRepository
from plugins.workflows.ollama_text_workflow import OllamaTextWorkflowPlugin


class SequenceProvider(ModelProvider):
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)

    def generate(self, profile, request) -> ModelResponse:
        return ModelResponse(
            provider=profile.provider,
            model_name=profile.model_name,
            content=self._responses.pop(0),
            latency_ms=50,
        )


def test_run_service_stores_model_invocation_summaries(monkeypatch) -> None:
    provider = SequenceProvider(
        [
            json.dumps(
                {
                    "cards": [
                        {
                            "front": "What are cells?",
                            "back": "Cells are the basic unit of life.",
                            "tags": ["biology"],
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

    assert len(generation_run.model_invocations) == 1
    assert generation_run.model_invocations[0].profile_id == "ollama_generation_default"
    assert generation_run.model_invocations[0].purpose == "card_generation"
