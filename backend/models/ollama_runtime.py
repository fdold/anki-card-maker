import logging
from dataclasses import asdict, dataclass

import httpx

from backend.models.base import ModelProfile

logger = logging.getLogger(__name__)
DEFAULT_OLLAMA_PROBE_TIMEOUT_SECONDS = 2.0


@dataclass(frozen=True, slots=True)
class OllamaEndpointStatus:
    base_url: str
    reachable: bool
    installed_models: tuple[str, ...] = ()
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class OllamaRuntimeStatus:
    profile_id: str
    provider: str
    model_name: str
    selected_runtime: str
    selected_base_url: str
    status: str
    message: str
    selected_reachable: bool
    selected_model_available: bool
    host_base_url: str | None
    host_reachable: bool
    host_model_available: bool
    container_base_url: str
    container_reachable: bool
    container_model_available: bool

    def model_dump(self) -> dict[str, object]:
        return asdict(self)


def normalize_ollama_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/api"):
        return normalized[:-4]
    return normalized


def is_ollama_available(
    *,
    base_url: str,
    client: httpx.Client,
    probe_timeout_seconds: float = DEFAULT_OLLAMA_PROBE_TIMEOUT_SECONDS,
) -> bool:
    return probe_ollama_endpoint(
        base_url=base_url,
        client=client,
        probe_timeout_seconds=probe_timeout_seconds,
    ).reachable


