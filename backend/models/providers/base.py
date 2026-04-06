from abc import ABC, abstractmethod

from backend.models.base import ModelProfile, ModelRequest, ModelResponse


class ModelProvider(ABC):
    @abstractmethod
    def generate(
        self,
        profile: ModelProfile,
        request: ModelRequest,
    ) -> ModelResponse:
        raise NotImplementedError

    def healthcheck(self, profile: ModelProfile) -> bool:
        return True

    def describe_runtime(self, profile: ModelProfile) -> dict[str, object]:
        return {
            "profile_id": profile.profile_id,
            "provider": profile.provider,
            "model_name": profile.model_name,
            "status": "unknown",
        }
