from fastapi.testclient import TestClient

from backend.models import ModelProviderError
from backend.api.main import create_app


def test_documents_endpoints_store_and_return_uploaded_documents() -> None:
    client = TestClient(create_app())

    upload_response = client.post(
        "/documents",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.\n\nDNA stores genetic information.",
        },
    )

    assert upload_response.status_code == 201
    payload = upload_response.json()
    document_id = payload["document_id"]
    assert payload["filename"] == "biology.txt"
    assert payload["source_type"] == "txt"
    assert payload["block_count"] == 2
    assert payload["has_parsed_content"] is True

    list_response = client.get("/documents")
    assert list_response.status_code == 200
    assert any(document["document_id"] == document_id for document in list_response.json())

    detail_response = client.get(f"/documents/{document_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["document_id"] == document_id


def test_overview_exposes_workflows_exporters_and_api_resources() -> None:
    client = TestClient(create_app())

    response = client.get("/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_input_formats"] == ["txt"]
    assert payload["available_workflow_plugins"][0]["plugin_id"] == "basic_text_workflow"
    assert "prompt_refine_selected" in payload["available_workflow_plugins"][0]["supported_operations"]
    assert any(
        plugin["plugin_id"] == "ollama_text_workflow"
        for plugin in payload["available_workflow_plugins"]
    )
    assert payload["available_model_profiles"] == []
    assert payload["available_exporters"][0]["exporter_id"] == "csv"
    assert payload["available_exporters"][0]["media_type"] == "text/csv"
    assert "/documents" in payload["api_resources"]
    assert "/runs/{run_id}/exports" in payload["api_resources"]


def test_runs_endpoints_create_run_and_expose_cards() -> None:
    client = TestClient(create_app())
    upload_response = client.post(
        "/documents",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.\n\nDNA stores genetic information.",
        },
    )
    document_id = upload_response.json()["document_id"]

    run_response = client.post(
        "/runs",
        json={
            "document_ids": [document_id],
            "workflow_plugin_id": "basic_text_workflow",
            "workflow_config": {"max_cards": 5},
        },
    )

    assert run_response.status_code == 201
    run_payload = run_response.json()
    run_id = run_payload["run_id"]
    assert run_payload["document_ids"] == [document_id]
    assert run_payload["status"] == "completed"
    assert run_payload["card_count"] == 2

    list_response = client.get("/runs")
    assert list_response.status_code == 200
    assert any(run["run_id"] == run_id for run in list_response.json())

    detail_response = client.get(f"/runs/{run_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["run_id"] == run_id

    cards_response = client.get(f"/runs/{run_id}/cards")
    assert cards_response.status_code == 200
    cards = cards_response.json()
    assert len(cards) == 2
    assert cards[0]["run_id"] == run_id
    assert cards[0]["original_back"] == cards[0]["back"]


def test_runs_endpoint_surfaces_ollama_provider_errors(monkeypatch) -> None:
    client = TestClient(create_app())
    upload_response = client.post(
        "/documents",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.",
        },
    )
    document_id = upload_response.json()["document_id"]

    def explode_create_run(*args, **kwargs):
        raise ModelProviderError(
            "Ollama request failed for model 'qwen3:8b' with status 404: "
            "model 'qwen3:8b' not found, try pulling it first"
        )

    monkeypatch.setattr(client.app.state.run_service, "create_run", explode_create_run)

    response = client.post(
        "/runs",
        json={
            "document_ids": [document_id],
            "workflow_plugin_id": "ollama_text_workflow",
        },
    )

    assert response.status_code == 502
    assert "try pulling it first" in response.json()["detail"]


def test_improvement_endpoints_apply_actions_and_list_history() -> None:
    client = TestClient(create_app())
    upload_response = client.post(
        "/documents",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.\n\nDNA stores genetic information.",
        },
    )
    document_id = upload_response.json()["document_id"]
    run_response = client.post(
        "/runs",
        json={
            "document_ids": [document_id],
            "workflow_plugin_id": "basic_text_workflow",
            "workflow_config": {"max_cards": 5},
        },
    )
    run_id = run_response.json()["run_id"]
    cards_response = client.get(f"/runs/{run_id}/cards")
    first_card_id = cards_response.json()[0]["card_id"]

    improvement_response = client.post(
        f"/runs/{run_id}/improvements",
        json={
            "actions": [
                {
                    "action_type": "edit_card",
                    "card_id": first_card_id,
                    "front": "What are cells?",
                },
                {
                    "action_type": "prompt_refine_selected",
                    "card_ids": [first_card_id],
                    "prompt": "Keep it a question",
                },
            ]
        },
    )

    assert improvement_response.status_code == 200
    updated_run = improvement_response.json()
    assert updated_run["run_id"] == run_id
    assert updated_run["card_count"] == 2

    updated_cards_response = client.get(f"/runs/{run_id}/cards")
    updated_cards = updated_cards_response.json()
    assert updated_cards[0]["front"].endswith("?")
    assert updated_cards[0]["status"] == "edited"

    history_response = client.get(f"/runs/{run_id}/improvements")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 2
    assert history[0]["action_type"] == "edit_card"
    assert history[1]["action_type"] == "prompt_refine_selected"


