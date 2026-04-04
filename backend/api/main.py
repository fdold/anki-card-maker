import logging

from fastapi import FastAPI, HTTPException, Request, Response, status

from backend.api.schemas import (
    ApplyImprovementsRequest,
    CreateRunRequest,
    CreateExportRequest,
    DocumentDetailResponse,
    DocumentSummaryResponse,
    ExportResponse,
    ImprovementRecordResponse,
    ImprovementActionRequest,
    RunCardResponse,
    RunDetailResponse,
    RunSummaryResponse,
    UploadDocumentRequest,
)
from backend.models import build_model_gateway
from backend.services.document_service import DocumentService
from backend.services.export_service import ExportService
from backend.services.improvement_service import ImprovementService
from backend.services.registry import create_application_overview
from backend.services.run_service import RunService
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.export_repository import InMemoryExportRepository
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import (
    ExportArtifact,
    GenerationRun,
    ImprovementAction,
    ImprovementBatch,
    ImprovementRecord,
    RunCard,
    StoredDocument,
)

logger = logging.getLogger(__name__)


def _build_document_summary(document: StoredDocument) -> DocumentSummaryResponse:
    parsed_content = document.parsed_content
    return DocumentSummaryResponse(
        document_id=document.document_id,
        filename=document.filename,
        title=document.title,
        source_type=document.source_type,
        created_at=document.created_at,
        block_count=len(parsed_content.blocks) if parsed_content is not None else 0,
        warnings=list(parsed_content.warnings) if parsed_content is not None else [],
    )


def _build_document_detail(document: StoredDocument) -> DocumentDetailResponse:
    summary = _build_document_summary(document)
    return DocumentDetailResponse(
        **summary.model_dump(),
        has_parsed_content=document.parsed_content is not None,
    )


def _build_run_summary(run: GenerationRun) -> RunSummaryResponse:
    return RunSummaryResponse(
        run_id=run.run_id,
        plugin_id=run.plugin_id,
        document_ids=list(run.document_ids),
        status=run.status,
        workflow_config=dict(run.workflow_config),
        warnings=list(run.warnings),
        card_count=len(run.cards),
        created_at=run.created_at,
        updated_at=run.updated_at,
        completed_at=run.completed_at,
    )


def _build_run_detail(run: GenerationRun) -> RunDetailResponse:
    summary = _build_run_summary(run)
    return RunDetailResponse(
        **summary.model_dump(),
        document_id=run.document_id,
    )


