from frontend.cli import main


def test_cli_generates_cards_and_writes_csv(tmp_path, capsys, monkeypatch) -> None:
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


def test_cli_returns_error_for_missing_input_file(capsys) -> None:
    exit_code = main(["missing.txt"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.out


def test_cli_accepts_plugin_and_output_type_flags(capsys, monkeypatch, tmp_path) -> None:
    input_file = tmp_path / "biology.txt"
    input_file.write_text("Cells are the basic unit of life.", encoding="utf-8")

    def fake_generate_cards_from_document(api_url, payload):
        assert payload["workflow_plugin_id"] == "basic_text_workflow"
        assert payload["output_type"] == "csv"
        return "front,back,tags\nQ,A,tag\n"

    monkeypatch.setattr(
        "frontend.cli.generate_cards_from_document",
        fake_generate_cards_from_document,
    )

    exit_code = main(
        [
            str(input_file),
            "--plugin",
            "basic_text_workflow",
            "--output-type",
            "csv",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "front,back,tags" in captured.out
