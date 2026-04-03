import argparse
import json
import os
from pathlib import Path

from frontend.api_client import (
    ApiClientError,
    apply_improvements,
    create_export,
    create_run,
    download_export,
    generate_cards_from_document,
    get_document,
    get_export,
    get_overview,
    get_run,
    list_improvements,
    list_documents,
    list_run_cards,
    list_runs,
    upload_document,
)


COMMANDS = {
    "generate",
    "overview",
    "upload",
    "documents",
    "document",
    "create-run",
    "runs",
    "run",
    "cards",
    "improve",
    "improvements",
    "create-export",
    "export",
    "download-export",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-card-maker",
        description="Frontend CLI for the resource-based Anki Card Maker API.",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("ANKI_CARD_MAKER_API_URL", "http://localhost:8000"),
        help="Base URL of the backend API.",
    )
    subparsers = parser.add_subparsers(dest="command")

    generate_parser = subparsers.add_parser(
        "generate",
        help="Upload a TXT document, create a run, export CSV, and print or write it.",
    )
    _add_generate_arguments(generate_parser)

    subparsers.add_parser("overview", help="Show API overview metadata.")
    subparsers.add_parser("documents", help="List uploaded documents.")

    document_parser = subparsers.add_parser("document", help="Fetch a single document.")
    document_parser.add_argument("document_id")

    upload_parser = subparsers.add_parser("upload", help="Upload a TXT document.")
    upload_parser.add_argument("input_file", help="Path to a UTF-8 encoded .txt file.")
    upload_parser.add_argument("--document-id")
    upload_parser.add_argument("--title")
    upload_parser.add_argument("--source-type")

    create_run_parser = subparsers.add_parser(
        "create-run",
        help="Create a workflow run from one or more uploaded documents.",
    )
    create_run_parser.add_argument("document_ids", nargs="+")
    create_run_parser.add_argument(
        "--plugin",
        "--plugin-id",
        dest="plugin_id",
        default="basic_text_workflow",
        help="Workflow plugin selected for the generation run.",
    )
    create_run_parser.add_argument(
        "--workflow-config",
        default="{}",
        help="Workflow config as a JSON object string.",
    )

    subparsers.add_parser("runs", help="List generation runs.")

    run_parser = subparsers.add_parser("run", help="Fetch a single run.")
    run_parser.add_argument("run_id")

    cards_parser = subparsers.add_parser("cards", help="List cards for a run.")
    cards_parser.add_argument("run_id")

    improve_parser = subparsers.add_parser(
        "improve",
        help="Apply one improvement action to a run.",
    )
    improve_parser.add_argument("run_id")
    improve_parser.add_argument(
        "--action",
        required=True,
        choices=[
            "edit_card",
            "delete_card",
            "rate_card",
            "rate_run",
            "prompt_refine_selected",
            "prompt_refine_all",
        ],
    )
    improve_parser.add_argument("--card-id")
    improve_parser.add_argument(
        "--target-card-id",
        dest="card_ids",
        action="append",
        default=[],
        help="Repeat to target multiple cards for prompt_refine_selected.",
    )
    improve_parser.add_argument("--front")
    improve_parser.add_argument("--back")
    improve_parser.add_argument("--rating", choices=["good", "mixed", "bad"])
    improve_parser.add_argument("--prompt")

    improvements_parser = subparsers.add_parser(
        "improvements",
        help="List the improvement history for a run.",
    )
    improvements_parser.add_argument("run_id")

    create_export_parser = subparsers.add_parser(
        "create-export",
        help="Create an export artifact for a run.",
    )
    create_export_parser.add_argument("run_id")
    create_export_parser.add_argument(
        "--exporter",
        "--exporter-id",
        dest="exporter_id",
        default="csv",
        help="Exporter identifier.",
    )
    create_export_parser.add_argument(
        "--card-id",
        dest="card_ids",
        action="append",
        default=[],
        help="Optional card id to export. Repeat for multiple cards.",
    )

    export_parser = subparsers.add_parser("export", help="Fetch export metadata.")
    export_parser.add_argument("export_id")

    download_export_parser = subparsers.add_parser(
        "download-export",
        help="Download an export artifact and print or write it.",
    )
    download_export_parser.add_argument("export_id")
    download_export_parser.add_argument("--output")
    download_export_parser.add_argument(
        "--media-type",
        default="text/csv",
        help="Expected response media type.",
    )

    return parser


def _add_generate_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input_file", help="Path to a UTF-8 encoded .txt file.")
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
    parser.add_argument(
        "--workflow-config",
        default="{}",
        help="Workflow config as a JSON object string.",
    )


