import csv
from io import StringIO

from domain.models import ExportableAnkiCard


def export_cards_to_csv(cards: list[ExportableAnkiCard]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["front", "back", "tags"])
    for card in cards:
        writer.writerow([card.front, card.back, " ".join(card.tags)])
    return buffer.getvalue()

