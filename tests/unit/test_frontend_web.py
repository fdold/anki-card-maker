from fastapi.testclient import TestClient

from frontend.api_client import ApiClientError
from frontend.web import create_app


def test_web_index_serves_html() -> None:
    client = TestClient(create_app(api_base_url="http://backend:8000"))

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Anki Card Maker" in response.text


def test_web_proxy_routes_delegate_to_frontend_api_client(monkeypatch) -> None:
    seen_base_urls = []

    def record_base_url(api_base_url: str) -> None:
        seen_base_urls.append(api_base_url)

    monkeypatch.setattr(
        "frontend.web.api_client.get_health",
        lambda api_base_url: (record_base_url(api_base_url), {"status": "ok"})[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.get_overview",
        lambda api_base_url: (record_base_url(api_base_url), {"available_workflow_plugins": []})[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.list_documents",
        lambda api_base_url: (record_base_url(api_base_url), [{"document_id": "doc-1"}])[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.upload_document",
        lambda api_base_url, payload: (
            record_base_url(api_base_url),
            {"document_id": payload["document_id"], "filename": payload["filename"]},
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.create_run",
        lambda api_base_url, payload: (
            record_base_url(api_base_url),
            {"run_id": "run-1", "document_ids": payload["document_ids"]},
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.get_run",
        lambda api_base_url, run_id: (
            record_base_url(api_base_url),
            {"run_id": run_id, "filename": "biology.csv", "media_type": "text/csv"},
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.list_run_cards",
        lambda api_base_url, run_id: (
            record_base_url(api_base_url),
            [{"card_id": f"{run_id}-card-1"}],
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.apply_improvements",
        lambda api_base_url, run_id, payload: (
            record_base_url(api_base_url),
            {"run_id": run_id, "actions": payload["actions"]},
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.list_improvements",
        lambda api_base_url, run_id: (
            record_base_url(api_base_url),
            [{"record_id": f"{run_id}-record-1"}],
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.create_export",
        lambda api_base_url, run_id, payload: (
            record_base_url(api_base_url),
            {"export_id": "export-1", "run_id": run_id, "exporter_id": payload["exporter_id"]},
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.get_export",
        lambda api_base_url, export_id: (
            record_base_url(api_base_url),
            {"export_id": export_id, "filename": "biology.csv", "media_type": "text/csv"},
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.download_export",
        lambda api_base_url, export_id, media_type: (
            record_base_url(api_base_url),
            f"{export_id}:{media_type}",
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.get_document",
        lambda api_base_url, document_id: (
            record_base_url(api_base_url),
            {"document_id": document_id},
        )[1],
    )
    monkeypatch.setattr(
        "frontend.web.api_client.list_runs",
        lambda api_base_url: (record_base_url(api_base_url), [{"run_id": "run-1"}])[1],
    )

    client = TestClient(create_app(api_base_url="http://backend:8000"))

    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/overview").json() == {"available_workflow_plugins": []}
    assert client.get("/api/documents").json() == [{"document_id": "doc-1"}]
    assert client.post(
        "/api/documents",
        json={"document_id": "doc-2", "filename": "biology.txt", "content": "Cells"},
    ).json() == {"document_id": "doc-2", "filename": "biology.txt"}
    assert client.get("/api/documents/doc-2").json() == {"document_id": "doc-2"}
    assert client.post(
        "/api/runs",
        json={
            "document_ids": ["doc-1"],
            "workflow_plugin_id": "basic_text_workflow",
            "workflow_config": {},
        },
    ).json() == {"run_id": "run-1", "document_ids": ["doc-1"]}
    assert client.get("/api/runs").json() == [{"run_id": "run-1"}]
    assert client.get("/api/runs/run-1").json()["run_id"] == "run-1"
    assert client.get("/api/runs/run-1/cards").json() == [{"card_id": "run-1-card-1"}]
    assert client.post(
        "/api/runs/run-1/improvements",
        json={"actions": [{"action_type": "rate_run", "rating": "good"}]},
    ).json()["run_id"] == "run-1"
    assert client.get("/api/runs/run-1/improvements").json() == [{"record_id": "run-1-record-1"}]
    assert client.post(
        "/api/runs/run-1/exports",
        json={"exporter_id": "csv"},
    ).json()["export_id"] == "export-1"
    assert client.get("/api/exports/export-1").json()["export_id"] == "export-1"

    download_response = client.get("/api/exports/export-1/download")
    assert download_response.status_code == 200
    assert download_response.text == "export-1:text/csv"
    assert download_response.headers["content-disposition"] == 'attachment; filename="biology.csv"'
    assert all(base_url == "http://backend:8000" for base_url in seen_base_urls)


def test_web_proxy_routes_surface_backend_errors(monkeypatch) -> None:
    def fake_get_run(_api_base_url: str, _run_id: str):
        raise ApiClientError(
            "API request failed with status 404: {\"detail\":\"Unknown run\"}",
            status_code=404,
            details='{"detail":"Unknown run"}',
        )

    monkeypatch.setattr("frontend.web.api_client.get_run", fake_get_run)

    client = TestClient(create_app(api_base_url="http://backend:8000"))

    response = client.get("/api/runs/missing-run")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown run"
