import pytest
from pydantic import BaseModel

from backend.models import (
    ModelGateway,
    ModelGenerationOptions,
    ModelMessage,
    ModelProfile,
    ModelProviderError,
    ModelResponse,
    ModelResponseValidationError,
    ModelSettings,
)
from backend.models.providers.base import ModelProvider


class CardBatchResponse(BaseModel):
    cards: list[dict[str, str]]


class FakeProvider(ModelProvider):
    def __init__(self, content: str = '{"cards": [{"front": "Q", "back": "A"}]}') -> None:
        self.content = content
        self.last_request = None

    def generate(self, profile, request) -> ModelResponse:
        self.last_request = request
        return ModelResponse(
            provider=profile.provider,
            model_name=profile.model_name,
            content=self.content,
        )


class ExplodingProvider(ModelProvider):
    def generate(self, profile, request) -> ModelResponse:
        raise ModelProviderError("boom")


def build_gateway(provider: ModelProvider) -> ModelGateway:
    return ModelGateway(
        settings=ModelSettings(
            profiles=[
                ModelProfile(
                    profile_id="ollama_generation_default",
                    provider="ollama",
                    model_name="qwen3:8b",
                    base_url="http://ollama-default:11434",
                    default_options=ModelGenerationOptions(temperature=0.1),
                    supports_structured_output=True,
                )
            ]
        ),
        providers={"ollama": provider},
    )


def test_model_gateway_merges_profile_defaults_with_request_options() -> None:
    provider = FakeProvider()
    gateway = build_gateway(provider)

    gateway.generate_text(
        profile_id="_default",
        purpose="card_generation",
        messages=[ModelMessage(role="user", content="Generate cards")],
        options=ModelGenerationOptions(max_output_tokens=256),
    )

    assert provider.last_request is not None
    assert provider.last_request.options.temperature == 0.1
    assert provider.last_request.options.max_output_tokens == 256


def test_model_gateway_validates_structured_responses() -> None:
    gateway = build_gateway(FakeProvider())

    result = gateway.generate_structured(
        profile_id="ollama_generation_default",
        purpose="card_generation",
        messages=[ModelMessage(role="user", content="Generate cards")],
        response_model=CardBatchResponse,
    )

    assert result.parsed.cards[0]["front"] == "Q"
    assert result.invocation.status == "completed"
    assert len(gateway.list_invocations()) == 1


def test_model_gateway_marks_failed_structured_validation() -> None:
    gateway = build_gateway(FakeProvider(content="not-json"))

    with pytest.raises(ModelResponseValidationError):
        gateway.generate_structured(
            profile_id="ollama_generation_default",
            purpose="card_generation",
            messages=[ModelMessage(role="user", content="Generate cards")],
            response_model=CardBatchResponse,
        )

    assert gateway.list_invocations()[-1].status == "failed"


def test_model_gateway_records_provider_failures() -> None:
    gateway = build_gateway(ExplodingProvider())

    with pytest.raises(ModelProviderError):
        gateway.generate_text(
            profile_id="ollama_generation_default",
            purpose="card_generation",
            messages=[ModelMessage(role="user", content="Generate cards")],
        )

    assert gateway.list_invocations()[-1].status == "failed"
