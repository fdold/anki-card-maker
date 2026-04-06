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
from backend.models.ollama_init import (
    OLLAMA_INIT_BASE_URL_ENV,
    OLLAMA_INIT_DELAY_SECONDS_ENV,
    OLLAMA_INIT_MAX_ATTEMPTS_ENV,
    ensure_models_present,
    list_installed_models,
    normalize_ollama_base_url,
    resolve_models_for_base_url,
    wait_for_ollama,
)
from backend.models.ollama_runtime import (
    DEFAULT_OLLAMA_PROBE_TIMEOUT_SECONDS,
    OllamaEndpointStatus,
    OllamaRuntimeStatus,
    describe_ollama_runtime,
    is_ollama_available,
    probe_ollama_endpoint,
    resolve_ollama_base_url,
)
from backend.models.providers import ModelProvider, OllamaProvider
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
    "DEFAULT_OLLAMA_PROBE_TIMEOUT_SECONDS",
    "OLLAMA_INIT_BASE_URL_ENV",
    "OLLAMA_INIT_DELAY_SECONDS_ENV",
    "OLLAMA_INIT_MAX_ATTEMPTS_ENV",
    "ModelGenerationOptions",
    "ModelGateway",
    "ModelInvocation",
    "ModelInvocationRecord",
    "ModelMessage",
    "ModelProfile",
    "ModelProvider",
    "ModelProviderError",
    "ModelRequest",
    "ModelResponse",
    "ModelResponseValidationError",
    "ModelSettings",
    "OllamaEndpointStatus",
    "OllamaProvider",
    "OllamaRuntimeStatus",
    "ModelUsage",
    "StructuredModelResult",
    "build_model_gateway",
    "build_provider_registry",
    "describe_ollama_runtime",
    "ensure_models_present",
    "get_model_profile",
    "list_installed_models",
    "list_model_profiles",
    "load_model_settings",
    "normalize_ollama_base_url",
    "is_ollama_available",
    "probe_ollama_endpoint",
    "resolve_models_for_base_url",
    "resolve_ollama_base_url",
    "wait_for_ollama",
]
