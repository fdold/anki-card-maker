from domain.models import StoredDocument


class InMemoryDocumentRepository:
    """Temporary repository until persistent document storage is introduced."""

    def __init__(self) -> None:
        self._documents: dict[str, StoredDocument] = {}

    def save(self, document: StoredDocument) -> None:
        self._documents[document.document_id] = document

    def get(self, document_id: str) -> StoredDocument | None:
        return self._documents.get(document_id)

    def list(self) -> list[StoredDocument]:
        return list(self._documents.values())

    def update(self, document: StoredDocument) -> None:
        if document.document_id not in self._documents:
            raise ValueError(f"Unknown document: {document.document_id}")
        self._documents[document.document_id] = document
