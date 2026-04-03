from backend.services.document_service import DocumentService
from backend.services.export_service import ExportService
from backend.services.improvement_service import ImprovementService
from backend.services.run_service import RunService
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.export_repository import InMemoryExportRepository
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import ImprovementAction, ImprovementBatch


def _build_services():
    document_repository = InMemoryDocumentRepository()
    run_repository = InMemoryRunRepository()
    export_repository = InMemoryExportRepository()
    document_service = DocumentService(document_repository=document_repository)
    run_service = RunService(
        document_repository=document_repository,
        run_repository=run_repository,
    )
    improvement_service = ImprovementService(run_repository=run_repository)
    export_service = ExportService(
        run_repository=run_repository,
        export_repository=export_repository,
        document_repository=document_repository,
    )
    return document_service, run_service, improvement_service, export_service


def test_export_service_creates_csv_export_from_run_cards() -> None:
    document_service, run_service, _improvement_service, export_service = _build_services()
    stored_document = document_service.upload_document(
        filename="biology.txt",
        content="Cells are the basic unit of life.\n\nDNA stores genetic information.",
        document_id="doc-1",
    )
    generation_run = run_service.create_run(
        document_ids=[stored_document.document_id],
        workflow_plugin_id="basic_text_workflow",
        workflow_config={"max_cards": 5},
    )

    export_artifact = export_service.create_export(
        run_id=generation_run.run_id,
        exporter_id="csv",
    )

    assert export_artifact.run_id == generation_run.run_id
    assert export_artifact.exporter_id == "csv"
    assert export_artifact.filename == "biology.csv"
    assert export_artifact.media_type == "text/csv"
    assert len(export_artifact.card_ids) == 2
    assert "front,back,tags" in export_artifact.content


def test_export_service_skips_deleted_cards_and_supports_selected_exports() -> None:
    document_service, run_service, improvement_service, export_service = _build_services()
    stored_document = document_service.upload_document(
        filename="biology.txt",
        content="Cells are the basic unit of life.\n\nDNA stores genetic information.",
        document_id="doc-1",
    )
    generation_run = run_service.create_run(
        document_ids=[stored_document.document_id],
        workflow_plugin_id="basic_text_workflow",
        workflow_config={"max_cards": 5},
    )
    deleted_card = generation_run.cards[1]
    improvement_service.apply_improvements(
        ImprovementBatch(
            run_id=generation_run.run_id,
            actions=[ImprovementAction(action_type="delete_card", card_id=deleted_card.card_id)],
        )
    )

    export_artifact = export_service.create_export(
        run_id=generation_run.run_id,
        exporter_id="csv",
    )

    assert len(export_artifact.card_ids) == 1
    assert "DNA stores genetic information." not in export_artifact.content

    selected_export = export_service.create_export(
        run_id=generation_run.run_id,
        exporter_id="csv",
        card_ids=[generation_run.cards[0].card_id],
    )

    assert len(selected_export.card_ids) == 1
    assert "Cells are the basic unit of life." in selected_export.content


def test_export_service_rejects_unknown_runs_exporters_and_cards() -> None:
    document_service, run_service, _improvement_service, export_service = _build_services()
    stored_document = document_service.upload_document(
        filename="biology.txt",
        content="Cells are the basic unit of life.",
        document_id="doc-1",
    )
    generation_run = run_service.create_run(
        document_ids=[stored_document.document_id],
        workflow_plugin_id="basic_text_workflow",
    )

    try:
        export_service.create_export(run_id="missing-run", exporter_id="csv")
    except ValueError as exc:
        assert str(exc) == "Unknown run: missing-run"
    else:
        raise AssertionError("Expected ValueError for unknown runs.")

    try:
        export_service.create_export(run_id=generation_run.run_id, exporter_id="pdf")
    except ValueError as exc:
        assert str(exc) == "Unsupported exporter: pdf"
    else:
        raise AssertionError("Expected ValueError for unsupported exporters.")

    try:
        export_service.create_export(
            run_id=generation_run.run_id,
            exporter_id="csv",
            card_ids=["missing-card"],
        )
    except ValueError as exc:
        assert str(exc) == "Card 'missing-card' is not exportable."
    else:
        raise AssertionError("Expected ValueError for unknown export card selections.")
