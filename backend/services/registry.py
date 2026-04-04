from dataclasses import dataclass
from typing import Callable

from backend.exporters.csv_exporter import export_cards_to_csv
from backend.pipeline.parsers.txt_parser import parse_txt_document
from domain.models import ExportableAnkiCard
from plugins.base import WorkflowPlugin
from plugins.workflows.basic_text_workflow import BasicTextWorkflowPlugin
from plugins.workflows.ollama_text_workflow import OllamaTextWorkflowPlugin


@dataclass(frozen=True, slots=True)
class ExporterDefinition:
    exporter_id: str
    media_type: str
    file_extension: str
    export: Callable[[list[ExportableAnkiCard]], str]


def get_workflow_plugin(plugin_id: str):
    workflows = {
        workflow.manifest.plugin_id: workflow for workflow in list_workflow_plugins()
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


def get_exporter(exporter_id: str) -> ExporterDefinition:
    exporters = {
        exporter.exporter_id: exporter for exporter in list_exporters()
    }
    try:
        return exporters[exporter_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported exporter: {exporter_id}") from exc


def list_workflow_plugins() -> list[WorkflowPlugin]:
    return [BasicTextWorkflowPlugin(), OllamaTextWorkflowPlugin()]


def list_exporters() -> list[ExporterDefinition]:
    return [
        ExporterDefinition(
            exporter_id="csv",
            media_type="text/csv",
            file_extension="csv",
            export=export_cards_to_csv,
        )
    ]


def create_application_overview() -> dict[str, object]:
    workflows = list_workflow_plugins()
    exporters = list_exporters()
    return {
        "active_workflow_example": workflows[0].manifest.model_dump(),
        "supported_input_formats": ["txt"],
        "available_workflow_plugins": [workflow.manifest.model_dump() for workflow in workflows],
        "available_exporters": [
            {
                "exporter_id": exporter.exporter_id,
                "media_type": exporter.media_type,
                "file_extension": exporter.file_extension,
            }
            for exporter in exporters
        ],
        "export_targets": [exporter.exporter_id for exporter in exporters],
        "api_resources": [
            "/documents",
            "/runs",
            "/runs/{run_id}/cards",
            "/runs/{run_id}/exports",
            "/exports/{export_id}",
            "/exports/{export_id}/download",
        ],
    }
