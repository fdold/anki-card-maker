from backend.exporters.csv_exporter import export_cards_to_csv
from domain.models import ExportableAnkiCard


def test_export_cards_to_csv_writes_anki_headers() -> None:
    csv_output = export_cards_to_csv(
        [ExportableAnkiCard(front="Q", back="A", tags=["tag1", "tag2"])]
    )

    assert "front,back,tags" in csv_output
    assert "Q,A,tag1 tag2" in csv_output

