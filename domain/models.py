from pydantic import BaseModel, Field


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


class WorkflowPluginConfig(BaseModel):
    max_cards: int = Field(default=20, ge=1, le=500)
    card_style: str = Field(default="basic")


class PluginManifest(BaseModel):
    plugin_id: str
    name: str
    plugin_type: str
    description: str
    supported_input_types: list[str] = Field(default_factory=list)
    config_schema: dict[str, object] = Field(default_factory=dict)


class CardCandidate(BaseModel):
    front: str
    back: str
    source: SourceReference
    tags: list[str] = Field(default_factory=list)
    workflow_plugin_id: str


class ExportableAnkiCard(BaseModel):
    front: str
    back: str
    tags: list[str] = Field(default_factory=list)


class GenerationRun(BaseModel):
    run_id: str
    plugin_id: str
    document_id: str
    cards: list[CardCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

