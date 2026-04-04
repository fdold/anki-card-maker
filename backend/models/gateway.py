import json
import time
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from backend.models.base import (
    ModelGenerationOptions,
    ModelInvocationRecord,
    ModelMessage,
    ModelProfile,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    ModelResponseValidationError,
)
from backend.models.providers.base import ModelProvider
from backend.models.settings import ModelSettings

StructuredModelT = TypeVar("StructuredModelT", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class StructuredModelResult(Generic[StructuredModelT]):
    parsed: StructuredModelT
    response: ModelResponse
    invocation: ModelInvocationRecord


class ModelGateway:
    def __init__(
        self,
        *,
        settings: ModelSettings,
        providers: dict[str, ModelProvider],
    ) -> None:
        self._settings = settings
        self._providers = dict(providers)
        self._invocations: list[ModelInvocationRecord] = []

    def list_profiles(self) -> list[ModelProfile]:
        return list(self._settings.profiles)

    def get_profile(self, profile_id: str) -> ModelProfile:
        return self._settings.get_profile(profile_id)

    def list_invocations(self) -> list[ModelInvocationRecord]:
        return list(self._invocations)

    def consume_invocations(self) -> list[ModelInvocationRecord]:
        invocations = list(self._invocations)
        self._invocations.clear()
        return invocations

    def generate_text(
        self,
        *,
        profile_id: str,
        purpose: str,
        messages: list[ModelMessage],
        options: ModelGenerationOptions | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ModelResponse:
        profile = self.get_profile(profile_id)
        request = ModelRequest(
            profile_id=profile_id,
            purpose=purpose,
            messages=list(messages),
            options=profile.default_options.merged_with(options),
            metadata=dict(metadata or {}),
        )

        response, latency_ms = self._execute_provider(profile.provider, profile, request)
        invocation = ModelInvocationRecord(
            profile_id=profile.profile_id,
            provider=response.provider,
            model_name=response.model_name,
            purpose=purpose,
            status="completed",
            latency_ms=latency_ms,
        )
        self._invocations.append(invocation)
        return response

    def generate_structured(
        self,
        *,
        profile_id: str,
        purpose: str,
        messages: list[ModelMessage],
        response_model: type[StructuredModelT],
        options: ModelGenerationOptions | None = None,
        metadata: dict[str, object] | None = None,
    ) -> StructuredModelResult[StructuredModelT]:
        profile = self.get_profile(profile_id)
        request = ModelRequest(
            profile_id=profile_id,
            purpose=purpose,
            messages=list(messages),
            options=profile.default_options.merged_with(options),
            metadata=dict(metadata or {}),
        )

        response, latency_ms = self._execute_provider(profile.provider, profile, request)

        try:
            parsed_payload = json.loads(response.content)
            parsed = response_model.model_validate(parsed_payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            invocation = ModelInvocationRecord(
                profile_id=profile.profile_id,
                provider=response.provider,
                model_name=response.model_name,
                purpose=purpose,
                status="failed",
                latency_ms=latency_ms,
                error_message=str(exc),
            )
            self._invocations.append(invocation)
            raise ModelResponseValidationError(
                f"Model response for profile '{profile_id}' could not be validated."
            ) from exc

        invocation = ModelInvocationRecord(
            profile_id=profile.profile_id,
            provider=response.provider,
            model_name=response.model_name,
            purpose=purpose,
            status="completed",
            latency_ms=latency_ms,
        )
        self._invocations.append(invocation)
        return StructuredModelResult(
            parsed=parsed,
            response=response,
            invocation=invocation,
        )

    def _execute_provider(
        self,
        provider_name: str,
        profile: ModelProfile,
        request: ModelRequest,
    ) -> tuple[ModelResponse, int]:
        provider = self._providers.get(provider_name)
        if provider is None:
            raise ValueError(f"Unsupported model provider: {provider_name}")

        started_at = time.perf_counter()
        try:
            response = provider.generate(profile, request)
        except ModelProviderError:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            invocation = ModelInvocationRecord(
                profile_id=profile.profile_id,
                provider=profile.provider,
                model_name=profile.model_name,
                purpose=request.purpose,
                status="failed",
                latency_ms=latency_ms,
                error_message="Model provider request failed.",
            )
            self._invocations.append(invocation)
            raise
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            invocation = ModelInvocationRecord(
                profile_id=profile.profile_id,
                provider=profile.provider,
                model_name=profile.model_name,
                purpose=request.purpose,
                status="failed",
                latency_ms=latency_ms,
                error_message=str(exc),
            )
            self._invocations.append(invocation)
            raise ModelProviderError(
                f"Model provider '{provider_name}' failed unexpectedly."
            ) from exc

        latency_ms = response.latency_ms
        if latency_ms is None:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            response = response.model_copy(update={"latency_ms": latency_ms})
        return response, latency_ms
