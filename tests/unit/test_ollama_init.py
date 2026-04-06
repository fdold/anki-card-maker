import json

import httpx

from backend.models.ollama_init import (
    ensure_models_present,
    list_installed_models,
    normalize_ollama_base_url,
    pull_model,
    resolve_models_for_base_url,
)


def test_normalize_ollama_base_url_strips_api_suffix() -> None:
    assert normalize_ollama_base_url("http://ollama-default:11434/api") == (
        "http://ollama-default:11434"
    )
    assert normalize_ollama_base_url("http://ollama-default:11434/") == (
        "http://ollama-default:11434"
    )


def test_resolve_models_for_base_url_reads_unique_matching_models(tmp_path) -> None:
    profiles_file = tmp_path / "profiles.json"
    profiles_file.write_text(
        json.dumps(
            [
                {
                    "profile_id": "generation",
                    "provider": "ollama",
                    "model_name": "qwen3:8b",
                    "base_url": "http://ollama-default:11434",
                    "host_base_url": "http://host.docker.internal:11434",
                    "prefer_host_if_available": True,
                },
                {
                    "profile_id": "improvement",
                    "provider": "ollama",
                    "model_name": "qwen3:8b",
                    "base_url": "http://ollama-default:11434/api",
                    "host_base_url": "http://host.docker.internal:11434",
                    "prefer_host_if_available": True,
                },
                {
                    "profile_id": "secondary",
                    "provider": "ollama",
                    "model_name": "llama3.1:8b",
                    "base_url": "http://ollama-heavy:11434",
                },
            ]
        ),
        encoding="utf-8",
    )

    models = resolve_models_for_base_url(
        profiles_file=str(profiles_file),
        target_base_url="http://ollama-default:11434",
    )

    assert models == ["qwen3:8b"]


def test_resolve_models_for_base_url_skips_local_pull_when_host_runtime_is_available(tmp_path) -> None:
    profiles_file = tmp_path / "profiles.json"
    profiles_file.write_text(
        json.dumps(
            [
                {
                    "profile_id": "generation",
                    "provider": "ollama",
                    "model_name": "qwen3:8b",
                    "base_url": "http://ollama-default:11434",
                    "host_base_url": "http://host.docker.internal:11434",
                    "prefer_host_if_available": True,
                }
            ]
        ),
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        request_url = str(request.url)
        if request_url == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})
        raise AssertionError(f"Unexpected request URL: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        models = resolve_models_for_base_url(
            profiles_file=str(profiles_file),
            target_base_url="http://ollama-default:11434",
            client=client,
        )

    assert models == []


def test_resolve_models_for_base_url_keeps_local_pull_when_host_model_is_missing(tmp_path) -> None:
    profiles_file = tmp_path / "profiles.json"
    profiles_file.write_text(
        json.dumps(
            [
                {
                    "profile_id": "generation",
                    "provider": "ollama",
                    "model_name": "qwen3:8b",
                    "base_url": "http://ollama-default:11434",
                    "host_base_url": "http://host.docker.internal:11434",
                    "prefer_host_if_available": True,
                }
            ]
        ),
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        request_url = str(request.url)
        if request_url == "http://host.docker.internal:11434/api/tags":
            return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}]})
        if request_url == "http://ollama-default:11434/api/tags":
            return httpx.Response(200, json={"models": []})
        raise AssertionError(f"Unexpected request URL: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        models = resolve_models_for_base_url(
            profiles_file=str(profiles_file),
            target_base_url="http://ollama-default:11434",
            client=client,
        )

    assert models == ["qwen3:8b"]


def test_list_installed_models_reads_tags_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://ollama-default:11434/api/tags"
        return httpx.Response(
            200,
            json={"models": [{"name": "qwen3:8b"}, {"name": "llama3.1:8b"}]},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        models = list_installed_models(
            base_url="http://ollama-default:11434",
            client=client,
        )

    assert models == {"qwen3:8b", "llama3.1:8b"}


def test_ensure_models_present_only_pulls_missing_models() -> None:
    observed_pulls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(
                200,
                json={"models": [{"name": "qwen3:8b"}]},
            )
        observed_pulls.append(json.loads(request.content.decode("utf-8"))["model"])
        return httpx.Response(200, json={"status": "success"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        ensure_models_present(
            base_url="http://ollama-default:11434",
            model_names=["qwen3:8b", "llama3.1:8b"],
            client=client,
            logger=lambda _message: None,
        )

    assert observed_pulls == ["llama3.1:8b"]


def test_pull_model_streams_progress_updates() -> None:
    logged_messages: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://ollama-default:11434/api/pull"
        assert json.loads(request.content.decode("utf-8")) == {"model": "qwen3:8b"}
        return httpx.Response(
            200,
            text=(
                '{"status":"pulling manifest"}\n'
                '{"status":"pulling layers","completed":50,"total":100}\n'
                '{"status":"pulling layers","completed":60,"total":100}\n'
                '{"status":"success"}\n'
            ),
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        pull_model(
            base_url="http://ollama-default:11434",
            model_name="qwen3:8b",
            client=client,
            logger=logged_messages.append,
        )

    assert logged_messages[0] == "Ollama pull 'qwen3:8b': pulling manifest"
    assert "50.0%" in logged_messages[1]
    assert "60.0%" in logged_messages[2]
    assert logged_messages[-1] == "Ollama pull 'qwen3:8b': success"
