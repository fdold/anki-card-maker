from backend.pipeline.parsers.txt_parser import parse_txt_document
from plugins.workflows.basic_text_workflow import BasicTextWorkflowPlugin


def get_workflow_plugin(plugin_id: str):
    workflows = {
        "basic_text_workflow": BasicTextWorkflowPlugin(),
    }
    try:
        return workflows[plugin_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported workflow plugin: {plugin_id}") from exc


def get_parser_for_source_type(source_type: str):
    parsers = {
        "txt": parse_txt_document,
    }
    try:
        return parsers[source_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported source type: {source_type}") from exc


def create_application_overview() -> dict[str, object]:
    workflow = BasicTextWorkflowPlugin()
    return {
        "active_workflow_example": workflow.manifest.model_dump(),
        "supported_input_formats": ["txt"],
        "available_workflow_plugins": [workflow.manifest.model_dump()],
        "export_targets": ["csv"],
    }
