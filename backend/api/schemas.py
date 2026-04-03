from pydantic import BaseModel, Field


class GenerateDocumentRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    content: str
    workflow_plugin_id: str = Field(..., min_length=1)
    source_type: str | None = None
    title: str | None = None
    document_id: str | None = None
    workflow_config: dict[str, object] = Field(default_factory=dict)
