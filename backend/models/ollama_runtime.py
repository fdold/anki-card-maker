import logging

import httpx

from backend.models.base import ModelProfile

logger = logging.getLogger(__name__)
DEFAULT_OLLAMA_PROBE_TIMEOUT_SECONDS = 2.0


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
    try:
        response = client.get(
            f"{normalize_ollama_base_url(base_url)}/api/tags",
            timeout=probe_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return False
    return True


def resolve_ollama_base_url(
    *,
    profile: ModelProfile,
    client: httpx.Client,
) -> str:
    container_base_url = normalize_ollama_base_url(profile.base_url)
    host_base_url = (
        normalize_ollama_base_url(profile.host_base_url)
        if profile.host_base_url is not None
        else None
    )

    if (
        profile.provider != "ollama"
        or not profile.prefer_host_if_available
        or host_base_url is None
    ):
        return container_base_url

    if is_ollama_available(base_url=host_base_url, client=client):
        logger.info(
            "Resolved Ollama runtime to host for profile=%s base_url=%s",
            profile.profile_id,
            host_base_url,
        )
        return host_base_url

    logger.info(
        "Host Ollama unavailable for profile=%s, falling back to container base_url=%s",
        profile.profile_id,
        container_base_url,
    )
    return container_base_url
