from backend.services.document_generation_service import generate_cards_from_document_input


def test_generate_cards_from_document_input_returns_traceable_cards() -> None:
    result = generate_cards_from_document_input(
        filename="biology.txt",
        content="Cells are the basic unit of life.",
        workflow_plugin_id="basic_text_workflow",
        source_type="txt",
        workflow_config={"max_cards": 5},
    )

    assert result.parsed_content.document.title == "biology"
    assert len(result.generation_run.cards) == 1
    assert result.generation_run.cards[0].source.section == "biology"
    assert result.exportable_cards[0].back == "Cells are the basic unit of life."


def test_generate_cards_from_document_input_rejects_unknown_source_type() -> None:
    try:
        generate_cards_from_document_input(
            filename="biology.md",
            content="Cells are the basic unit of life.",
            workflow_plugin_id="basic_text_workflow",
            source_type="md",
        )
    except ValueError as exc:
        assert str(exc) == "Unsupported source type: md"
    else:
        raise AssertionError("Expected a ValueError for unknown source types.")

def test_generate_cards_from_document_input_uses_parser_segmentation() -> None:
    result = generate_cards_from_document_input(
        filename="segmented.txt",
        content="First fact\n\nSecond fact",
        workflow_plugin_id="basic_text_workflow",
        source_type="txt",
        document_id="doc-segments",
    )

    assert result.generation_run.document_id == "doc-segments"
    assert len(result.generation_run.cards) == 2
    assert result.generation_run.cards[0].source.position == 0
    assert result.generation_run.cards[1].source.position == 1
