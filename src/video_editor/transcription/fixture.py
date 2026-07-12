"""Deterministic backend that replays a prepared raw-transcription JSON file.

Used by automated tests and available for development so no command depends on
model weights. The fixture file holds exactly what a real backend would return:
{"language": ..., "model": ..., "segments": [...]}.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from video_editor.errors import InvalidInputError


class FixtureBackend:
    name = "fixture"

    def __init__(self, fixture: Path) -> None:
        self._fixture = fixture

    def transcribe(
        self, media: Path, model: str | None, language: str | None
    ) -> dict[str, Any]:
        if not self._fixture.is_file():
            raise InvalidInputError(f"fixture transcript not found: {self._fixture}")
        raw: dict[str, Any] = json.loads(self._fixture.read_text())
        if "segments" not in raw:
            raise InvalidInputError(
                f"fixture transcript {self._fixture} has no 'segments' key"
            )
        return raw
