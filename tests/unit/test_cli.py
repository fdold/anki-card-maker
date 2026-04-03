from frontend.cli import main


def test_cli_generate_command_writes_csv(tmp_path, capsys, monkeypatch) -> None:
    input_file = tmp_path / "physics.txt"
    csv_output = tmp_path / "cards.csv"
    input_file.write_text(
        "Force equals mass times acceleration.\n\nEnergy is the capacity to do work.",
        encoding="utf-8",
    )

    def fake_generate_cards_from_document(api_url, payload):
        assert api_url == "http://localhost:8000"
        assert payload["filename"] == "physics.txt"
        assert payload["workflow_plugin_id"] == "basic_text_workflow"
        assert payload["output_type"] == "csv"
        assert "Force equals mass times acceleration." in payload["content"]
        return "front,back,tags\nWhat is stated in section 'physics'?,Force equals mass times acceleration.,generated txt\n"

    monkeypatch.setattr(
        "frontend.cli.generate_cards_from_document",
        fake_generate_cards_from_document,
    )

    exit_code = main(
        [
            "generate",
            str(input_file),
            "--csv-output",
            str(csv_output),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CSV export written to" in captured.out
    assert csv_output.exists()
    assert "front,back,tags" in csv_output.read_text(encoding="utf-8")


def test_cli_keeps_backward_compatible_file_shortcut(tmp_path, capsys, monkeypatch) -> None:
    input_file = tmp_path / "biology.txt"
    input_file.write_text("Cells are the basic unit of life.", encoding="utf-8")

    def fake_generate_cards_from_document(_api_url, _payload):
        return "front,back,tags\nQ,A,tag\n"

    monkeypatch.setattr(
        "frontend.cli.generate_cards_from_document",
        fake_generate_cards_from_document,
    )

    exit_code = main([str(input_file)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "front,back,tags" in captured.out


def test_cli_upload_command_prints_document_metadata(tmp_path, capsys, monkeypatch) -> None:
    input_file = tmp_path / "biology.txt"
    input_file.write_text("Cells are the basic unit of life.", encoding="utf-8")

    def fake_upload_document(api_url, payload):
        assert api_url == "http://localhost:8000"
        assert payload["filename"] == "biology.txt"
        return {
            "document_id": "doc-1",
            "filename": "biology.txt",
            "title": "biology",
        }

    monkeypatch.setattr("frontend.cli.upload_document", fake_upload_document)

    exit_code = main(["upload", str(input_file)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"document_id": "doc-1"' in captured.out


def test_cli_create_run_and_cards_commands_use_resource_endpoints(capsys, monkeypatch) -> None:
    def fake_create_run(api_url, payload):
        assert api_url == "http://localhost:8000"
        assert payload["document_ids"] == ["doc-1", "doc-2"]
        assert payload["workflow_plugin_id"] == "basic_text_workflow"
        assert payload["workflow_config"] == {"max_cards": 2}
        return {"run_id": "run-1", "status": "completed"}

    def fake_list_run_cards(api_url, run_id):
        assert api_url == "http://localhost:8000"
        assert run_id == "run-1"
        return [{"card_id": "card-1", "front": "Q", "back": "A"}]

    monkeypatch.setattr("frontend.cli.create_run", fake_create_run)
    monkeypatch.setattr("frontend.cli.list_run_cards", fake_list_run_cards)

    create_exit_code = main(
        [
            "create-run",
            "doc-1",
            "doc-2",
            "--workflow-config",
            '{"max_cards": 2}',
        ]
    )
    create_captured = capsys.readouterr()

    cards_exit_code = main(["cards", "run-1"])
    cards_captured = capsys.readouterr()

    assert create_exit_code == 0
    assert '"run_id": "run-1"' in create_captured.out
    assert cards_exit_code == 0
    assert '"card_id": "card-1"' in cards_captured.out


def test_cli_export_commands_support_creation_and_download(tmp_path, capsys, monkeypatch) -> None:
    output_file = tmp_path / "cards.csv"

    def fake_create_export(api_url, run_id, payload):
        assert api_url == "http://localhost:8000"
        assert run_id == "run-1"
        assert payload["exporter_id"] == "csv"
        assert payload["card_ids"] == ["card-1"]
        return {"export_id": "export-1"}

    def fake_download_export(api_url, export_id, media_type):
        assert api_url == "http://localhost:8000"
        assert export_id == "export-1"
        assert media_type == "text/csv"
        return "front,back,tags\nQ,A,tag\n"

    monkeypatch.setattr("frontend.cli.create_export", fake_create_export)
    monkeypatch.setattr("frontend.cli.download_export", fake_download_export)

    create_exit_code = main(["create-export", "run-1", "--card-id", "card-1"])
    create_captured = capsys.readouterr()

    download_exit_code = main(["download-export", "export-1", "--output", str(output_file)])
    download_captured = capsys.readouterr()

    assert create_exit_code == 0
    assert '"export_id": "export-1"' in create_captured.out
    assert download_exit_code == 0
    assert "Export written to" in download_captured.out
    assert output_file.read_text(encoding="utf-8") == "front,back,tags\nQ,A,tag\n"


def test_cli_improve_and_improvements_commands_use_api(capsys, monkeypatch) -> None:
    def fake_apply_improvements(api_url, run_id, payload):
        assert api_url == "http://localhost:8000"
        assert run_id == "run-1"
        assert payload["actions"][0]["action_type"] == "prompt_refine_selected"
        assert payload["actions"][0]["card_ids"] == ["card-1"]
        assert payload["actions"][0]["prompt"] == "Keep it a question"
        return {"run_id": "run-1", "status": "completed"}

    def fake_list_improvements(api_url, run_id):
        assert api_url == "http://localhost:8000"
        assert run_id == "run-1"
        return [{"record_id": "record-1", "action_type": "prompt_refine_selected"}]

    monkeypatch.setattr("frontend.cli.apply_improvements", fake_apply_improvements)
    monkeypatch.setattr("frontend.cli.list_improvements", fake_list_improvements)

    improve_exit_code = main(
        [
            "improve",
            "run-1",
            "--action",
            "prompt_refine_selected",
            "--target-card-id",
            "card-1",
            "--prompt",
            "Keep it a question",
        ]
    )
    improve_captured = capsys.readouterr()

    history_exit_code = main(["improvements", "run-1"])
    history_captured = capsys.readouterr()

    assert improve_exit_code == 0
    assert '"run_id": "run-1"' in improve_captured.out
    assert history_exit_code == 0
    assert '"record_id": "record-1"' in history_captured.out


def test_cli_returns_error_for_missing_input_file(capsys) -> None:
    exit_code = main(["generate", "missing.txt"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.out
