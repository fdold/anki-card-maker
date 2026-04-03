import logging

from fastapi import FastAPI, HTTPException, Response

from backend.api.schemas import (
    GenerateDocumentRequest,
)
from backend.services.registry import create_application_overview
from backend.services.document_generation_service import generate_cards_from_document_input

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Anki Card Maker API",
    version="0.1.0",
    description="Backend API for modular document-to-Anki flashcard generation.",
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/overview")
def overview() -> dict[str, object]:
    return create_application_overview()


@app.post("/generate/document")
def generate_from_document(
    request: GenerateDocumentRequest,
) -> Response:
    source_type = request.source_type or request.filename.rsplit(".", 1)[-1].lower()
    logger.info(
        "Received document generation request for filename '%s' with workflow '%s'",
        request.filename,
        request.workflow_plugin_id,
    )
    try:
        result = generate_cards_from_document_input(
            content=request.content,
            workflow_plugin_id=request.workflow_plugin_id,
            source_type=source_type,
            filename=request.filename,
            title=request.title,
            document_id=request.document_id,
            workflow_config=request.workflow_config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    csv_filename = f"{result.parsed_content.document.title}.csv"
    return Response(
        content=result.to_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{csv_filename}"'},
    )
