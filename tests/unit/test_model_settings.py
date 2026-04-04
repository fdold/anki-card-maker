import json

import pytest

from backend.models import MODEL_PROFILES_FILE_ENV, load_model_settings


def test_load_model_settings_supports_list_payload(tmp_path) -> None:
    profiles_file = tmp_path / "profiles.json"
    profiles_file.write_text(
        json.dumps(
            [
                {
                    "profile_id": "ollama_generation_default",
                    "provider": "ollama",
                    "model_name": "qwen3:8b",
                    "base_url": "http://ollama-default:11434",
                    "supports_structured_output": True,
                }
            ]
        ),
        encoding="utf-8",
    )

    settings = load_model_settings(profiles_file=profiles_file)

    assert len(settings.profiles) == 1
    assert settings.profiles[0].profile_id == "ollama_generation_default"


def test_load_model_settings_supports_env_path(tmp_path) -> None:
    profiles_file = tmp_path / "profiles.json"
    profiles_file.write_text(
        json.dumps({"profiles": []}),
        encoding="utf-8",
    )

    settings = load_model_settings(
        env={MODEL_PROFILES_FILE_ENV: str(profiles_file)},
    )

    assert settings.profiles == []


def test_load_model_settings_rejects_duplicate_profile_ids(tmp_path) -> None:
    profiles_file = tmp_path / "profiles.json"
    profiles_file.write_text(
        json.dumps(
            [
                {
                    "profile_id": "duplicate",
                    "provider": "ollama",
                    "model_name": "qwen3:8b",
                    "base_url": "http://ollama-default:11434",
                },
                {
                    "profile_id": "duplicate",
                    "provider": "ollama",
                    "model_name": "llama3.1:8b",
                    "base_url": "http://ollama-default:11434",
                },
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate model profile ids: duplicate"):
        load_model_settings(profiles_file=profiles_file)
