from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from pydantic import BaseModel

from backend.models import ModelGateway
from domain.models import (
    CardCandidate,
    ParsedContent,
    PluginManifest,
    RunCard,
    WorkflowImprovementRequest,
)

WorkflowPluginConfigT = TypeVar("WorkflowPluginConfigT", bound=BaseModel)


@dataclass(slots=True)
class WorkflowExecutionContext:
    run_id: str
    models: ModelGateway | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def require_models(self) -> ModelGateway:
        if self.models is None:
            raise ValueError("This workflow execution context does not provide model access.")
        return self.models


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
        context: WorkflowExecutionContext | None = None,
    ) -> list[CardCandidate]:
        raise NotImplementedError

    def apply_improvement(
        self,
        request: WorkflowImprovementRequest,
        config: WorkflowPluginConfigT,
        context: WorkflowExecutionContext | None = None,
    ) -> list[RunCard]:
        raise NotImplementedError(
            f"Workflow plugin '{self.manifest.plugin_id}' does not support "
            f"improvement operation '{request.action_type}'."
        )
