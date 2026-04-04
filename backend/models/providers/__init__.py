"""Provider adapters for centrally managed model access."""

from backend.models.providers.base import ModelProvider
from backend.models.providers.ollama import OllamaProvider

__all__ = ["ModelProvider", "OllamaProvider"]
