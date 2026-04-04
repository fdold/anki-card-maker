import json
from urllib import error, request


class ApiClientError(Exception):
    """Raised when the frontend client cannot complete an API request."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        details: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def _request_json(
    api_url: str,
    *,
    method: str,
    payload: dict[str, object] | None = None,
) -> object:
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
        raise ApiClientError(
            f"API request failed with status {exc.code}: {details}",
            status_code=exc.code,
            details=details,
        ) from exc
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
        raise ApiClientError(
            f"API request failed with status {exc.code}: {details}",
            status_code=exc.code,
            details=details,
        ) from exc
    except error.URLError as exc:
        raise ApiClientError(f"Could not reach backend API: {exc.reason}") from exc


def get_health(api_base_url: str) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/health",
        method="GET",
    )
    return dict(response)


def upload_document(api_base_url: str, payload: dict[str, object]) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/documents",
        method="POST",
        payload=payload,
    )
    return dict(response)


def list_documents(api_base_url: str) -> list[dict[str, object]]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/documents",
        method="GET",
    )
    return list(response)


def get_document(api_base_url: str, document_id: str) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/documents/{document_id}",
        method="GET",
    )
    return dict(response)


def create_run(api_base_url: str, payload: dict[str, object]) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/runs",
        method="POST",
        payload=payload,
    )
    return dict(response)


def list_runs(api_base_url: str) -> list[dict[str, object]]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/runs",
        method="GET",
    )
    return list(response)


def get_run(api_base_url: str, run_id: str) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/runs/{run_id}",
        method="GET",
    )
    return dict(response)


def list_run_cards(api_base_url: str, run_id: str) -> list[dict[str, object]]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/runs/{run_id}/cards",
        method="GET",
    )
    return list(response)


def apply_improvements(
    api_base_url: str,
    run_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/runs/{run_id}/improvements",
        method="POST",
        payload=payload,
    )
    return dict(response)


def list_improvements(api_base_url: str, run_id: str) -> list[dict[str, object]]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/runs/{run_id}/improvements",
        method="GET",
    )
    return list(response)


def create_export(
    api_base_url: str,
    run_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/runs/{run_id}/exports",
        method="POST",
        payload=payload,
    )
    return dict(response)


def get_export(api_base_url: str, export_id: str) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/exports/{export_id}",
        method="GET",
    )
    return dict(response)


def download_export(api_base_url: str, export_id: str, media_type: str = "text/csv") -> str:
    return _request_text(
        f"{api_base_url.rstrip('/')}/exports/{export_id}/download",
        method="GET",
        accept=media_type,
    )


def get_overview(api_base_url: str) -> dict[str, object]:
    response = _request_json(
        f"{api_base_url.rstrip('/')}/overview",
        method="GET",
    )
    return dict(response)


def generate_cards_from_document(
    api_base_url: str,
    payload: dict[str, object],
) -> str:
    output_type = str(payload.get("output_type", "csv"))
    if output_type != "csv":
        raise ApiClientError(f"Unsupported output type for frontend client: {output_type}")

    document_response = upload_document(
        api_base_url,
        payload={
            "filename": payload["filename"],
            "content": payload["content"],
            "source_type": payload.get("source_type"),
            "title": payload.get("title"),
            "document_id": payload.get("document_id"),
        },
    )
    run_response = create_run(
        api_base_url,
        payload={
            "document_ids": [document_response["document_id"]],
            "workflow_plugin_id": payload["workflow_plugin_id"],
            "workflow_config": payload.get("workflow_config", {}),
        },
    )
    export_response = create_export(
        api_base_url,
        str(run_response["run_id"]),
        payload={"exporter_id": output_type},
    )
    return download_export(api_base_url, str(export_response["export_id"]), "text/csv")
