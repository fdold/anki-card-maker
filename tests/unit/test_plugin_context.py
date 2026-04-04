import pytest

from backend.models import ModelGateway, ModelProfile, ModelSettings
from plugins.base import WorkflowExecutionContext


def test_workflow_execution_context_returns_model_gateway() -> None:
    gateway = ModelGateway(
        settings=ModelSettings(
            profiles=[
                ModelProfile(
                    profile_id="ollama_generation_default",
                    provider="ollama",
                    model_name="qwen3:8b",
                    base_url="http://ollama-default:11434",
                )
            ]
        ),
        providers={},
    )
    context = WorkflowExecutionContext(run_id="run-1", models=gateway)

    assert context.require_models() is gateway


def test_workflow_execution_context_requires_models_when_requested() -> None:
    context = WorkflowExecutionContext(run_id="run-1")

    with pytest.raises(ValueError, match="does not provide model access"):
        context.require_models()
