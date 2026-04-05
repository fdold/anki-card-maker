import json

import httpx
import pytest

from backend.models import ModelGenerationOptions, ModelMessage, ModelProfile, ModelRequest
from backend.models.base import ModelProviderError
from backend.models.providers.ollama import OllamaProvider


def build_provider_with_transport(handler) -> OllamaProvider:
    transport = httpx.MockTransport(handler)
    return OllamaProvider(
        client_factory=lambda timeout: httpx.Client(
            transport=transport,
            timeout=timeout,
        )
    )


def test_ollama_provider_maps_chat_payload_and_response_schema() -> None:
    observed_payload: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal observed_payload
        observed_payload = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "model": "qwen3:8b",
                "message": {"role": "assistant", "content": '{"cards": []}'},
                "done_reason": "stop",
                "total_duration": 2_000_000,
                "prompt_eval_count": 12,
                "eval_count": 8,
            },
        )

    provider = build_provider_with_transport(handler)

    response = provider.generate(
        ModelProfile(
            profile_id="ollama_generation_default",
            provider="ollama",
            model_name="qwen3:8b",
            base_url="http://ollama-default:11434",
            supports_structured_output=True,
        ),
        ModelRequest(
            profile_id="ollama_generation_default",
            purpose="card_generation",
            messages=[ModelMessage(role="user", content="Generate cards")],
            options=ModelGenerationOptions(temperature=0.1, max_output_tokens=128),
            response_schema={"type": "object"},
        ),
    )

    assert observed_payload["model"] == "qwen3:8b"
    assert observed_payload["stream"] is False
    assert observed_payload["format"] == {"type": "object"}
    assert observed_payload["options"]["temperature"] == 0.1
    assert observed_payload["options"]["num_predict"] == 128
    assert response.content == '{"cards": []}'
    assert response.usage is not None
    assert response.usage.total_tokens == 20
    assert response.latency_ms == 2


def test_ollama_provider_accepts_base_url_with_api_suffix() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://ollama-default:11434/api/chat"
        return httpx.Response(
            200,
            json={
                "model": "qwen3:8b",
                "message": {"role": "assistant", "content": "ok"},
            },
        )

    provider = build_provider_with_transport(handler)

    provider.generate(
        ModelProfile(
            profile_id="ollama_generation_default",
            provider="ollama",
            model_name="qwen3:8b",
            base_url="http://ollama-default:11434/api",
        ),
        ModelRequest(
            profile_id="ollama_generation_default",
            purpose="card_generation",
            messages=[ModelMessage(role="user", content="Generate cards")],
        ),
    )


def test_ollama_provider_wraps_transport_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    provider = build_provider_with_transport(handler)

    with pytest.raises(ModelProviderError, match="Ollama request failed"):
        provider.generate(
            ModelProfile(
                profile_id="ollama_generation_default",
                provider="ollama",
                model_name="qwen3:8b",
                base_url="http://ollama-default:11434",
            ),
            ModelRequest(
                profile_id="ollama_generation_default",
                purpose="card_generation",
                messages=[ModelMessage(role="user", content="Generate cards")],
            ),
        )


def test_ollama_provider_surfaces_ollama_error_body_for_missing_models() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"error": "model 'qwen3:8b' not found, try pulling it first"},
        )

    provider = build_provider_with_transport(handler)

    with pytest.raises(
        ModelProviderError,
        match="model 'qwen3:8b' not found, try pulling it first",
    ):
        provider.generate(
            ModelProfile(
                profile_id="ollama_generation_default",
                provider="ollama",
                model_name="qwen3:8b",
                base_url="http://ollama-default:11434",
            ),
            ModelRequest(
                profile_id="ollama_generation_default",
                purpose="card_generation",
                messages=[ModelMessage(role="user", content="Generate cards")],
            ),
        )
