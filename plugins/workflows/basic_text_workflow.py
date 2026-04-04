from pydantic import BaseModel, Field

from domain.models import (
    CardCandidate,
    ParsedContent,
    PluginManifest,
    RunCard,
    WorkflowImprovementRequest,
    utc_now,
)
from plugins.base import WorkflowExecutionContext, WorkflowPlugin


class BasicTextWorkflowConfig(BaseModel):
    max_cards: int = Field(default=20, ge=1, le=500)
    card_style: str = Field(default="basic")


class BasicTextWorkflowPlugin(WorkflowPlugin[BasicTextWorkflowConfig]):
    config_model = BasicTextWorkflowConfig
    base_manifest = PluginManifest(
        plugin_id="basic_text_workflow",
        name="Basic Text Workflow",
        plugin_type="workflow",
        description="Minimal starter workflow for TXT inputs and basic cards.",
        supported_input_types=["txt"],
        supported_operations=["prompt_refine_selected", "prompt_refine_all"],
    )

    def generate_cards(
        self,
        parsed_content: ParsedContent,
        config: BasicTextWorkflowConfig,
        context: WorkflowExecutionContext | None = None,
    ) -> list[CardCandidate]:
        cards: list[CardCandidate] = []
        for block in parsed_content.blocks[: config.max_cards]:
            if not block.text:
                continue
            cards.append(
                CardCandidate(
                    front=f"What is stated in section '{block.source.section or 'Document'}'?",
                    back=block.text,
                    source=block.source,
                    tags=["generated", "txt"],
                    workflow_plugin_id=self.manifest.plugin_id,
                )
            )
        return cards

    def apply_improvement(
        self,
        request: WorkflowImprovementRequest,
        config: BasicTextWorkflowConfig,
        context: WorkflowExecutionContext | None = None,
    ) -> list[RunCard]:
        normalized_prompt = request.prompt.strip()
        lower_prompt = normalized_prompt.lower()
        refined_cards: list[RunCard] = []

        for card in request.cards:
            refined_front = card.front
            refined_back = card.back

            if "question" in lower_prompt:
                refined_front = refined_front.rstrip("?.!") + "?"

            if "concise" in lower_prompt or "short" in lower_prompt:
                first_sentence = refined_back.split(".")[0].strip()
                if first_sentence:
                    refined_back = first_sentence
                    if card.back.strip().endswith("."):
                        refined_back += "."

            refined_tags = list(card.tags)
            if "improved" not in refined_tags:
                refined_tags.append("improved")

            refined_cards.append(
                card.model_copy(
                    update={
                        "front": refined_front,
                        "back": refined_back,
                        "tags": refined_tags,
                        "status": "edited",
                        "updated_at": utc_now(),
                    }
                )
            )

        return refined_cards
