from domain.models import WorkflowPluginConfig
from backend.pipeline.parsers.txt_parser import parse_txt_document
from plugins.workflows.basic_text_workflow import BasicTextWorkflowPlugin


def test_basic_text_workflow_generates_traceable_cards() -> None:
    plugin = BasicTextWorkflowPlugin()
    parsed = parse_txt_document("doc-1", "Biology", "Cells are the basic unit of life.")

    cards = plugin.generate_cards(parsed, WorkflowPluginConfig(max_cards=5))

    assert len(cards) == 1
    assert cards[0].workflow_plugin_id == plugin.manifest.plugin_id
    assert cards[0].source.section == "Biology"
    assert cards[0].back == "Cells are the basic unit of life."

