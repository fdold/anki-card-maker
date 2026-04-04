import json

from pydantic import BaseModel, Field

from backend.models import ModelGenerationOptions, ModelMessage
from domain.models import (
    CardCandidate,
    ParsedContent,
    PluginManifest,
    RunCard,
    WorkflowImprovementRequest,
    utc_now,
)
from plugins.base import WorkflowExecutionContext, WorkflowPlugin

DEFAULT_GENERATION_TAGS = ["generated", "ollama", "txt"]


class OllamaTextWorkflowConfig(BaseModel):
    generator_model_profile: str = Field(default="ollama_generation_default", min_length=1)
    improver_model_profile: str = Field(default="ollama_improvement_default", min_length=1)
    max_cards: int = Field(default=20, ge=1, le=500)
    max_blocks: int = Field(default=20, ge=1, le=500)
    max_cards_per_block: int = Field(default=3, ge=1, le=20)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    card_style: str = Field(default="basic", min_length=1)


class OllamaGeneratedCard(BaseModel):
    front: str = Field(..., min_length=1)
    back: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class OllamaGeneratedCardBatch(BaseModel):
    cards: list[OllamaGeneratedCard] = Field(default_factory=list)


class OllamaImprovedCard(BaseModel):
    card_id: str = Field(..., min_length=1)
    front: str = Field(..., min_length=1)
    back: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class OllamaImprovedCardBatch(BaseModel):
    cards: list[OllamaImprovedCard] = Field(default_factory=list)


