import pytest
from pydantic import ValidationError

from backend.api.schemas import CreateRunRequest, DocumentDetailResponse


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