def test_runs_endpoint_rejects_unknown_documents() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/runs",
        json={
            "document_ids": ["missing-doc"],
            "workflow_plugin_id": "basic_text_workflow",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown document: missing-doc"


def test_document_and_run_detail_endpoints_return_404_for_missing_resources() -> None:
    client = TestClient(create_app())

    document_response = client.get("/documents/missing-doc")
    assert document_response.status_code == 404
    assert document_response.json()["detail"] == "Unknown document: missing-doc"

    run_response = client.get("/runs/missing-run")
    assert run_response.status_code == 404
    assert run_response.json()["detail"] == "Unknown run: missing-run"

    cards_response = client.get("/runs/missing-run/cards")
    assert cards_response.status_code == 404
    assert cards_response.json()["detail"] == "Unknown run: missing-run"

    improvements_response = client.get("/runs/missing-run/improvements")
    assert improvements_response.status_code == 404
    assert improvements_response.json()["detail"] == "Unknown run: missing-run"


def test_export_endpoints_create_describe_and_download_exports() -> None:
    client = TestClient(create_app())
    upload_response = client.post(
        "/documents",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.\n\nDNA stores genetic information.",
        },
    )
    document_id = upload_response.json()["document_id"]
    run_response = client.post(
        "/runs",
        json={
            "document_ids": [document_id],
            "workflow_plugin_id": "basic_text_workflow",
            "workflow_config": {"max_cards": 5},
        },
    )
    run_id = run_response.json()["run_id"]

    export_response = client.post(
        f"/runs/{run_id}/exports",
        json={"exporter_id": "csv"},
    )

    assert export_response.status_code == 201
    export_payload = export_response.json()
    export_id = export_payload["export_id"]
    assert export_payload["run_id"] == run_id
    assert export_payload["exporter_id"] == "csv"
    assert export_payload["filename"] == "biology.csv"
    assert export_payload["media_type"] == "text/csv"
    assert export_payload["card_count"] == 2

    detail_response = client.get(f"/exports/{export_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["export_id"] == export_id

    download_response = client.get(f"/exports/{export_id}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("text/csv")
    assert 'filename="biology.csv"' in download_response.headers["content-disposition"]
    assert "front,back,tags" in download_response.text


def test_export_endpoints_validate_unknown_resources_and_exporters() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/runs/missing-run/exports",
        json={"exporter_id": "csv"},
    )
    assert create_response.status_code == 400
    assert create_response.json()["detail"] == "Unknown run: missing-run"

    missing_export_response = client.get("/exports/missing-export")
    assert missing_export_response.status_code == 404
    assert missing_export_response.json()["detail"] == "Unknown export: missing-export"

    missing_download_response = client.get("/exports/missing-export/download")
    assert missing_download_response.status_code == 404
    assert missing_download_response.json()["detail"] == "Unknown export: missing-export"


def test_improvement_endpoints_validate_bad_requests() -> None:
    client = TestClient(create_app())
    upload_response = client.post(
        "/documents",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.",
        },
    )
    document_id = upload_response.json()["document_id"]
    run_response = client.post(
        "/runs",
        json={
            "document_ids": [document_id],
            "workflow_plugin_id": "basic_text_workflow",
        },
    )
    run_id = run_response.json()["run_id"]

    response = client.post(
        f"/runs/{run_id}/improvements",
        json={
            "actions": [
                {
                    "action_type": "edit_card",
                    "card_id": "missing-card",
                    "front": "Updated front",
                }
            ]
        },
    )

    assert response.status_code == 400
    assert "Unknown card 'missing-card'" in response.json()["detail"]


def test_legacy_generate_document_endpoint_is_no_longer_available() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/generate/document",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.",
            "workflow_plugin_id": "basic_text_workflow",
            "output_type": "csv",
        },
    )

    assert response.status_code == 404
