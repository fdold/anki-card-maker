import json
from urllib import error

import pytest

from frontend.api_client import ApiClientError, generate_cards_from_document


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
