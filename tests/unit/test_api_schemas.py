import pytest
from pydantic import ValidationError

from backend.api.schemas import CreateRunRequest, DocumentDetailResponse, RunDetailResponse


def test_create_run_request_requires_at_least_one_document() -> None:
    with pytest.raises(ValidationError):
        CreateRunRequest(document_ids=[], workflow_plugin_id="basic_text_workflow")


def test_document_detail_response_can_represent_parsed_documents() -> None:
    response = DocumentDetailResponse(
        document_id="doc-1",
        filename="biology.txt",
        title="biology",
        source_type="txt",
        block_count=2,
        warnings=[],
        has_parsed_content=True,
        created_at="2026-04-03T12:00:00Z",
    )

    assert response.document_id == "doc-1"
    assert response.block_count == 2
    assert response.has_parsed_content is True


def test_run_detail_response_can_include_model_invocations() -> None:
    response = RunDetailResponse(
        run_id="run-1",
        plugin_id="ollama_text_workflow",
        document_id="doc-1",
        document_ids=["doc-1"],
        status="completed",
        workflow_config={},
        warnings=[],
        card_count=1,
        created_at="2026-04-03T12:00:00Z",
        updated_at="2026-04-03T12:05:00Z",
        model_invocations=[
            {
                "invocation_id": "inv-1",
                "profile_id": "ollama_generation_default",
                "provider": "ollama",
                "model_name": "qwen3:8b",
                "purpose": "card_generation",
                "status": "completed",
                "latency_ms": 140,
            }
        ],
    )

    assert len(response.model_invocations) == 1
    assert response.model_invocations[0].profile_id == "ollama_generation_default"
