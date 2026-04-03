import json
from urllib import error, request


class ApiClientError(Exception):
    """Raised when the frontend client cannot complete an API request."""


def generate_cards_from_document(
    api_base_url: str,
    payload: dict[str, object],
) -> str:
    endpoint = f"{api_base_url.rstrip('/')}/generate/document"
    api_request = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(api_request) as response:
            return response.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8")
        raise ApiClientError(f"API request failed with status {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise ApiClientError(f"Could not reach backend API: {exc.reason}") from exc