def normalize_argv(argv: list[str] | None) -> list[str] | None:
    if not argv:
        return argv
    if any(token in COMMANDS for token in argv):
        return argv

    prefix: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--api-url":
            if index + 1 >= len(argv):
                return argv
            prefix.extend(argv[index : index + 2])
            index += 2
            continue
        if token.startswith("--api-url="):
            prefix.append(token)
            index += 1
            continue
        break
    return [*prefix, "generate", *argv[index:]]


def read_txt_document(input_path: str | Path) -> tuple[str, str]:
    path = Path(input_path)
    if path.suffix.lower() != ".txt":
        raise ValueError("Only .txt files are supported by the frontend CLI.")

    text = path.read_text(encoding="utf-8")
    return path.name, text


def write_text_output(content: str, output_path: str | Path) -> None:
    path = Path(output_path)
    path.write_text(content, encoding="utf-8")


def parse_json_object(raw_value: str) -> dict[str, object]:
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON object: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Workflow config must be a JSON object.")
    return parsed


def print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def handle_generate(args: argparse.Namespace) -> None:
    filename, content = read_txt_document(args.input_file)
    workflow_config = parse_json_object(args.workflow_config)
    csv_content = generate_cards_from_document(
        args.api_url,
        {
            "filename": filename,
            "content": content,
            "workflow_plugin_id": args.plugin_id,
            "output_type": args.output_type,
            "workflow_config": workflow_config,
        },
    )

    if args.output_type == "csv" and args.csv_output:
        write_text_output(csv_content, args.csv_output)
        print(f"CSV export written to {args.csv_output}")
        return
    print(csv_content)


def handle_upload(args: argparse.Namespace) -> None:
    filename, content = read_txt_document(args.input_file)
    response = upload_document(
        args.api_url,
        {
            "filename": filename,
            "content": content,
            "document_id": args.document_id,
            "title": args.title,
            "source_type": args.source_type,
        },
    )
    print_json(response)


def handle_create_run(args: argparse.Namespace) -> None:
    workflow_config = parse_json_object(args.workflow_config)
    response = create_run(
        args.api_url,
        {
            "document_ids": args.document_ids,
            "workflow_plugin_id": args.plugin_id,
            "workflow_config": workflow_config,
        },
    )
    print_json(response)


def handle_create_export(args: argparse.Namespace) -> None:
    response = create_export(
        args.api_url,
        args.run_id,
        {
            "exporter_id": args.exporter_id,
            "card_ids": args.card_ids,
        },
    )
    print_json(response)


def handle_improve(args: argparse.Namespace) -> None:
    action_payload: dict[str, object] = {
        "action_type": args.action,
        "card_ids": args.card_ids,
    }
    if args.card_id is not None:
        action_payload["card_id"] = args.card_id
    if args.front is not None:
        action_payload["front"] = args.front
    if args.back is not None:
        action_payload["back"] = args.back
    if args.rating is not None:
        action_payload["rating"] = args.rating
    if args.prompt is not None:
        action_payload["prompt"] = args.prompt

    response = apply_improvements(
        args.api_url,
        args.run_id,
        {"actions": [action_payload]},
    )
    print_json(response)


def handle_download_export(args: argparse.Namespace) -> None:
    content = download_export(args.api_url, args.export_id, args.media_type)
    if args.output:
        write_text_output(content, args.output)
        print(f"Export written to {args.output}")
        return
    print(content)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    normalized_argv = normalize_argv(argv)
    args = parser.parse_args(normalized_argv)

    try:
        if args.command == "generate":
            handle_generate(args)
        elif args.command == "overview":
            print_json(get_overview(args.api_url))
        elif args.command == "upload":
            handle_upload(args)
        elif args.command == "documents":
            print_json(list_documents(args.api_url))
        elif args.command == "document":
            print_json(get_document(args.api_url, args.document_id))
        elif args.command == "create-run":
            handle_create_run(args)
        elif args.command == "runs":
            print_json(list_runs(args.api_url))
        elif args.command == "run":
            print_json(get_run(args.api_url, args.run_id))
        elif args.command == "cards":
            print_json(list_run_cards(args.api_url, args.run_id))
        elif args.command == "improve":
            handle_improve(args)
        elif args.command == "improvements":
            print_json(list_improvements(args.api_url, args.run_id))
        elif args.command == "create-export":
            handle_create_export(args)
        elif args.command == "export":
            print_json(get_export(args.api_url, args.export_id))
        elif args.command == "download-export":
            handle_download_export(args)
        else:
            parser.print_help()
            return 1
    except (ApiClientError, FileNotFoundError, UnicodeDecodeError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
