from backend.services.document_service import DocumentService
from backend.services.run_service import RunService
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.run_repository import InMemoryRunRepository


def test_run_service_creates_run_from_stored_documents() -> None:
    document_repository = InMemoryDocumentRepository()
    run_repository = InMemoryRunRepository()
    document_service = DocumentService(document_repository=document_repository)
    run_service = RunService(
        document_repository=document_repository,
        run_repository=run_repository,
    )

    stored_document = document_service.upload_document(
        filename="biology.txt",
        content="Cells are the basic unit of life.\n\nDNA stores genetic information.",
        document_id="doc-1",
    )

    generation_run = run_service.create_run(
        document_ids=[stored_document.document_id],
        workflow_plugin_id="basic_text_workflow",
        workflow_config={"max_cards": 5},
    )

    assert generation_run.document_ids == ["doc-1"]
    assert generation_run.status == "completed"
    assert len(generation_run.cards) == 2
    assert generation_run.cards[0].run_id == generation_run.run_id
    assert generation_run.cards[0].original_back == generation_run.cards[0].back
    assert run_repository.get(generation_run.run_id) == generation_run


def test_run_service_rejects_unknown_documents() -> None:
    run_service = RunService(
        document_repository=InMemoryDocumentRepository(),
        run_repository=InMemoryRunRepository(),
    )

    try:
        run_service.create_run(
            document_ids=["missing-doc"],
            workflow_plugin_id="basic_text_workflow",
        )
    except ValueError as exc:
        assert str(exc) == "Unknown document: missing-doc"
    else:
        raise AssertionError("Expected ValueError for unknown documents.")


def test_run_service_rejects_unknown_plugins() -> None:
    document_repository = InMemoryDocumentRepository()
    document_service = DocumentService(document_repository=document_repository)
    run_service = RunService(
        document_repository=document_repository,
        run_repository=InMemoryRunRepository(),
    )
    stored_document = document_service.upload_document(
        filename="biology.txt",
        content="Cells are the basic unit of life.",
        document_id="doc-1",
    )

    try:
        run_service.create_run(
            document_ids=[stored_document.document_id],
            workflow_plugin_id="missing_workflow",
        )
    except ValueError as exc:
        assert str(exc) == "Unsupported workflow plugin: missing_workflow"
    else:
        raise AssertionError("Expected ValueError for unsupported workflow plugin.")
