from backend.models import (
    ModelProfile,
    ModelSettings,
    build_model_gateway,
    build_provider_registry,
    get_model_profile,
    list_model_profiles,
)
from backend.models.base import ModelResponse
from backend.models.providers.base import ModelProvider


class FakeProvider(ModelProvider):
    def generate(self, profile, request) -> ModelResponse:
        return ModelResponse(
            provider=profile.provider,
            model_name=profile.model_name,
            content="ok",
        )


def test_model_registry_lists_and_resolves_profiles() -> None:
    settings = ModelSettings(
        profiles=[
            ModelProfile(
                profile_id="ollama_generation_default",
                provider="ollama",
                model_name="qwen3:8b",
                base_url="http://ollama-default:11434",
            )
        ]
    )

    profiles = list_model_profiles(settings)

    assert len(profiles) == 1
    assert get_model_profile("ollama_generation_default", settings).model_name == "qwen3:8b"


def test_build_provider_registry_instantiates_factories() -> None:
    providers = build_provider_registry({"ollama": FakeProvider})

    assert isinstance(providers["ollama"], FakeProvider)


def test_build_model_gateway_uses_supplied_providers() -> None:
    settings = ModelSettings(
        profiles=[
            ModelProfile(
                profile_id="ollama_generation_default",
                provider="ollama",
                model_name="qwen3:8b",
                base_url="http://ollama-default:11434",
            )
        ]
    )

    gateway = build_model_gateway(
        settings=settings,
        providers={"ollama": FakeProvider()},
    )

    assert gateway.get_profile("ollama_generation_default").provider == "ollama"
