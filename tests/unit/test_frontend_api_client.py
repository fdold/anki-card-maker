import json
from urllib import error

import pytest

from frontend.api_client import (
    ApiClientError,
    apply_improvements,
    create_export,
    create_run,
    download_export,
    generate_cards_from_document,
    get_document,
    get_export,
    get_overview,
    get_run,
    list_improvements,
    list_documents,
    list_run_cards,
    list_runs,
    upload_document,
)


class DummyResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_generate_cards_from_document_calls_api(monkeypatch) -> None:
    requests_seen = []

    def fake_urlopen(api_request):
        requests_seen.append(api_request)
        if api_request.full_url == "http://localhost:8000/documents":
            payload = json.loads(api_request.data.decode("utf-8"))
            assert payload["filename"] == "biology.txt"
            return DummyResponse('{"document_id": "doc-1"}')
        if api_request.full_url == "http://localhost:8000/runs":
            payload = json.loads(api_request.data.decode("utf-8"))
            assert payload["document_ids"] == ["doc-1"]
            assert payload["workflow_plugin_id"] == "basic_text_workflow"
            return DummyResponse('{"run_id": "run-1"}')
        if api_request.full_url == "http://localhost:8000/runs/run-1/exports":
            payload = json.loads(api_request.data.decode("utf-8"))
            assert payload["exporter_id"] == "csv"
            return DummyResponse('{"export_id": "export-1"}')
        if api_request.full_url == "http://localhost:8000/exports/export-1/download":
            assert api_request.headers["Accept"] == "text/csv"
            return DummyResponse("front,back,tags\nQ,A,generated")
        raise AssertionError(f"Unexpected request URL: {api_request.full_url}")

    monkeypatch.setattr("frontend.api_client.request.urlopen", fake_urlopen)

    response = generate_cards_from_document(
        "http://localhost:8000",
        {
            "filename": "biology.txt",
            "content": "Cells",
            "workflow_plugin_id": "basic_text_workflow",
            "output_type": "csv",
        },
    )

    assert "front,back,tags" in response
    assert [request.full_url for request in requests_seen] == [
        "http://localhost:8000/documents",
        "http://localhost:8000/runs",
        "http://localhost:8000/runs/run-1/exports",
        "http://localhost:8000/exports/export-1/download",
    ]


def test_generate_cards_from_document_wraps_http_errors(monkeypatch) -> None:
    def fake_urlopen(_api_request):
        raise error.URLError("connection refused")

    monkeypatch.setattr("frontend.api_client.request.urlopen", fake_urlopen)

    with pytest.raises(ApiClientError, match="Could not reach backend API"):
        generate_cards_from_document(
            "http://localhost:8000",
            {
                "filename": "biology.txt",
                "content": "Cells",
                "workflow_plugin_id": "basic_text_workflow",
                "output_type": "csv",
            },
        )


def test_generate_cards_from_document_rejects_unsupported_output_types() -> None:
    with pytest.raises(ApiClientError, match="Unsupported output type"):
        generate_cards_from_document(
            "http://localhost:8000",
            {
                "filename": "biology.txt",
                "content": "Cells",
                "workflow_plugin_id": "basic_text_workflow",
                "output_type": "json",
            },
        )


def test_resource_client_functions_call_expected_endpoints(monkeypatch) -> None:
    def fake_urlopen(api_request):
        if api_request.full_url == "http://localhost:8000/overview":
            assert api_request.get_method() == "GET"
            return DummyResponse('{"status": "ok"}')
        if api_request.full_url == "http://localhost:8000/documents":
            if api_request.get_method() == "POST":
                payload = json.loads(api_request.data.decode("utf-8"))
                assert payload["filename"] == "biology.txt"
                return DummyResponse('{"document_id": "doc-1"}')
            return DummyResponse('[{"document_id": "doc-1"}]')
        if api_request.full_url == "http://localhost:8000/documents/doc-1":
            return DummyResponse('{"document_id": "doc-1"}')
        if api_request.full_url == "http://localhost:8000/runs":
            if api_request.get_method() == "POST":
                payload = json.loads(api_request.data.decode("utf-8"))
                assert payload["document_ids"] == ["doc-1"]
                return DummyResponse('{"run_id": "run-1"}')
            return DummyResponse('[{"run_id": "run-1"}]')
        if api_request.full_url == "http://localhost:8000/runs/run-1":
            return DummyResponse('{"run_id": "run-1"}')
        if api_request.full_url == "http://localhost:8000/runs/run-1/cards":
            return DummyResponse('[{"card_id": "card-1"}]')
        if api_request.full_url == "http://localhost:8000/runs/run-1/improvements":
            if api_request.get_method() == "POST":
                payload = json.loads(api_request.data.decode("utf-8"))
                assert payload["actions"][0]["action_type"] == "rate_run"
                return DummyResponse('{"run_id": "run-1"}')
            return DummyResponse('[{"record_id": "record-1"}]')
        if api_request.full_url == "http://localhost:8000/runs/run-1/exports":
            payload = json.loads(api_request.data.decode("utf-8"))
            assert payload["exporter_id"] == "csv"
            return DummyResponse('{"export_id": "export-1"}')
        if api_request.full_url == "http://localhost:8000/exports/export-1":
            return DummyResponse('{"export_id": "export-1"}')
        if api_request.full_url == "http://localhost:8000/exports/export-1/download":
            return DummyResponse("front,back,tags\nQ,A,tag\n")
        raise AssertionError(f"Unexpected request URL: {api_request.full_url}")

    monkeypatch.setattr("frontend.api_client.request.urlopen", fake_urlopen)

    assert get_overview("http://localhost:8000") == {"status": "ok"}
    assert upload_document(
        "http://localhost:8000",
        {"filename": "biology.txt", "content": "Cells"},
    ) == {"document_id": "doc-1"}
    assert list_documents("http://localhost:8000") == [{"document_id": "doc-1"}]
    assert get_document("http://localhost:8000", "doc-1") == {"document_id": "doc-1"}
    assert create_run(
        "http://localhost:8000",
        {
            "document_ids": ["doc-1"],
            "workflow_plugin_id": "basic_text_workflow",
            "workflow_config": {},
        },
    ) == {"run_id": "run-1"}
    assert list_runs("http://localhost:8000") == [{"run_id": "run-1"}]
    assert get_run("http://localhost:8000", "run-1") == {"run_id": "run-1"}
    assert list_run_cards("http://localhost:8000", "run-1") == [{"card_id": "card-1"}]
    assert apply_improvements(
        "http://localhost:8000",
        "run-1",
        {"actions": [{"action_type": "rate_run", "rating": "good"}]},
    ) == {"run_id": "run-1"}
    assert list_improvements("http://localhost:8000", "run-1") == [{"record_id": "record-1"}]
    assert create_export(
        "http://localhost:8000",
        "run-1",
        {"exporter_id": "csv"},
    ) == {"export_id": "export-1"}
    assert get_export("http://localhost:8000", "export-1") == {"export_id": "export-1"}
    assert download_export("http://localhost:8000", "export-1") == "front,back,tags\nQ,A,tag\n"
