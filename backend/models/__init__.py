"""Central model and method integration layer."""

from backend.models.base import (
    ModelGenerationOptions,
    ModelInvocation,
    ModelInvocationRecord,
    ModelMessage,
    ModelProfile,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    ModelResponseValidationError,
    ModelUsage,
)
from backend.models.gateway import ModelGateway, StructuredModelResult
from backend.models.registry import (
    build_model_gateway,
    build_provider_registry,
    get_model_profile,
    list_model_profiles,
)
from backend.models.settings import (
    MODEL_PROFILES_FILE_ENV,
    ModelSettings,
    load_model_settings,
)

__all__ = [
    "MODEL_PROFILES_FILE_ENV",
    "ModelGenerationOptions",
    "ModelGateway",
    "ModelInvocation",
    "ModelInvocationRecord",
    "ModelMessage",
    "ModelProfile",
    "ModelProviderError",
    "ModelRequest",
    "ModelResponse",
    "ModelResponseValidationError",
    "ModelSettings",
    "ModelUsage",
    "StructuredModelResult",
    "build_model_gateway",
    "build_provider_registry",
    "get_model_profile",
    "list_model_profiles",
    "load_model_settings",
]
