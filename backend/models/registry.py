from collections.abc import Callable, Mapping

from backend.models.gateway import ModelGateway
from backend.models.providers.base import ModelProvider
from backend.models.settings import ModelSettings, load_model_settings

ProviderFactory = Callable[[], ModelProvider]


def list_model_profiles(settings: ModelSettings | None = None):
    resolved_settings = settings or load_model_settings()
    return list(resolved_settings.profiles)


def get_model_profile(profile_id: str, settings: ModelSettings | None = None):
    resolved_settings = settings or load_model_settings()
    return resolved_settings.get_profile(profile_id)


def build_provider_registry(
    provider_factories: Mapping[str, ProviderFactory] | None = None,
) -> dict[str, ModelProvider]:
    resolved_factories = dict(provider_factories or {})
    return {
        provider_name: factory()
        for provider_name, factory in resolved_factories.items()
    }


def build_model_gateway(
    *,
    settings: ModelSettings | None = None,
    providers: Mapping[str, ModelProvider] | None = None,
    provider_factories: Mapping[str, ProviderFactory] | None = None,
) -> ModelGateway:
    resolved_settings = settings or load_model_settings()
    resolved_providers = (
        dict(providers)
        if providers is not None
        else build_provider_registry(provider_factories)
    )
    return ModelGateway(settings=resolved_settings, providers=resolved_providers)
