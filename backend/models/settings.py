import json
import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from backend.models.base import ModelProfile

MODEL_PROFILES_FILE_ENV = "ANKI_CARD_MAKER_MODEL_PROFILES_FILE"


class ModelSettings(BaseModel):
    profiles: list[ModelProfile] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_profile_ids(self) -> "ModelSettings":
        profile_ids = [profile.profile_id for profile in self.profiles]
        duplicates = {
            profile_id
            for profile_id in profile_ids
            if profile_ids.count(profile_id) > 1
        }
        if duplicates:
            duplicate_list = ", ".join(sorted(duplicates))
            raise ValueError(f"Duplicate model profile ids: {duplicate_list}")
        return self

    def get_profile(self, profile_id: str) -> ModelProfile:
        for profile in self.profiles:
            if profile.profile_id == profile_id:
                return profile
        raise ValueError(f"Unknown model profile: {profile_id}")


def load_model_settings(
    *,
    profiles_file: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> ModelSettings:
    resolved_env = env or os.environ
    resolved_file = profiles_file or resolved_env.get(MODEL_PROFILES_FILE_ENV)
    if resolved_file is None:
        return ModelSettings()

    path = Path(resolved_file)
    if not path.exists():
        raise ValueError(f"Model profiles file does not exist: {path}")

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid model profiles file JSON: {path}") from exc

    if isinstance(raw_data, list):
        return ModelSettings(profiles=raw_data)
    if isinstance(raw_data, dict) and "profiles" in raw_data:
        return ModelSettings.model_validate(raw_data)

    raise ValueError(
        "Model profiles file must contain either a list of profiles or "
        "an object with a 'profiles' field."
    )