class OllamaTextWorkflowPlugin(WorkflowPlugin[OllamaTextWorkflowConfig]):
    config_model = OllamaTextWorkflowConfig
    base_manifest = PluginManifest(
        plugin_id="ollama_text_workflow",
        name="Ollama Text Workflow",
        plugin_type="workflow",
        description=(
            "LLM-based TXT workflow using centrally managed Ollama model profiles "
            "for structured card generation and refinement."
        ),
        supported_input_types=["txt"],
        supported_operations=["prompt_refine_selected", "prompt_refine_all"],
    )

    def generate_cards(
        self,
        parsed_content: ParsedContent,
        config: OllamaTextWorkflowConfig,
        context: WorkflowExecutionContext | None = None,
    ) -> list[CardCandidate]:
        models = self._require_models(context)
        generated_cards: list[CardCandidate] = []

        for block in parsed_content.blocks[: config.max_blocks]:
            if not block.text.strip():
                continue
            remaining_cards = config.max_cards - len(generated_cards)
            if remaining_cards <= 0:
                break

            result = models.generate_structured(
                profile_id=config.generator_model_profile,
                purpose="card_generation",
                messages=self._build_generation_messages(
                    parsed_content=parsed_content,
                    block_text=block.text,
                    block_order=block.order,
                    block_section=block.source.section,
                    card_style=config.card_style,
                    max_cards=min(remaining_cards, config.max_cards_per_block),
                ),
                response_model=OllamaGeneratedCardBatch,
                options=ModelGenerationOptions(temperature=config.temperature),
                metadata={
                    "workflow_plugin_id": self.manifest.plugin_id,
                    "block_order": block.order,
                },
            )

            for generated_card in result.parsed.cards[: min(remaining_cards, config.max_cards_per_block)]:
                front = generated_card.front.strip()
                back = generated_card.back.strip()
                if not front or not back:
                    continue
                generated_cards.append(
                    CardCandidate(
                        front=front,
                        back=back,
                        source=block.source,
                        tags=self._merge_tags(DEFAULT_GENERATION_TAGS, generated_card.tags),
                        workflow_plugin_id=self.manifest.plugin_id,
                    )
                )

        return generated_cards

    def apply_improvement(
        self,
        request: WorkflowImprovementRequest,
        config: OllamaTextWorkflowConfig,
        context: WorkflowExecutionContext | None = None,
    ) -> list[RunCard]:
        models = self._require_models(context)
        selected_cards = {card.card_id: card for card in request.cards}
        if not selected_cards:
            return []

        result = models.generate_structured(
            profile_id=config.improver_model_profile,
            purpose="card_improvement",
            messages=self._build_improvement_messages(
                request=request,
                cards=request.cards,
            ),
            response_model=OllamaImprovedCardBatch,
            options=ModelGenerationOptions(temperature=max(config.temperature - 0.1, 0.0)),
            metadata={
                "workflow_plugin_id": self.manifest.plugin_id,
                "card_count": len(request.cards),
            },
        )

        refined_cards: list[RunCard] = []
        for improved_card in result.parsed.cards:
            original_card = selected_cards.get(improved_card.card_id)
            if original_card is None:
                continue

            front = improved_card.front.strip()
            back = improved_card.back.strip()
            if not front or not back:
                continue

            refined_cards.append(
                original_card.model_copy(
                    update={
                        "front": front,
                        "back": back,
                        "tags": self._merge_tags(
                            list(original_card.tags) + ["improved"],
                            improved_card.tags,
                        ),
                        "status": "edited",
                        "updated_at": utc_now(),
                    }
                )
            )

        return refined_cards

    def _require_models(
        self,
        context: WorkflowExecutionContext | None,
    ):
        if context is None:
            raise ValueError(
                f"Workflow plugin '{self.manifest.plugin_id}' requires a workflow execution context."
            )
        return context.require_models()

    def _build_generation_messages(
        self,
        *,
        parsed_content: ParsedContent,
        block_text: str,
        block_order: int,
        block_section: str | None,
        card_style: str,
        max_cards: int,
    ) -> list[ModelMessage]:
        return [
            ModelMessage(
                role="system",
                content=(
                    "You generate high-quality Anki flashcards from source text. "
                    "Return valid JSON only. Keep cards atomic, concise, correct, "
                    "and grounded in the provided source block. Avoid trivia, "
                    "duplicates, and multi-fact cards."
                ),
            ),
            ModelMessage(
                role="user",
                content=(
                    f"Document title: {parsed_content.document.title}\n"
                    f"Section: {block_section or parsed_content.document.title}\n"
                    f"Block order: {block_order}\n"
                    f"Card style: {card_style}\n"
                    f"Maximum cards to return: {max_cards}\n"
                    "Return an object with a 'cards' array. Each card must have "
                    "'front', 'back', and optional 'tags'.\n"
                    "Source block:\n"
                    f"{block_text}"
                ),
            ),
        ]

    def _build_improvement_messages(
        self,
        *,
        request: WorkflowImprovementRequest,
        cards: list[RunCard],
    ) -> list[ModelMessage]:
        serialized_cards = [
            {
                "card_id": card.card_id,
                "front": card.front,
                "back": card.back,
                "tags": list(card.tags),
            }
            for card in cards
        ]
        return [
            ModelMessage(
                role="system",
                content=(
                    "You improve existing Anki flashcards. Return valid JSON only. "
                    "Preserve card ids exactly. Follow the user's instruction while "
                    "keeping cards concise, correct, and learnable."
                ),
            ),
            ModelMessage(
                role="user",
                content=(
                    f"Improvement request: {request.prompt}\n"
                    "Return an object with a 'cards' array. Each card must contain "
                    "'card_id', 'front', 'back', and optional 'tags'.\n"
                    f"Cards to improve:\n{json.dumps(serialized_cards, ensure_ascii=True, indent=2)}"
                ),
            ),
        ]

    @staticmethod
    def _merge_tags(base_tags: list[str], extra_tags: list[str]) -> list[str]:
        merged_tags: list[str] = []
        for tag in [*base_tags, *extra_tags]:
            normalized_tag = tag.strip()
            if not normalized_tag or normalized_tag in merged_tags:
                continue
            merged_tags.append(normalized_tag)
        return merged_tags
