from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


def test_generate_document_returns_csv_export() -> None:
    response = client.post(
        "/generate/document",
        json={
            "filename": "biology.txt",
            "content": (
                "Cells are the basic unit of life.\n\n"
                "DNA stores genetic information."
            ),
            "workflow_plugin_id": "basic_text_workflow",
            "output_type": "csv",
            "workflow_config": {"max_cards": 2},
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="biology.csv"' in response.headers["content-disposition"]
    assert "front,back,tags" in response.text
    assert "DNA stores genetic information." in response.text


def test_generate_document_rejects_unknown_plugin() -> None:
    response = client.post(
        "/generate/document",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.",
            "workflow_plugin_id": "missing_workflow",
            "output_type": "csv",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported workflow plugin: missing_workflow"


def test_generate_document_rejects_unknown_output_type() -> None:
    response = client.post(
        "/generate/document",
        json={
            "filename": "biology.txt",
            "content": "Cells are the basic unit of life.",
            "workflow_plugin_id": "basic_text_workflow",
            "output_type": "json",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported output type: json"
