from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import GenerationRun, StoredDocument


def test_document_repository_saves_lists_and_updates_documents() -> None:
    repository = InMemoryDocumentRepository()
    stored_document = StoredDocument(
        document_id="doc-1",
        filename="biology.txt",
        title="biology",
        source_type="txt",
        content="Cells are the basic unit of life.",
    )

    repository.save(stored_document)

    assert repository.get("doc-1") == stored_document
    assert repository.list() == [stored_document]

    updated_document = stored_document.model_copy(update={"title": "Biology Notes"})
    repository.update(updated_document)

    assert repository.get("doc-1") is not None
    assert repository.get("doc-1").title == "Biology Notes"


def test_run_repository_saves_lists_and_updates_runs() -> None:
    repository = InMemoryRunRepository()
    generation_run = GenerationRun(
        run_id="run-1",
        plugin_id="basic_text_workflow",
        document_id="doc-1",
        document_ids=["doc-1"],
        status="pending",
    )

    repository.save(generation_run)

    assert repository.get("run-1") == generation_run
    assert repository.list() == [generation_run]

    updated_run = generation_run.model_copy(update={"status": "completed"})
    repository.update(updated_run)

    assert repository.get("run-1") is not None
    assert repository.get("run-1").status == "completed"
