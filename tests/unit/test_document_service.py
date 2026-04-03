from backend.services.document_service import DocumentService
from backend.storage.document_repository import InMemoryDocumentRepository


def test_document_service_uploads_and_parses_txt_document() -> None:
    repository = InMemoryDocumentRepository()
    service = DocumentService(document_repository=repository)

    stored_document = service.upload_document(
        filename="biology.txt",
        content="Cells are the basic unit of life.\n\nDNA stores genetic information.",
        document_id="doc-1",
    )

    assert stored_document.document_id == "doc-1"
    assert stored_document.source_type == "txt"
    assert stored_document.parsed_content is not None
    assert len(stored_document.parsed_content.blocks) == 2
    assert repository.get("doc-1") == stored_document


def test_document_service_rejects_unknown_source_type() -> None:
    service = DocumentService(document_repository=InMemoryDocumentRepository())

    try:
        service.upload_document(
            filename="biology.md",
            content="Cells are the basic unit of life.",
            source_type="md",
        )
    except ValueError as exc:
        assert str(exc) == "Unsupported source type: md"
    else:
        raise AssertionError("Expected ValueError for unsupported source type.")
