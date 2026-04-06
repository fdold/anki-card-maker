import httpx

from backend.models import ModelProfile
from backend.models.ollama_runtime import (
    describe_ollama_runtime,
    is_ollama_available,
    resolve_ollama_base_url,
)


def test_is_ollama_available_returns_true_for_healthy_tags_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://host.docker.internal:11434/api/tags"
        return httpx.Response(200, json={"models": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert is_ollama_available(
            base_url="http://host.docker.internal:11434",
            client=client,
        )


def test_describe_ollama_runtime_prefers_host_when_model_is_available() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        request_url = str(request.url)
        if request_url == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})
        raise AssertionError(f"Unexpected request URL: {request.url}")

    profile = ModelProfile(
        profile_id="ollama_generation_default",
        provider="ollama",
        model_name="qwen3:8b",
        base_url="http://ollama-default:11434",
        host_base_url="http://host.docker.internal:11434",
        prefer_host_if_available=True,
    )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        runtime_status = describe_ollama_runtime(profile=profile, client=client)

    assert runtime_status.selected_runtime == "host"
    assert runtime_status.status == "ready"
    assert runtime_status.selected_base_url == "http://host.docker.internal:11434"


def test_describe_ollama_runtime_falls_back_to_container_when_host_model_missing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        request_url = str(request.url)
        if request_url == "http://ollama-default:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})
        if request_url == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}]})
        raise AssertionError(f"Unexpected request URL: {request.url}")

    profile = ModelProfile(
        profile_id="ollama_generation_default",
        provider="ollama",
        model_name="qwen3:8b",
        base_url="http://ollama-default:11434",
        host_base_url="http://host.docker.internal:11434",
        prefer_host_if_available=True,
    )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        runtime_status = describe_ollama_runtime(profile=profile, client=client)

    assert runtime_status.selected_runtime == "container"
    assert runtime_status.status == "ready"
    assert runtime_status.message.startswith("Host Ollama at http://host.docker.internal:11434")


def test_describe_ollama_runtime_marks_missing_model_when_no_ready_runtime_exists() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        request_url = str(request.url)
        if request_url == "http://ollama-default:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}]})
        if request_url == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}]})
        raise AssertionError(f"Unexpected request URL: {request.url}")

    profile = ModelProfile(
        profile_id="ollama_generation_default",
        provider="ollama",
        model_name="qwen3:8b",
        base_url="http://ollama-default:11434",
        host_base_url="http://host.docker.internal:11434",
        prefer_host_if_available=True,
    )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        runtime_status = describe_ollama_runtime(profile=profile, client=client)

    assert runtime_status.selected_runtime == "host"
    assert runtime_status.status == "model_missing"
    assert runtime_status.selected_model_available is False


def test_resolve_ollama_base_url_prefers_host_when_available() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        request_url = str(request.url)
        if request_url == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})
        raise AssertionError(f"Unexpected request URL: {request.url}")

    profile = ModelProfile(
        profile_id="ollama_generation_default",
        provider="ollama",
        model_name="qwen3:8b",
        base_url="http://ollama-default:11434",
        host_base_url="http://host.docker.internal:11434",
        prefer_host_if_available=True,
    )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        resolved_base_url = resolve_ollama_base_url(profile=profile, client=client)

    assert resolved_base_url == "http://host.docker.internal:11434"


def test_resolve_ollama_base_url_falls_back_to_container_when_host_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        request_url = str(request.url)
        if request_url == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(500, json={"error": "not available"})
        if request_url == "http://ollama-default:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})
        raise AssertionError(f"Unexpected request URL: {request.url}")

    profile = ModelProfile(
        profile_id="ollama_generation_default",
        provider="ollama",
        model_name="qwen3:8b",
        base_url="http://ollama-default:11434",
        host_base_url="http://host.docker.internal:11434",
        prefer_host_if_available=True,
    )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        resolved_base_url = resolve_ollama_base_url(profile=profile, client=client)

    assert resolved_base_url == "http://ollama-default:11434"
