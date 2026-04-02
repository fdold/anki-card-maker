from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from domain.models import CardCandidate, ParsedContent, PluginManifest

WorkflowPluginConfigT = TypeVar("WorkflowPluginConfigT", bound=BaseModel)


class WorkflowPlugin(ABC, Generic[WorkflowPluginConfigT]):
    """User-selectable workflow plugin interface."""

    base_manifest: PluginManifest
    config_model: type[WorkflowPluginConfigT]

    @property
    def manifest(self) -> PluginManifest:
        return self.base_manifest.model_copy(
            update={"config_schema": self.config_model.model_json_schema()}
        )

    @abstractmethod
    def generate_cards(
        self,
        parsed_content: ParsedContent,
        config: WorkflowPluginConfigT,
    ) -> list[CardCandidate]:
        raise NotImplementedError
