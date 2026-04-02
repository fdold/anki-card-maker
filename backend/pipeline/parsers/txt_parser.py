from domain.models import Document, ParsedContent, SourceReference, TextBlock


def parse_txt_document(document_id: str, title: str, text: str) -> ParsedContent:
    """Create a minimal normalized representation for plain-text inputs."""
    block = TextBlock(
        text=text.strip(),
        order=0,
        source=SourceReference(section=title or "Document", position=0),
    )
    return ParsedContent(
        document=Document(document_id=document_id, title=title, source_type="txt"),
        blocks=[block],
        warnings=[] if block.text else ["Input text was empty after trimming."],
    )

