import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from frontend import api_client


STATIC_DIR = Path(__file__).with_name("static")


def _extract_error_detail(exc: api_client.ApiClientError) -> str:
    if exc.details:
        try:
            payload = json.loads(exc.details)
        except json.JSONDecodeError:
            return exc.details
        if isinstance(payload, dict) and isinstance(payload.get("detail"), str):
            return payload["detail"]
        return exc.details
    return str(exc)


def _raise_proxy_error(exc: api_client.ApiClientError) -> None:
    raise HTTPException(
        status_code=exc.status_code or 502,
        detail=_extract_error_detail(exc),
    ) from exc


async def _read_json_request(request: Request) -> dict[str, object]:
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON request body.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")
    return payload


def create_app(api_base_url: str | None = None) -> FastAPI:
    app = FastAPI(
        title="Anki Card Maker Frontend",
        version="0.1.0",
        description="Browser-based frontend for the Anki Card Maker API.",
    )
    app.state.api_base_url = api_base_url or os.getenv(
        "ANKI_CARD_MAKER_API_URL",
        "http://localhost:8000",
    )
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/health")
    def backend_health(http_request: Request) -> dict[str, object]:
        try:
            return api_client.get_health(http_request.app.state.api_base_url)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/overview")
    def overview(http_request: Request) -> dict[str, object]:
        try:
            return api_client.get_overview(http_request.app.state.api_base_url)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/documents")
    def list_documents(http_request: Request) -> list[dict[str, object]]:
        try:
            return api_client.list_documents(http_request.app.state.api_base_url)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.post("/api/documents")
    async def upload_document(http_request: Request) -> dict[str, object]:
        payload = await _read_json_request(http_request)
        try:
            return api_client.upload_document(http_request.app.state.api_base_url, payload)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/documents/{document_id}")
    def get_document(document_id: str, http_request: Request) -> dict[str, object]:
        try:
            return api_client.get_document(http_request.app.state.api_base_url, document_id)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/runs")
    def list_runs(http_request: Request) -> list[dict[str, object]]:
        try:
            return api_client.list_runs(http_request.app.state.api_base_url)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.post("/api/runs")
    async def create_run(http_request: Request) -> dict[str, object]:
        payload = await _read_json_request(http_request)
        try:
            return api_client.create_run(http_request.app.state.api_base_url, payload)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str, http_request: Request) -> dict[str, object]:
        try:
            return api_client.get_run(http_request.app.state.api_base_url, run_id)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/runs/{run_id}/cards")
    def list_run_cards(run_id: str, http_request: Request) -> list[dict[str, object]]:
        try:
            return api_client.list_run_cards(http_request.app.state.api_base_url, run_id)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/runs/{run_id}/improvements")
    def list_improvements(run_id: str, http_request: Request) -> list[dict[str, object]]:
        try:
            return api_client.list_improvements(http_request.app.state.api_base_url, run_id)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.post("/api/runs/{run_id}/improvements")
    async def apply_improvements(run_id: str, http_request: Request) -> dict[str, object]:
        payload = await _read_json_request(http_request)
        try:
            return api_client.apply_improvements(
                http_request.app.state.api_base_url,
                run_id,
                payload,
            )
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.post("/api/runs/{run_id}/exports")
    async def create_export(run_id: str, http_request: Request) -> dict[str, object]:
        payload = await _read_json_request(http_request)
        try:
            return api_client.create_export(
                http_request.app.state.api_base_url,
                run_id,
                payload,
            )
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/exports/{export_id}")
    def get_export(export_id: str, http_request: Request) -> dict[str, object]:
        try:
            return api_client.get_export(http_request.app.state.api_base_url, export_id)
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)

    @app.get("/api/exports/{export_id}/download")
    def download_export(export_id: str, http_request: Request) -> Response:
        try:
            export_details = api_client.get_export(
                http_request.app.state.api_base_url,
                export_id,
            )
            media_type = str(export_details.get("media_type", "text/csv"))
            filename = str(export_details.get("filename", f"{export_id}.txt"))
            content = api_client.download_export(
                http_request.app.state.api_base_url,
                export_id,
                media_type,
            )
        except api_client.ApiClientError as exc:
            _raise_proxy_error(exc)
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return app


app = create_app()
