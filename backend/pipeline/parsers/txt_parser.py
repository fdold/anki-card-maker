from domain.models import Document, ParsedContent, SourceReference, TextBlock


def parse_txt_document(document_id: str, title: str, text: str) -> ParsedContent:
    """Create a minimal normalized representation for plain-text inputs."""
    blocks: list[TextBlock] = []
    warnings: list[str] = []

    for index, raw_segment in enumerate(text.split("\n\n")):
        cleaned_segment = raw_segment.strip()
        if not cleaned_segment:
            continue
        blocks.append(
            TextBlock(
                text=cleaned_segment,
                order=index,
                source=SourceReference(section=title or "Document", position=index),
            )
        )

    if not blocks:
        warnings.append("Input text was empty after trimming.")

    return ParsedContent(
        document=Document(document_id=document_id, title=title, source_type="txt"),
        blocks=blocks,
        warnings=warnings,
    )
