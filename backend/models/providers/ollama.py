from collections.abc import Callable

import httpx

from backend.models.base import (
    ModelProfile,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from backend.models.providers.base import ModelProvider


class OllamaProvider(ModelProvider):
    def __init__(
        self,
        client_factory: Callable[[float], httpx.Client] | None = None,
    ) -> None:
        self._client_factory = client_factory or self._default_client_factory

    def generate(
        self,
        profile: ModelProfile,
        request: ModelRequest,
    ) -> ModelResponse:
        endpoint = self._build_chat_endpoint(profile.base_url)
        payload = {
            "model": profile.model_name,
            "messages": [self._serialize_message(message) for message in request.messages],
            "stream": False,
        }

        options = self._serialize_options(request)
        if options:
            payload["options"] = options

        if request.response_schema is not None and profile.supports_structured_output:
            payload["format"] = request.response_schema

        try:
            with self._client_factory(profile.timeout_seconds) as client:
                http_response = client.post(endpoint, json=payload)
        except httpx.HTTPError as exc:
            raise ModelProviderError(
                f"Ollama request failed for model '{profile.model_name}': {exc}."
            ) from exc

        try:
            http_response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            response_details = self._extract_error_details(http_response)
            raise ModelProviderError(
                "Ollama request failed for model "
                f"'{profile.model_name}' with status {http_response.status_code}: "
                f"{response_details}"
            ) from exc

        try:
            response_payload = http_response.json()
        except ValueError as exc:
            raise ModelProviderError(
                f"Ollama returned a non-JSON response for model '{profile.model_name}'."
            ) from exc

        usage = self._extract_usage(response_payload)
        content = response_payload.get("message", {}).get("content", "")
        if not isinstance(content, str):
            raise ModelProviderError(
                f"Ollama returned invalid content for model '{profile.model_name}'."
            )

        return ModelResponse(
            provider=profile.provider,
            model_name=str(response_payload.get("model") or profile.model_name),
            content=content,
            raw_payload=response_payload,
            usage=usage,
            latency_ms=self._convert_ns_to_ms(response_payload.get("total_duration")),
            finish_reason=response_payload.get("done_reason"),
        )

    @staticmethod
    def _default_client_factory(timeout_seconds: float) -> httpx.Client:
        return httpx.Client(timeout=timeout_seconds)

    @staticmethod
    def _build_chat_endpoint(base_url: str) -> str:
        normalized_base_url = base_url.rstrip("/")
        if normalized_base_url.endswith("/api"):
            return f"{normalized_base_url}/chat"
        return f"{normalized_base_url}/api/chat"

    @staticmethod
    def _serialize_message(message) -> dict[str, str]:
        payload = {
            "role": message.role,
            "content": message.content,
        }
        if message.name is not None:
            payload["name"] = message.name
        return payload

    @staticmethod
    def _serialize_options(request: ModelRequest) -> dict[str, object]:
        options: dict[str, object] = {}
        if request.options.temperature is not None:
            options["temperature"] = request.options.temperature
        if request.options.top_p is not None:
            options["top_p"] = request.options.top_p
        if request.options.seed is not None:
            options["seed"] = request.options.seed
        if request.options.max_output_tokens is not None:
            options["num_predict"] = request.options.max_output_tokens
        if request.options.stop:
            options["stop"] = list(request.options.stop)
        return options

    @staticmethod
    def _extract_usage(payload: dict[str, object]) -> ModelUsage | None:
        input_tokens = payload.get("prompt_eval_count")
        output_tokens = payload.get("eval_count")
        total_tokens = None
        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
            total_tokens = input_tokens + output_tokens

        if not any(
            isinstance(value, int)
            for value in (input_tokens, output_tokens, total_tokens)
        ):
            return None

        return ModelUsage(
            input_tokens=input_tokens if isinstance(input_tokens, int) else None,
            output_tokens=output_tokens if isinstance(output_tokens, int) else None,
            total_tokens=total_tokens,
        )

    @staticmethod
    def _convert_ns_to_ms(duration_ns: object) -> int | None:
        if not isinstance(duration_ns, int):
            return None
        return int(duration_ns / 1_000_000)

    @staticmethod
    def _extract_error_details(http_response: httpx.Response) -> str:
        try:
            payload = http_response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            error_message = payload.get("error")
            if isinstance(error_message, str) and error_message.strip():
                return error_message.strip()

        response_text = http_response.text.strip()
        if response_text:
            return response_text

        return "No error details returned by Ollama."
