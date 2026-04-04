from backend.models import (
    ModelGenerationOptions,
    ModelInvocation,
    ModelInvocationRecord,
    ModelMessage,
    ModelProfile,
    ModelRequest,
)


def test_model_generation_options_can_merge_overrides() -> None:
    base_options = ModelGenerationOptions(
        temperature=0.2,
        top_p=0.9,
        stop=["END"],
    )
    override_options = ModelGenerationOptions(
        temperature=0.4,
        max_output_tokens=256,
    )

    merged = base_options.merged_with(override_options)

    assert merged.temperature == 0.4
    assert merged.top_p == 0.9
    assert merged.max_output_tokens == 256
    assert merged.stop == ["END"]


def test_model_request_uses_normalized_message_and_options_models() -> None:
    request = ModelRequest(
        profile_id="ollama_generation_default",
        purpose="card_generation",
        messages=[ModelMessage(role="user", content="Generate cards")],
    )

    assert request.messages[0].role == "user"
    assert request.options.temperature is None


def test_model_profile_exposes_default_options() -> None:
    profile = ModelProfile(
        profile_id="ollama_generation_default",
        provider="ollama",
        model_name="qwen3:8b",
        base_url="http://ollama-default:11434",
        default_options=ModelGenerationOptions(temperature=0.1),
        supports_structured_output=True,
    )

    assert profile.default_options.temperature == 0.1
    assert profile.supports_structured_output is True


def test_model_invocation_alias_stays_compatible_with_record_shape() -> None:
    invocation = ModelInvocation(
        profile_id="ollama_generation_default",
        provider="ollama",
        model_name="qwen3:8b",
        purpose="card_generation",
        status="completed",
        latency_ms=250,
    )

    record = ModelInvocationRecord.model_validate(invocation.model_dump())

    assert record.profile_id == invocation.profile_id
    assert record.status == "completed"