def probe_ollama_endpoint(
    *,
    base_url: str,
    client: httpx.Client,
    probe_timeout_seconds: float = DEFAULT_OLLAMA_PROBE_TIMEOUT_SECONDS,
    probe_cache: dict[str, OllamaEndpointStatus] | None = None,
) -> OllamaEndpointStatus:
    normalized_base_url = normalize_ollama_base_url(base_url)
    if probe_cache is not None and normalized_base_url in probe_cache:
        return probe_cache[normalized_base_url]

    try:
        response = client.get(
            f"{normalized_base_url}/api/tags",
            timeout=probe_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        status = OllamaEndpointStatus(
            base_url=normalized_base_url,
            reachable=False,
            error_message=str(exc),
        )
    else:
        models_payload = payload.get("models", [])
        installed_models: list[str] = []
        if isinstance(models_payload, list):
            for model_payload in models_payload:
                if not isinstance(model_payload, dict):
                    continue
                model_name = model_payload.get("name")
                if isinstance(model_name, str) and model_name.strip():
                    installed_models.append(model_name.strip())
        status = OllamaEndpointStatus(
            base_url=normalized_base_url,
            reachable=True,
            installed_models=tuple(installed_models),
        )

    if probe_cache is not None:
        probe_cache[normalized_base_url] = status
    return status


def describe_ollama_runtime(
    *,
    profile: ModelProfile,
    client: httpx.Client,
    probe_cache: dict[str, OllamaEndpointStatus] | None = None,
    probe_all_endpoints: bool = False,
) -> OllamaRuntimeStatus:
    container_base_url = normalize_ollama_base_url(profile.base_url)
    host_base_url = (
        normalize_ollama_base_url(profile.host_base_url)
        if profile.host_base_url is not None
        else None
    )
    host_status = None
    host_model_available = False
    if host_base_url is not None:
        host_status = probe_ollama_endpoint(
            base_url=host_base_url,
            client=client,
            probe_cache=probe_cache,
        )
        host_model_available = profile.model_name in host_status.installed_models

    if (
        profile.prefer_host_if_available
        and host_status is not None
        and host_status.reachable
        and host_model_available
        and not probe_all_endpoints
    ):
        status = OllamaRuntimeStatus(
            profile_id=profile.profile_id,
            provider=profile.provider,
            model_name=profile.model_name,
            selected_runtime="host",
            selected_base_url=host_status.base_url,
            status="ready",
            message=(
                f"Using host Ollama at {host_status.base_url} with model "
                f"'{profile.model_name}'."
            ),
            selected_reachable=True,
            selected_model_available=True,
            host_base_url=host_status.base_url,
            host_reachable=True,
            host_model_available=True,
            container_base_url=container_base_url,
            container_reachable=False,
            container_model_available=False,
        )
        logger.info(
            "Resolved Ollama runtime to host for profile=%s base_url=%s",
            profile.profile_id,
            host_status.base_url,
        )
        return status

    container_status = probe_ollama_endpoint(
        base_url=container_base_url,
        client=client,
        probe_cache=probe_cache,
    )
    container_model_available = profile.model_name in container_status.installed_models

    if (
        profile.prefer_host_if_available
        and host_status is not None
        and host_status.reachable
        and host_model_available
    ):
        status = OllamaRuntimeStatus(
            profile_id=profile.profile_id,
            provider=profile.provider,
            model_name=profile.model_name,
            selected_runtime="host",
            selected_base_url=host_status.base_url,
            status="ready",
            message=(
                f"Using host Ollama at {host_status.base_url} with model "
                f"'{profile.model_name}'."
            ),
            selected_reachable=True,
            selected_model_available=True,
            host_base_url=host_status.base_url,
            host_reachable=True,
            host_model_available=True,
            container_base_url=container_status.base_url,
            container_reachable=container_status.reachable,
            container_model_available=container_model_available,
        )
        logger.info(
            "Resolved Ollama runtime to host for profile=%s base_url=%s",
            profile.profile_id,
            host_status.base_url,
        )
        return status

    if container_status.reachable and container_model_available:
        message = (
            f"Using local Ollama container at {container_status.base_url} with model "
            f"'{profile.model_name}'."
        )
        if profile.prefer_host_if_available and host_status is not None:
            if not host_status.reachable:
                message = (
                    f"Host Ollama unavailable; using local Ollama container at "
                    f"{container_status.base_url} with model '{profile.model_name}'."
                )
            elif not host_model_available:
                message = (
                    f"Host Ollama at {host_status.base_url} is reachable but model "
                    f"'{profile.model_name}' is missing; using local Ollama container at "
                    f"{container_status.base_url}."
                )
        logger.info(
            "Resolved Ollama runtime to container for profile=%s base_url=%s",
            profile.profile_id,
            container_status.base_url,
        )
        return OllamaRuntimeStatus(
            profile_id=profile.profile_id,
            provider=profile.provider,
            model_name=profile.model_name,
            selected_runtime="container",
            selected_base_url=container_status.base_url,
            status="ready",
            message=message,
            selected_reachable=True,
            selected_model_available=True,
            host_base_url=host_base_url,
            host_reachable=host_status.reachable if host_status is not None else False,
            host_model_available=host_model_available,
            container_base_url=container_status.base_url,
            container_reachable=True,
            container_model_available=True,
        )

    if profile.prefer_host_if_available and host_status is not None and host_status.reachable:
        return OllamaRuntimeStatus(
            profile_id=profile.profile_id,
            provider=profile.provider,
            model_name=profile.model_name,
            selected_runtime="host",
            selected_base_url=host_status.base_url,
            status="model_missing",
            message=(
                f"Host Ollama at {host_status.base_url} is reachable, but model "
                f"'{profile.model_name}' is missing."
            ),
            selected_reachable=True,
            selected_model_available=False,
            host_base_url=host_status.base_url,
            host_reachable=True,
            host_model_available=False,
            container_base_url=container_status.base_url,
            container_reachable=container_status.reachable,
            container_model_available=container_model_available,
        )

    if container_status.reachable:
        return OllamaRuntimeStatus(
            profile_id=profile.profile_id,
            provider=profile.provider,
            model_name=profile.model_name,
            selected_runtime="container",
            selected_base_url=container_status.base_url,
            status="model_missing",
            message=(
                f"Local Ollama container at {container_status.base_url} is reachable, but "
                f"model '{profile.model_name}' is missing."
            ),
            selected_reachable=True,
            selected_model_available=False,
            host_base_url=host_base_url,
            host_reachable=host_status.reachable if host_status is not None else False,
            host_model_available=host_model_available,
            container_base_url=container_status.base_url,
            container_reachable=True,
            container_model_available=False,
        )

    return OllamaRuntimeStatus(
        profile_id=profile.profile_id,
        provider=profile.provider,
        model_name=profile.model_name,
        selected_runtime="container",
        selected_base_url=container_status.base_url,
        status="unavailable",
        message=(
            f"No Ollama runtime is reachable for profile '{profile.profile_id}'. "
            "Start native Ollama on the host or enable the local Compose profile with "
            "`docker compose --profile local-ollama up --build`."
        ),
        selected_reachable=False,
        selected_model_available=False,
        host_base_url=host_base_url,
        host_reachable=host_status.reachable if host_status is not None else False,
        host_model_available=host_model_available,
        container_base_url=container_status.base_url,
        container_reachable=False,
        container_model_available=False,
    )


def resolve_ollama_base_url(
    *,
    profile: ModelProfile,
    client: httpx.Client,
) -> str:
    return describe_ollama_runtime(profile=profile, client=client).selected_base_url
