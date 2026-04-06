import json
import logging

from pydantic import BaseModel

from backend.models import ModelGateway, ModelProfile, ModelResponse, ModelSettings
from backend.models.providers.base import ModelProvider
from backend.pipeline.parsers.txt_parser import parse_txt_document
from domain.models import RunCard, WorkflowImprovementRequest
from plugins.base import WorkflowExecutionContext
from plugins.workflows.ollama_text_workflow import (
    OllamaTextWorkflowConfig,
    OllamaTextWorkflowPlugin,
)


class SequenceProvider(ModelProvider):
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.requests = []

    def generate(self, profile, request) -> ModelResponse:
        self.requests.append(request)
        return ModelResponse(
            provider=profile.provider,
            model_name=profile.model_name,
            content=self._responses.pop(0),
        )


def build_gateway(provider: SequenceProvider) -> ModelGateway:
    return ModelGateway(
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


def test_ollama_text_workflow_generates_traceable_cards(caplog) -> None:
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
    plugin = OllamaTextWorkflowPlugin()
    parsed = parse_txt_document("doc-1", "Biology", "Cells are the basic unit of life.")
    context = WorkflowExecutionContext(
        run_id="run-1",
        models=build_gateway(provider),
    )

    with caplog.at_level(logging.INFO):
        cards = plugin.generate_cards(
            parsed,
            OllamaTextWorkflowConfig(max_cards=5, max_blocks=1, max_cards_per_block=1),
            context,
        )

    assert len(cards) == 1
    assert cards[0].workflow_plugin_id == plugin.manifest.plugin_id
    assert cards[0].source.section == "Biology"
    assert "generated" in cards[0].tags
    assert "ollama" in cards[0].tags
    assert "biology" in cards[0].tags
    assert provider.requests[0].response_schema is not None
    assert "Starting Ollama workflow generation" in caplog.text
    assert "Finished block generation" in caplog.text


def test_ollama_text_workflow_applies_prompt_refinement() -> None:
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
    plugin = OllamaTextWorkflowPlugin()
    context = WorkflowExecutionContext(
        run_id="run-1",
        models=build_gateway(provider),
    )

    refined_cards = plugin.apply_improvement(
        WorkflowImprovementRequest(
            action_type="prompt_refine_selected",
            run_id="run-1",
            prompt="Make this more precise",
            cards=[
                RunCard(
                    card_id="card-1",
                    run_id="run-1",
                    front="What are cells?",
                    back="Cells are the basic unit of life.",
                    source={"section": "Biology", "position": 0},
                    tags=["generated", "ollama", "txt"],
                    workflow_plugin_id=plugin.manifest.plugin_id,
                    original_front="What are cells?",
                    original_back="Cells are the basic unit of life.",
                )
            ],
        ),
        OllamaTextWorkflowConfig(),
        context,
    )

    assert len(refined_cards) == 1
    assert refined_cards[0].back == "Cells are the smallest basic units of life."
    assert refined_cards[0].status == "edited"
    assert "improved" in refined_cards[0].tags
    assert "clarified" in refined_cards[0].tags


def test_ollama_text_workflow_requires_execution_context() -> None:
    plugin = OllamaTextWorkflowPlugin()
    parsed = parse_txt_document("doc-1", "Biology", "Cells are the basic unit of life.")

    try:
        plugin.generate_cards(parsed, OllamaTextWorkflowConfig())
    except ValueError as exc:
        assert "requires a workflow execution context" in str(exc)
    else:
        raise AssertionError("Expected the workflow to require an execution context.")
