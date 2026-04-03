from domain.models import RunCard, WorkflowImprovementRequest
from backend.pipeline.parsers.txt_parser import parse_txt_document
from plugins.workflows.basic_text_workflow import (
    BasicTextWorkflowConfig,
    BasicTextWorkflowPlugin,
)


def test_basic_text_workflow_generates_traceable_cards() -> None:
    plugin = BasicTextWorkflowPlugin()
    parsed = parse_txt_document("doc-1", "Biology", "Cells are the basic unit of life.")

    cards = plugin.generate_cards(parsed, BasicTextWorkflowConfig(max_cards=5))

    assert len(cards) == 1
    assert cards[0].workflow_plugin_id == plugin.manifest.plugin_id
    assert cards[0].source.section == "Biology"
    assert cards[0].back == "Cells are the basic unit of life."


def test_basic_text_workflow_exposes_its_own_config_schema() -> None:
    plugin = BasicTextWorkflowPlugin()

    assert plugin.manifest.config_schema["title"] == "BasicTextWorkflowConfig"
    assert "max_cards" in plugin.manifest.config_schema["properties"]
    assert "card_style" in plugin.manifest.config_schema["properties"]
    assert "prompt_refine_selected" in plugin.manifest.supported_operations
    assert "prompt_refine_all" in plugin.manifest.supported_operations


def test_basic_text_workflow_can_apply_prompt_refinement() -> None:
    plugin = BasicTextWorkflowPlugin()
    refined_cards = plugin.apply_improvement(
        WorkflowImprovementRequest(
            action_type="prompt_refine_selected",
            run_id="run-1",
            prompt="Make this more concise and keep it a question",
            cards=[
                RunCard(
                    card_id="card-1",
                    run_id="run-1",
                    front="What is stated in section 'Biology'.",
                    back="Cells are the basic unit of life. They form tissues.",
                    source={"section": "Biology", "position": 0},
                    tags=["generated", "txt"],
                    workflow_plugin_id=plugin.manifest.plugin_id,
                    original_front="What is stated in section 'Biology'.",
                    original_back="Cells are the basic unit of life. They form tissues.",
                )
            ],
        ),
        BasicTextWorkflowConfig(max_cards=5),
    )

    assert len(refined_cards) == 1
    assert refined_cards[0].front.endswith("?")
    assert refined_cards[0].back == "Cells are the basic unit of life."
    assert "improved" in refined_cards[0].tags
    assert refined_cards[0].status == "edited"
