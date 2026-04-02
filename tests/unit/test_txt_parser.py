from backend.pipeline.parsers.txt_parser import parse_txt_document


def test_parse_txt_document_creates_single_block() -> None:
    parsed = parse_txt_document("doc-1", "Sample", "Hello world")

    assert parsed.document.document_id == "doc-1"
    assert len(parsed.blocks) == 1
    assert parsed.blocks[0].text == "Hello world"
    assert parsed.blocks[0].source.section == "Sample"

