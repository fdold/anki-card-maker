import argparse
import os
from pathlib import Path

from frontend.api_client import ApiClientError, generate_cards_from_document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-card-maker",
        description="Frontend CLI that sends TXT content to the backend API.",
    )
    parser.add_argument("input_file", help="Path to a UTF-8 encoded .txt file.")
    parser.add_argument(
        "--api-url",
        default=os.getenv("ANKI_CARD_MAKER_API_URL", "http://localhost:8000"),
        help="Base URL of the backend API.",
    )
    parser.add_argument(
        "--plugin",
        "--plugin-id",
        dest="plugin_id",
        default="basic_text_workflow",
        help="Workflow plugin selected for the generation run.",
    )
    parser.add_argument(
        "--output-type",
        default="csv",
        help="Requested backend output type. Currently supported: csv.",
    )
    parser.add_argument(
        "--csv-output",
        help="Optional path for exporting generated cards as Anki-compatible CSV.",
    )
    return parser


def read_txt_document(input_path: str | Path) -> tuple[str, str]:
    path = Path(input_path)
    if path.suffix.lower() != ".txt":
        raise ValueError("Only .txt files are supported by the frontend CLI.")

    text = path.read_text(encoding="utf-8")
    return path.name, text


def write_csv_output(csv_content: str, output_path: str | Path) -> None:
    path = Path(output_path)
    path.write_text(csv_content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        filename, content = read_txt_document(args.input_file)
        payload = {
            "filename": filename,
            "content": content,
            "workflow_plugin_id": args.plugin_id,
            "output_type": args.output_type,
        }
        csv_content = generate_cards_from_document(args.api_url, payload)
    except (ApiClientError, FileNotFoundError, UnicodeDecodeError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    if args.output_type == "csv" and args.csv_output:
        write_csv_output(csv_content, args.csv_output)
        print(f"CSV export written to {args.csv_output}")
    else:
        print(csv_content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
