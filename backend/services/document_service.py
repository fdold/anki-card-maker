import logging
from pathlib import Path
from uuid import uuid4

from backend.services.registry import get_parser_for_source_type
from backend.storage.document_repository import InMemoryDocumentRepository
from domain.models import StoredDocument

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        document_repository: InMemoryDocumentRepository | None = None,
    ) -> None:
        self._document_repository = document_repository or InMemoryDocumentRepository()

    def upload_document(
        self,
        *,
        filename: str,
        content: str,
        source_type: str | None = None,
        title: str | None = None,
        document_id: str | None = None,
    ) -> StoredDocument:
        resolved_source_type = source_type or filename.rsplit(".", 1)[-1].lower()
        parser = get_parser_for_source_type(resolved_source_type)
        resolved_document_id = document_id or str(uuid4())
        resolved_title = title or Path(filename).stem

        logger.info(
            "Uploading document '%s' with source_type '%s'",
            filename,
            resolved_source_type,
        )
        parsed_content = parser(
            document_id=resolved_document_id,
            title=resolved_title,
            text=content,
        )
        stored_document = StoredDocument(
            document_id=resolved_document_id,
            filename=filename,
            title=resolved_title,
            source_type=resolved_source_type,
            content=content,
            parsed_content=parsed_content,
        )
        self._document_repository.save(stored_document)
        logger.info("Stored document '%s' as %s", filename, resolved_document_id)
        return stored_document

    def get_document(self, document_id: str) -> StoredDocument | None:
        return self._document_repository.get(document_id)

    def list_documents(self) -> list[StoredDocument]:
        return self._document_repository.list()