def _build_run_card(card: RunCard) -> RunCardResponse:
    return RunCardResponse(
        card_id=card.card_id,
        run_id=card.run_id,
        front=card.front,
        back=card.back,
        source=card.source,
        tags=list(card.tags),
        workflow_plugin_id=card.workflow_plugin_id,
        original_front=card.original_front,
        original_back=card.original_back,
        status=card.status,
        rating=card.rating,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


def _build_export_response(export_artifact: ExportArtifact) -> ExportResponse:
    return ExportResponse(
        export_id=export_artifact.export_id,
        run_id=export_artifact.run_id,
        exporter_id=export_artifact.exporter_id,
        card_ids=list(export_artifact.card_ids),
        filename=export_artifact.filename,
        media_type=export_artifact.media_type,
        status=export_artifact.status,
        created_at=export_artifact.created_at,
        completed_at=export_artifact.completed_at,
        card_count=len(export_artifact.card_ids),
    )


def _build_improvement_record_response(
    record: ImprovementRecord,
) -> ImprovementRecordResponse:
    return ImprovementRecordResponse(
        record_id=record.record_id,
        run_id=record.run_id,
        action_type=record.action_type,
        card_id=record.card_id,
        applied_at=record.applied_at,
        summary=record.summary,
    )


def _to_improvement_action(action: ImprovementActionRequest) -> ImprovementAction:
    return ImprovementAction(
        action_type=action.action_type,
        card_id=action.card_id,
        card_ids=list(action.card_ids),
        front=action.front,
        back=action.back,
        rating=action.rating,
        prompt=action.prompt,
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Anki Card Maker API",
        version="0.1.0",
        description="Backend API for modular document-to-Anki flashcard generation.",
    )
    document_repository = InMemoryDocumentRepository()
    run_repository = InMemoryRunRepository()
    export_repository = InMemoryExportRepository()
    model_gateway = build_model_gateway()
    app.state.document_service = DocumentService(document_repository=document_repository)
    app.state.run_service = RunService(
        document_repository=document_repository,
        run_repository=run_repository,
        model_gateway=model_gateway,
    )
    app.state.improvement_service = ImprovementService(
        run_repository=run_repository,
        model_gateway=model_gateway,
    )
    app.state.export_service = ExportService(
        run_repository=run_repository,
        export_repository=export_repository,
        document_repository=document_repository,
    )

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/overview")
    def overview() -> dict[str, object]:
        return create_application_overview()

    @app.post(
        "/documents",
        response_model=DocumentDetailResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def upload_document(
        request: UploadDocumentRequest,
        http_request: Request,
    ) -> DocumentDetailResponse:
        logger.info("Received document upload for filename '%s'", request.filename)
        try:
            stored_document = http_request.app.state.document_service.upload_document(
                filename=request.filename,
                content=request.content,
                source_type=request.source_type,
                title=request.title,
                document_id=request.document_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _build_document_detail(stored_document)

    @app.get("/documents", response_model=list[DocumentSummaryResponse])
    def list_documents(http_request: Request) -> list[DocumentSummaryResponse]:
        documents = http_request.app.state.document_service.list_documents()
        return [_build_document_summary(document) for document in documents]

    @app.get("/documents/{document_id}", response_model=DocumentDetailResponse)
    def get_document(document_id: str, http_request: Request) -> DocumentDetailResponse:
        stored_document = http_request.app.state.document_service.get_document(document_id)
        if stored_document is None:
            raise HTTPException(status_code=404, detail=f"Unknown document: {document_id}")
        return _build_document_detail(stored_document)

    @app.post(
        "/runs",
        response_model=RunDetailResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_run(request: CreateRunRequest, http_request: Request) -> RunDetailResponse:
        logger.info(
            "Received run creation request for workflow '%s' and %s documents",
            request.workflow_plugin_id,
            len(request.document_ids),
        )
        try:
            run = http_request.app.state.run_service.create_run(
                document_ids=request.document_ids,
                workflow_plugin_id=request.workflow_plugin_id,
                workflow_config=request.workflow_config,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _build_run_detail(run)

    @app.get("/runs", response_model=list[RunSummaryResponse])
    def list_runs(http_request: Request) -> list[RunSummaryResponse]:
        runs = http_request.app.state.run_service.list_runs()
        return [_build_run_summary(run) for run in runs]

    @app.get("/runs/{run_id}", response_model=RunDetailResponse)
    def get_run(run_id: str, http_request: Request) -> RunDetailResponse:
        run = http_request.app.state.run_service.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Unknown run: {run_id}")
        return _build_run_detail(run)

    @app.get("/runs/{run_id}/cards", response_model=list[RunCardResponse])
    def get_run_cards(run_id: str, http_request: Request) -> list[RunCardResponse]:
        run = http_request.app.state.run_service.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Unknown run: {run_id}")
        return [_build_run_card(card) for card in run.cards]

    @app.post(
        "/runs/{run_id}/improvements",
        response_model=RunDetailResponse,
    )
    def apply_improvements(
        run_id: str,
        request: ApplyImprovementsRequest,
        http_request: Request,
    ) -> RunDetailResponse:
        try:
            updated_run = http_request.app.state.improvement_service.apply_improvements(
                ImprovementBatch(
                    run_id=run_id,
                    actions=[_to_improvement_action(action) for action in request.actions],
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _build_run_detail(updated_run)

    @app.get(
        "/runs/{run_id}/improvements",
        response_model=list[ImprovementRecordResponse],
    )
    def list_improvements(
        run_id: str,
        http_request: Request,
    ) -> list[ImprovementRecordResponse]:
        run = http_request.app.state.run_service.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Unknown run: {run_id}")
        return [
            _build_improvement_record_response(record)
            for record in run.improvement_history
        ]

    @app.post(
        "/runs/{run_id}/exports",
        response_model=ExportResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_export(
        run_id: str,
        request: CreateExportRequest,
        http_request: Request,
    ) -> ExportResponse:
        try:
            export_artifact = http_request.app.state.export_service.create_export(
                run_id=run_id,
                exporter_id=request.exporter_id,
                card_ids=request.card_ids,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _build_export_response(export_artifact)

    @app.get("/exports/{export_id}", response_model=ExportResponse)
    def get_export(export_id: str, http_request: Request) -> ExportResponse:
        export_artifact = http_request.app.state.export_service.get_export(export_id)
        if export_artifact is None:
            raise HTTPException(status_code=404, detail=f"Unknown export: {export_id}")
        return _build_export_response(export_artifact)

    @app.get("/exports/{export_id}/download")
    def download_export(export_id: str, http_request: Request) -> Response:
        export_artifact = http_request.app.state.export_service.get_export(export_id)
        if export_artifact is None:
            raise HTTPException(status_code=404, detail=f"Unknown export: {export_id}")
        return Response(
            content=export_artifact.content,
            media_type=export_artifact.media_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{export_artifact.filename}"'
                )
            },
        )

    return app


app = create_app()
