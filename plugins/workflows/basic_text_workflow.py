from domain.models import CardCandidate, ParsedContent, PluginManifest, WorkflowPluginConfig
from plugins.base import WorkflowPlugin


class BasicTextWorkflowPlugin(WorkflowPlugin):
    manifest = PluginManifest(
        plugin_id="basic_text_workflow",
        name="Basic Text Workflow",
        plugin_type="workflow",
        description="Minimal starter workflow for TXT inputs and basic cards.",
        supported_input_types=["txt"],
        config_schema=WorkflowPluginConfig.model_json_schema(),
    )

    def generate_cards(
        self,
        parsed_content: ParsedContent,
        config: WorkflowPluginConfig,
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

