from plugins.workflows.basic_text_workflow import BasicTextWorkflowPlugin


def create_application_overview() -> dict[str, object]:
    workflow = BasicTextWorkflowPlugin()
    return {
        "active_workflow_example": workflow.manifest.model_dump(),
        "supported_input_formats": ["txt"],
        "export_targets": ["csv"],
    }

