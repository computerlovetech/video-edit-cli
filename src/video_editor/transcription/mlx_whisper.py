"""mlx-whisper backend: local word-level transcription on Apple Silicon.

The `mlx-whisper` dependency is an optional extra (`video-edit-cli[mlx]`); its
absence fails cleanly without affecting other commands. Integration tests that
run real inference are opt-in via the `integration` pytest marker.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from video_editor.errors import VideoEditorError

DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


class MlxWhisperBackend:
    name = "mlx-whisper"

    def transcribe(
        self, media: Path, model: str | None, language: str | None
    ) -> dict[str, Any]:
        import importlib

        try:
            mlx_whisper = importlib.import_module("mlx_whisper")
        except ImportError as exc:
            raise VideoEditorError(
                "missing-dependency",
                "the mlx-whisper backend requires the optional 'mlx' extra; "
                "install with `uv sync --extra mlx` (Apple Silicon only)",
                exit_code=5,
            ) from exc

        model_name = model or DEFAULT_MODEL
        raw = mlx_whisper.transcribe(
            str(media),
            path_or_hf_repo=model_name,
            word_timestamps=True,
            language=language,
        )
        segments = []
        for segment in raw.get("segments", []):
            words = [
                {
                    "text": str(word["word"]).strip(),
                    "start": float(word["start"]),
                    "end": float(word["end"]),
                    "confidence": float(word["probability"])
                    if word.get("probability") is not None
                    else None,
                }
                for word in segment.get("words", [])
            ]
            segments.append(
                {
                    "start": float(segment["start"]),
                    "end": float(segment["end"]),
                    "text": str(segment["text"]).strip(),
                    "words": words,
                }
            )
        return {
            "language": raw.get("language"),
            "model": model_name,
            "segments": segments,
        }
