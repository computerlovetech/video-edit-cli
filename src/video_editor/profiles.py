"""External project profiles: explicit YAML passed by path, never discovered.

Project identity (canvases, codecs, loudness targets, assets, music, fonts,
camera aliases) lives here, outside the skill and the package defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from video_editor import schemas
from video_editor.errors import InvalidInputError


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InvalidInputError(f"project profile not found: {path}")
    try:
        document = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise InvalidInputError(
            f"project profile {path} is not valid YAML: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise InvalidInputError(f"project profile {path} must be a YAML mapping")
    schemas.validate(document, "project-profile.schema.json")

    base = path.parent
    music = document.get("music")
    if music:
        music_path = (base / music["path"]).resolve()
        if not music_path.is_file():
            raise InvalidInputError(f"profile music file not found: {music_path}")
        music["path"] = str(music_path)
    for section in ("assets", "fonts"):
        mapping = document.get(section) or {}
        for key, rel in mapping.items():
            resolved = (base / rel).resolve()
            if not resolved.is_file():
                raise InvalidInputError(
                    f"profile {section[:-1]} '{key}' file not found: {resolved}"
                )
            mapping[key] = str(resolved)
    return document


def named_profile(document: dict[str, Any], name: str) -> dict[str, Any]:
    profiles = document["profiles"]
    if name not in profiles:
        known = ", ".join(sorted(profiles))
        raise InvalidInputError(
            f"unknown render profile '{name}' (profile declares: {known})"
        )
    profile: dict[str, Any] = profiles[name]
    return profile
