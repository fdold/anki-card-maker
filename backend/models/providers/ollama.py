import json
import logging
import time
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
from backend.models.ollama_runtime import resolve_ollama_base_url

logger = logging.getLogger(__name__)
STREAM_PROGRESS_LOG_INTERVAL_SECONDS = 10.0


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
        payload = {
            "model": profile.model_name,
            "messages": [self._serialize_message(message) for message in request.messages],
            "stream": True,
        }

        options = self._serialize_options(request)
        if options:
            payload["options"] = options

        if request.response_schema is not None and profile.supports_structured_output:
            payload["format"] = request.response_schema

        logger.info(
            "Starting Ollama request profile=%s model=%s purpose=%s messages=%s structured=%s",
            profile.profile_id,
            profile.model_name,
            request.purpose,
            len(request.messages),
            request.response_schema is not None,
        )

        response_payload: dict[str, object]
        try:
            with self._client_factory(profile.timeout_seconds) as client:
                resolved_base_url = resolve_ollama_base_url(profile=profile, client=client)
                endpoint = self._build_chat_endpoint(resolved_base_url)
                logger.info(
                    "Using Ollama endpoint profile=%s model=%s base_url=%s",
                    profile.profile_id,
                    profile.model_name,
                    resolved_base_url,
                )
                with client.stream("POST", endpoint, json=payload) as http_response:
                    try:
                        http_response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        response_details = self._extract_error_details(http_response)
                        raise ModelProviderError(
                            "Ollama request failed for model "
                            f"'{profile.model_name}' with status {http_response.status_code}: "
                            f"{response_details}"
                        ) from exc

                    response_payload = self._read_streamed_response(
                        http_response=http_response,
                        model_name=profile.model_name,
                        purpose=request.purpose,
                    )
        except httpx.HTTPError as exc:
            raise ModelProviderError(
                f"Ollama request failed for model '{profile.model_name}': {exc}."
            ) from exc

        usage = self._extract_usage(response_payload)
        content = response_payload.get("message", {}).get("content", "")
        if not isinstance(content, str):
            raise ModelProviderError(
                f"Ollama returned invalid content for model '{profile.model_name}'."
            )

        logger.info(
            "Completed Ollama request profile=%s model=%s purpose=%s output_chars=%s finish_reason=%s",
            profile.profile_id,
            profile.model_name,
            request.purpose,
            len(content),
            response_payload.get("done_reason"),
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
        timeout = httpx.Timeout(
            connect=timeout_seconds,
            read=None,
            write=timeout_seconds,
            pool=timeout_seconds,
        )
        return httpx.Client(timeout=timeout)

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

    @staticmethod
    def _read_streamed_response(
        *,
        http_response: httpx.Response,
        model_name: str,
        purpose: str,
    ) -> dict[str, object]:
        content_parts: list[str] = []
        accumulated_chars = 0
        final_payload: dict[str, object] | None = None
        last_progress_log_at = time.monotonic()

        for line in http_response.iter_lines():
            if not line:
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ModelProviderError(
                    f"Ollama returned invalid streamed JSON for model '{model_name}'."
                ) from exc

            if not isinstance(payload, dict):
                continue

            error_message = payload.get("error")
            if isinstance(error_message, str) and error_message.strip():
                raise ModelProviderError(
                    f"Ollama request failed for model '{model_name}': {error_message.strip()}"
                )

            message = payload.get("message")
            if isinstance(message, dict):
                content_chunk = message.get("content")
                if isinstance(content_chunk, str) and content_chunk:
                    content_parts.append(content_chunk)
                    accumulated_chars += len(content_chunk)

            final_payload = payload
            if time.monotonic() - last_progress_log_at >= STREAM_PROGRESS_LOG_INTERVAL_SECONDS:
                logger.info(
                    "Ollama response still streaming model=%s purpose=%s accumulated_chars=%s",
                    model_name,
                    purpose,
                    accumulated_chars,
                )
                last_progress_log_at = time.monotonic()

        if final_payload is None:
            raise ModelProviderError(
                f"Ollama returned an empty streamed response for model '{model_name}'."
            )

        final_message = final_payload.get("message")
        if not isinstance(final_message, dict):
            final_message = {}
        final_message["content"] = "".join(content_parts)
        final_payload["message"] = final_message
        return final_payload
