from abc import ABC, abstractmethod

from domain.models import CardCandidate, ParsedContent, PluginManifest, WorkflowPluginConfig


class WorkflowPlugin(ABC):
    """User-selectable workflow plugin interface."""

    manifest: PluginManifest

    @abstractmethod
    def generate_cards(
        self,
        parsed_content: ParsedContent,
        config: WorkflowPluginConfig,
    ) -> list[CardCandidate]:
        raise NotImplementedError

