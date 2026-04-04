from datetime import datetime

from pydantic import BaseModel, Field

from domain.models import SourceReference


class UploadDocumentRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    content: str
    source_type: str | None = None
    title: str | None = None
    document_id: str | None = None


class DocumentSummaryResponse(BaseModel):
    document_id: str
    filename: str
    title: str
    source_type: str
    created_at: datetime
    block_count: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)


class DocumentDetailResponse(DocumentSummaryResponse):
    has_parsed_content: bool = False


class CreateRunRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1)
    workflow_plugin_id: str = Field(..., min_length=1)
    workflow_config: dict[str, object] = Field(default_factory=dict)


class RunSummaryResponse(BaseModel):
    run_id: str
    plugin_id: str
    document_ids: list[str] = Field(default_factory=list)
    status: str
    workflow_config: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    card_count: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class RunModelInvocationResponse(BaseModel):
    invocation_id: str
    profile_id: str
    provider: str
    model_name: str
    purpose: str
    status: str
    latency_ms: int | None = None
    error_message: str | None = None


class RunDetailResponse(RunSummaryResponse):
    document_id: str | None = None
    model_invocations: list[RunModelInvocationResponse] = Field(default_factory=list)


class RunCardResponse(BaseModel):
    card_id: str
    run_id: str
    front: str
    back: str
    source: SourceReference
    tags: list[str] = Field(default_factory=list)
    workflow_plugin_id: str
    original_front: str
    original_back: str
    status: str
    rating: str | None = None
    created_at: datetime
    updated_at: datetime


class ImprovementActionRequest(BaseModel):
    action_type: str
    card_id: str | None = None
    card_ids: list[str] = Field(default_factory=list)
    front: str | None = None
    back: str | None = None
    rating: str | None = None
    prompt: str | None = None


class ApplyImprovementsRequest(BaseModel):
    actions: list[ImprovementActionRequest] = Field(default_factory=list)


class ImprovementRecordResponse(BaseModel):
    record_id: str
    run_id: str
    action_type: str
    card_id: str | None = None
    applied_at: datetime
    summary: str


class CreateExportRequest(BaseModel):
    exporter_id: str = Field(..., min_length=1)
    card_ids: list[str] = Field(default_factory=list)


class ExportResponse(BaseModel):
    export_id: str
    run_id: str
    exporter_id: str
    card_ids: list[str] = Field(default_factory=list)
    filename: str
    media_type: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    card_count: int = Field(default=0, ge=0)
