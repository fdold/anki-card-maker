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


class RunDetailResponse(RunSummaryResponse):
    document_id: str | None = None


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
