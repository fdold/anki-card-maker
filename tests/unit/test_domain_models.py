from domain.models import GenerationRun, RunCard, SourceReference, StoredDocument


def test_stored_document_can_embed_parsed_content_metadata() -> None:
    stored_document = StoredDocument(
        document_id="doc-1",
        filename="biology.txt",
        title="biology",
        source_type="txt",
        content="Cells are the basic unit of life.",
    )

    assert stored_document.document_id == "doc-1"
    assert stored_document.filename == "biology.txt"
    assert stored_document.created_at is not None


def test_run_card_tracks_original_and_current_card_content() -> None:
    run_card = RunCard(
        card_id="card-1",
        run_id="run-1",
        front="What is a cell?",
        back="The basic unit of life.",
        original_front="What is a cell?",
        original_back="The basic unit of life.",
        source=SourceReference(section="Biology", position=0),
        tags=["generated"],
        workflow_plugin_id="basic_text_workflow",
    )

    assert run_card.status == "active"
    assert run_card.original_front == run_card.front
    assert run_card.original_back == run_card.back
    assert run_card.updated_at is not None


def test_generation_run_supports_multiple_documents_and_status_tracking() -> None:
    generation_run = GenerationRun(
        run_id="run-1",
        plugin_id="basic_text_workflow",
        document_id="doc-1",
        document_ids=["doc-1", "doc-2"],
        status="pending",
        workflow_config={"max_cards": 5},
    )

    assert generation_run.document_id == "doc-1"
    assert generation_run.document_ids == ["doc-1", "doc-2"]
    assert generation_run.status == "pending"
    assert generation_run.workflow_config["max_cards"] == 5
