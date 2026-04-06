import json
import logging

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
            text="\n".join(
                [
                    json.dumps(
                        {
                            "model": "qwen3:8b",
                            "message": {"role": "assistant", "content": '{"cards": '},
                            "done": False,
                        }
                    ),
                    json.dumps(
                        {
                            "model": "qwen3:8b",
                            "message": {"role": "assistant", "content": "[]}"},
                            "done": True,
                            "done_reason": "stop",
                            "total_duration": 2_000_000,
                            "prompt_eval_count": 12,
                            "eval_count": 8,
                        }
                    ),
                ]
            ),
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
    assert observed_payload["stream"] is True
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
            text=json.dumps(
                {
                    "model": "qwen3:8b",
                    "message": {"role": "assistant", "content": "ok"},
                    "done": True,
                }
            ),
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


def test_ollama_provider_emits_request_lifecycle_logs(caplog) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=json.dumps(
                {
                    "model": "qwen3:8b",
                    "message": {"role": "assistant", "content": "ok"},
                    "done": True,
                }
            ),
        )

    provider = build_provider_with_transport(handler)

    with caplog.at_level(logging.INFO):
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

    assert "Starting Ollama request" in caplog.text
    assert "Completed Ollama request" in caplog.text


def test_ollama_provider_uses_host_runtime_when_available() -> None:
    observed_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed_urls.append(str(request.url))
        if str(request.url) == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})
        if str(request.url) == "http://host.docker.internal:11434/api/chat":
            return httpx.Response(
                200,
                text=json.dumps(
                    {
                        "model": "qwen3:8b",
                        "message": {"role": "assistant", "content": "ok"},
                        "done": True,
                    }
                ),
            )
        raise AssertionError(f"Unexpected request URL: {request.url}")

    provider = build_provider_with_transport(handler)

    provider.generate(
        ModelProfile(
            profile_id="ollama_generation_default",
            provider="ollama",
            model_name="qwen3:8b",
            base_url="http://ollama-default:11434",
            host_base_url="http://host.docker.internal:11434",
            prefer_host_if_available=True,
        ),
        ModelRequest(
            profile_id="ollama_generation_default",
            purpose="card_generation",
            messages=[ModelMessage(role="user", content="Generate cards")],
        ),
    )

    assert observed_urls == [
        "http://host.docker.internal:11434/api/tags",
        "http://host.docker.internal:11434/api/chat",
    ]


def test_ollama_provider_rechecks_host_runtime_after_container_fallback() -> None:
    observed_urls: list[str] = []
    probe_results = iter([500, 200])

    def handler(request: httpx.Request) -> httpx.Response:
        observed_urls.append(str(request.url))
        request_url = str(request.url)
        if request_url == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(next(probe_results), json={"models": [{"name": "qwen3:8b"}]})
        if request_url == "http://ollama-default:11434/api/chat":
            return httpx.Response(
                200,
                text=json.dumps(
                    {
                        "model": "qwen3:8b",
                        "message": {"role": "assistant", "content": "container"},
                        "done": True,
                    }
                ),
            )
        if request_url == "http://host.docker.internal:11434/api/chat":
            return httpx.Response(
                200,
                text=json.dumps(
                    {
                        "model": "qwen3:8b",
                        "message": {"role": "assistant", "content": "host"},
                        "done": True,
                    }
                ),
            )
        raise AssertionError(f"Unexpected request URL: {request.url}")

    provider = build_provider_with_transport(handler)
    profile = ModelProfile(
        profile_id="ollama_generation_default",
        provider="ollama",
        model_name="qwen3:8b",
        base_url="http://ollama-default:11434",
        host_base_url="http://host.docker.internal:11434",
        prefer_host_if_available=True,
    )
    request = ModelRequest(
        profile_id="ollama_generation_default",
        purpose="card_generation",
        messages=[ModelMessage(role="user", content="Generate cards")],
    )

    first_response = provider.generate(profile, request)
    second_response = provider.generate(profile, request)

    assert first_response.content == "container"
    assert second_response.content == "host"
    assert observed_urls == [
        "http://host.docker.internal:11434/api/tags",
        "http://ollama-default:11434/api/chat",
        "http://host.docker.internal:11434/api/tags",
        "http://host.docker.internal:11434/api/chat",
    ]
