from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


CardStatus = Literal["active", "edited", "deleted", "accepted", "rejected"]
CardRating = Literal["good", "mixed", "bad"]
RunStatus = Literal["pending", "running", "completed", "failed"]
ImprovementActionType = Literal[
    "edit_card",
    "delete_card",
    "rate_card",
    "rate_run",
    "prompt_refine_selected",
    "prompt_refine_all",
]


class SourceReference(BaseModel):
    page: int | None = None
    section: str | None = None
    chapter: str | None = None
    position: int | None = None


class Document(BaseModel):
    document_id: str
    title: str
    source_type: str


class TextBlock(BaseModel):
    text: str
    order: int
    source: SourceReference


class ParsedContent(BaseModel):
    document: Document
    blocks: list[TextBlock] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StoredDocument(BaseModel):
    document_id: str
    filename: str
    title: str
    source_type: str
    content: str
    parsed_content: ParsedContent | None = None
    created_at: datetime = Field(default_factory=utc_now)


class PluginManifest(BaseModel):
    plugin_id: str
    name: str
    plugin_type: str
    description: str
    supported_input_types: list[str] = Field(default_factory=list)
    supported_operations: list[str] = Field(default_factory=list)
    config_schema: dict[str, object] = Field(default_factory=dict)


class CardCandidate(BaseModel):
    front: str
    back: str
    source: SourceReference
    tags: list[str] = Field(default_factory=list)
    workflow_plugin_id: str


class RunCard(BaseModel):
    card_id: str
    run_id: str
    front: str
    back: str
    source: SourceReference
    tags: list[str] = Field(default_factory=list)
    workflow_plugin_id: str
    original_front: str
    original_back: str
    status: CardStatus = "active"
    rating: CardRating | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ImprovementAction(BaseModel):
    action_type: ImprovementActionType
    card_id: str | None = None
    card_ids: list[str] = Field(default_factory=list)
    front: str | None = None
    back: str | None = None
    rating: CardRating | None = None
    prompt: str | None = None


class ImprovementBatch(BaseModel):
    run_id: str
    actions: list[ImprovementAction] = Field(default_factory=list)


class ImprovementRecord(BaseModel):
    record_id: str
    run_id: str
    action_type: ImprovementActionType
    card_id: str | None = None
    applied_at: datetime = Field(default_factory=utc_now)
    summary: str


class WorkflowImprovementRequest(BaseModel):
    action_type: Literal["prompt_refine_selected", "prompt_refine_all"]
    run_id: str
    prompt: str
    cards: list[RunCard] = Field(default_factory=list)


class ExportableAnkiCard(BaseModel):
    front: str
    back: str
    tags: list[str] = Field(default_factory=list)


class GenerationRun(BaseModel):
    run_id: str
    plugin_id: str
    document_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    status: RunStatus = "completed"
    rating: CardRating | None = None
    workflow_config: dict[str, object] = Field(default_factory=dict)
    cards: list[RunCard] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    improvement_history: list[ImprovementRecord] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
