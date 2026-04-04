from typing import Any, Literal

from pydantic import BaseModel, Field

ModelRole = Literal["system", "user", "assistant", "tool"]
ModelInvocationStatus = Literal["completed", "failed"]


class ModelMessage(BaseModel):
    role: ModelRole
    content: str = Field(..., min_length=1)
    name: str | None = None


class ModelGenerationOptions(BaseModel):
    temperature: float | None = Field(default=None, ge=0.0)
    top_p: float | None = Field(default=None, gt=0.0, le=1.0)
    seed: int | None = None
    max_output_tokens: int | None = Field(default=None, ge=1)
    stop: list[str] = Field(default_factory=list)

    def merged_with(
        self,
        override: "ModelGenerationOptions | None",
    ) -> "ModelGenerationOptions":
        if override is None:
            return self.model_copy(deep=True)

        update_data: dict[str, object] = {}
        for field_name in ("temperature", "top_p", "seed", "max_output_tokens"):
            value = getattr(override, field_name)
            if value is not None:
                update_data[field_name] = value

        if "stop" in override.model_fields_set:
            update_data["stop"] = list(override.stop)
        return self.model_copy(update=update_data, deep=True)


class ModelProfile(BaseModel):
    profile_id: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1, description="Central provider identifier.")
    model_name: str = Field(..., min_length=1)
    base_url: str = Field(..., min_length=1)
    timeout_seconds: float = Field(default=60.0, gt=0.0)
    default_options: ModelGenerationOptions = Field(
        default_factory=ModelGenerationOptions
    )
    supports_structured_output: bool = False


class ModelRequest(BaseModel):
    profile_id: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=1, description="Why the model is being used.")
    messages: list[ModelMessage] = Field(default_factory=list)
    options: ModelGenerationOptions = Field(default_factory=ModelGenerationOptions)
    metadata: dict[str, object] = Field(default_factory=dict)


class ModelUsage(BaseModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class ModelResponse(BaseModel):
    provider: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    content: str = Field(..., description="Normalized text content returned by the provider.")
    raw_payload: Any = None
    usage: ModelUsage | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    finish_reason: str | None = None


class ModelInvocationRecord(BaseModel):
    profile_id: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=1)
    status: ModelInvocationStatus
    latency_ms: int | None = Field(default=None, ge=0)
    error_message: str | None = None


class ModelInvocation(ModelInvocationRecord):
    """Backward-compatible minimal invocation record alias."""


class ModelProviderError(RuntimeError):
    """Raised when a model provider request fails."""


class ModelResponseValidationError(ValueError):
    """Raised when a provider response cannot be validated into the expected schema."""
