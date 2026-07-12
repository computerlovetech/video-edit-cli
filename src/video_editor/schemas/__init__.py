"""JSON schemas validated at command boundaries."""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any

import jsonschema

from video_editor.errors import InvalidInputError


@cache
def load(name: str) -> dict[str, Any]:
    text = resources.files("video_editor.schemas").joinpath(name).read_text()
    schema: dict[str, Any] = json.loads(text)
    return schema


def validate(instance: Any, schema_name: str) -> None:
    try:
        jsonschema.validate(instance, load(schema_name))
    except jsonschema.ValidationError as exc:
        location = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        raise InvalidInputError(
            f"schema validation failed against {schema_name} at {location}: {exc.message}"
        ) from exc
