import json
import os
import time
from collections.abc import Callable

import httpx

from backend.models.settings import MODEL_PROFILES_FILE_ENV, load_model_settings

OLLAMA_INIT_BASE_URL_ENV = "OLLAMA_INIT_BASE_URL"
OLLAMA_INIT_MAX_ATTEMPTS_ENV = "OLLAMA_INIT_MAX_ATTEMPTS"
OLLAMA_INIT_DELAY_SECONDS_ENV = "OLLAMA_INIT_DELAY_SECONDS"
PULL_PROGRESS_LOG_STEP = 5


def normalize_ollama_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/api"):
        return normalized[:-4]
    return normalized


def resolve_models_for_base_url(
    *,
    profiles_file: str | None,
    target_base_url: str,
) -> list[str]:
    settings = load_model_settings(profiles_file=profiles_file)
    normalized_target = normalize_ollama_base_url(target_base_url)
    resolved_models: list[str] = []

    for profile in settings.profiles:
        if profile.provider != "ollama":
            continue
        if normalize_ollama_base_url(profile.base_url) != normalized_target:
            continue
        if profile.model_name in resolved_models:
            continue
        resolved_models.append(profile.model_name)

    return resolved_models


def wait_for_ollama(
    *,
    base_url: str,
    client: httpx.Client,
    max_attempts: int = 60,
    delay_seconds: float = 1.0,
    logger: Callable[[str], None] = print,
) -> None:
    tags_url = f"{normalize_ollama_base_url(base_url)}/api/tags"
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.get(tags_url)
            response.raise_for_status()
            logger(f"Ollama is ready at {normalize_ollama_base_url(base_url)}.")
            return
        except httpx.HTTPError as exc:
            last_error = exc
            logger(
                f"Waiting for Ollama at {normalize_ollama_base_url(base_url)} "
                f"(attempt {attempt}/{max_attempts})..."
            )
            time.sleep(delay_seconds)

    raise RuntimeError(
        f"Ollama at {normalize_ollama_base_url(base_url)} did not become ready."
    ) from last_error


def list_installed_models(
    *,
    base_url: str,
    client: httpx.Client,
) -> set[str]:
    response = client.get(f"{normalize_ollama_base_url(base_url)}/api/tags")
    response.raise_for_status()
    payload = response.json()
    models = payload.get("models", [])

    installed_models: set[str] = set()
    if not isinstance(models, list):
        return installed_models

    for model in models:
        if not isinstance(model, dict):
            continue
        name = model.get("name")
        if isinstance(name, str) and name.strip():
            installed_models.add(name.strip())

    return installed_models


def pull_model(
    *,
    base_url: str,
    model_name: str,
    client: httpx.Client,
    logger: Callable[[str], None] = print,
) -> None:
    endpoint = f"{normalize_ollama_base_url(base_url)}/api/pull"
    with client.stream(
        "POST",
        endpoint,
        json={"model": model_name},
    ) as response:
        response.raise_for_status()

        last_status: str | None = None
        last_progress_bucket = -1

        for line in response.iter_lines():
            if not line:
                continue

            payload = json.loads(line)
            if not isinstance(payload, dict):
                continue

            error_message = payload.get("error")
            if isinstance(error_message, str) and error_message.strip():
                raise RuntimeError(
                    f"Ollama reported a pull error for '{model_name}': {error_message.strip()}"
                )

            status = payload.get("status")
            completed = payload.get("completed")
            total = payload.get("total")

            if not isinstance(status, str) or not status.strip():
                continue

            normalized_status = status.strip()
            progress_bucket = _get_progress_bucket(completed, total)
            should_log = False
            if normalized_status != last_status:
                should_log = True
            elif progress_bucket is not None and progress_bucket > last_progress_bucket:
                should_log = True

            if should_log:
                logger(
                    _format_pull_status_message(
                        model_name=model_name,
                        status=normalized_status,
                        completed=completed,
                        total=total,
                    )
                )

            last_status = normalized_status
            if progress_bucket is not None:
                last_progress_bucket = progress_bucket


def ensure_models_present(
    *,
    base_url: str,
    model_names: list[str],
    client: httpx.Client,
    logger: Callable[[str], None] = print,
) -> None:
    if not model_names:
        logger(
            f"No Ollama models configured for {normalize_ollama_base_url(base_url)}. "
            "Skipping provisioning."
        )
        return

    installed_models = list_installed_models(base_url=base_url, client=client)

    for model_name in model_names:
        if model_name in installed_models:
            logger(f"Ollama model '{model_name}' is already available.")
            continue

        logger(f"Pulling Ollama model '{model_name}'...")
        pull_model(
            base_url=base_url,
            model_name=model_name,
            client=client,
            logger=logger,
        )
        logger(f"Finished pulling Ollama model '{model_name}'.")


def _get_progress_bucket(completed: object, total: object) -> int | None:
    if not isinstance(completed, int) or not isinstance(total, int) or total <= 0:
        return None
    percentage = (completed / total) * 100
    return int(percentage // PULL_PROGRESS_LOG_STEP)


def _format_pull_status_message(
    *,
    model_name: str,
    status: str,
    completed: object,
    total: object,
) -> str:
    if isinstance(completed, int) and isinstance(total, int) and total > 0:
        percentage = min((completed / total) * 100, 100.0)
        return (
            f"Ollama pull '{model_name}': {status} "
            f"({percentage:.1f}%, {_format_bytes(completed)} / {_format_bytes(total)})"
        )
    return f"Ollama pull '{model_name}': {status}"


def _format_bytes(num_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0


def main() -> None:
    profiles_file = os.environ.get(MODEL_PROFILES_FILE_ENV)
    target_base_url = os.environ.get(OLLAMA_INIT_BASE_URL_ENV, "http://ollama-default:11434")
    max_attempts = int(os.environ.get(OLLAMA_INIT_MAX_ATTEMPTS_ENV, "60"))
    delay_seconds = float(os.environ.get(OLLAMA_INIT_DELAY_SECONDS_ENV, "1"))
    model_names = resolve_models_for_base_url(
        profiles_file=profiles_file,
        target_base_url=target_base_url,
    )

    timeout = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=30.0)
    with httpx.Client(timeout=timeout) as client:
        wait_for_ollama(
            base_url=target_base_url,
            client=client,
            max_attempts=max_attempts,
            delay_seconds=delay_seconds,
        )
        ensure_models_present(
            base_url=target_base_url,
            model_names=model_names,
            client=client,
        )


if __name__ == "__main__":
    main()
