import json
from urllib import error, request


class ApiClientError(Exception):
    """Raised when the frontend client cannot complete an API request."""


def _request_json(
    api_url: str,
    *,
    method: str,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    api_request = request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method=method,
    )
    try:
        with request.urlopen(api_request) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8")
        raise ApiClientError(f"API request failed with status {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise ApiClientError(f"Could not reach backend API: {exc.reason}") from exc


def _request_text(
    api_url: str,
    *,
    method: str,
    accept: str,
) -> str:
    api_request = request.Request(
        api_url,
        headers={"Accept": accept},
        method=method,
    )
    try:
        with request.urlopen(api_request) as response:
            return response.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8")
        raise ApiClientError(f"API request failed with status {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise ApiClientError(f"Could not reach backend API: {exc.reason}") from exc


def generate_cards_from_document(
    api_base_url: str,
    payload: dict[str, object],
) -> str:
    output_type = str(payload.get("output_type", "csv"))
    if output_type != "csv":
        raise ApiClientError(f"Unsupported output type for frontend client: {output_type}")

    base_url = api_base_url.rstrip("/")
    document_response = _request_json(
        f"{base_url}/documents",
        method="POST",
        payload={
            "filename": payload["filename"],
            "content": payload["content"],
            "source_type": payload.get("source_type"),
            "title": payload.get("title"),
            "document_id": payload.get("document_id"),
        },
    )
    run_response = _request_json(
        f"{base_url}/runs",
        method="POST",
        payload={
            "document_ids": [document_response["document_id"]],
            "workflow_plugin_id": payload["workflow_plugin_id"],
            "workflow_config": payload.get("workflow_config", {}),
        },
    )
    export_response = _request_json(
        f"{base_url}/runs/{run_response['run_id']}/exports",
        method="POST",
        payload={"exporter_id": output_type},
    )
    return _request_text(
        f"{base_url}/exports/{export_response['export_id']}/download",
        method="GET",
        accept="text/csv",
    )
