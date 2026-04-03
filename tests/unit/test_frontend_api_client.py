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
    def fake_urlopen(api_request):
        assert api_request.full_url == "http://localhost:8000/generate/document"
        assert json.loads(api_request.data.decode("utf-8"))["workflow_plugin_id"] == "basic_text_workflow"
        assert json.loads(api_request.data.decode("utf-8"))["output_type"] == "csv"
        assert api_request.headers["Accept"] == "text/csv"
        return DummyResponse("front,back,tags\nQ,A,generated")

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
