"""Transcription backend interface.

A backend turns one media file into raw segments; `transcribe_to_document`
wraps the result in the authoritative transcript JSON document. Backends are
isolated behind this interface so the initial mlx-whisper backend can be
replaced without touching callers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from video_editor import SCHEMA_VERSION, schemas
from video_editor.errors import InvalidInputError
from video_editor.provenance import sha256_file, utc_now


class TranscriptionBackend(Protocol):
    name: str

    def transcribe(
        self, media: Path, model: str | None, language: str | None
    ) -> dict[str, Any]:
        """Return {"language": str|None, "model": str|None, "segments": [...]}.

        Each segment: {"start", "end", "text", "words": [{"text", "start",
        "end", "confidence"?}], "speaker"?}.
        """
        ...


def get_backend(name: str, fixture: Path | None = None) -> TranscriptionBackend:
    if name == "mlx-whisper":
        from video_editor.transcription.mlx_whisper import MlxWhisperBackend

        return MlxWhisperBackend()
    if name == "fixture":
        from video_editor.transcription.fixture import FixtureBackend

        if fixture is None:
            raise InvalidInputError(
                "--fixture <raw.json> is required with --backend fixture"
            )
        return FixtureBackend(fixture)
    raise InvalidInputError(f"unknown transcription backend '{name}'")


def transcribe_to_document(
    backend: TranscriptionBackend,
    media: Path,
    model: str | None,
    language: str | None,
    source_id: str | None = None,
) -> dict[str, Any]:
    if not media.is_file():
        raise InvalidInputError(f"input file not found: {media}")
    raw = backend.transcribe(media, model, language)
    document: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "path": str(media.resolve()),
            "sha256": sha256_file(media),
            "source_id": source_id,
        },
        "language": raw.get("language"),
        "backend": backend.name,
        "model": raw.get("model"),
        "created_at": utc_now(),
        "segments": raw["segments"],
    }
    schemas.validate(document, "transcript.schema.json")
    return document
