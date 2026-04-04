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
