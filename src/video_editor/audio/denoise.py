"""Conservative neural speech denoising behind an explicit backend interface.

DeepFilterNet is the first backend; it is optional (`video-edit-cli[df]` extra)
and never applied implicitly — the agent chooses to denoise. Stronger or
generative restoration would be added as further explicit backends.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Protocol

from video_editor.errors import InvalidInputError, ToolFailureError, VideoEditorError


class DenoiseBackend(Protocol):
    name: str

    def denoise(self, source: Path, output: Path) -> dict[str, Any]:
        """Write denoised audio to `output`; return provenance details."""
        ...


class DeepFilterNetBackend:
    name = "deepfilternet"

    def denoise(self, source: Path, output: Path) -> dict[str, Any]:
        try:
            enhance_mod = importlib.import_module("df.enhance")
        except ModuleNotFoundError as exc:
            missing = exc.name or "unknown module"
            raise VideoEditorError(
                "missing-dependency",
                f"the deepfilternet backend could not import '{missing}'; "
                "install a compatible audio-restoration environment and run "
                "`video-edit-cli doctor --workflow audio-restoration`",
                exit_code=5,
            ) from exc
        except ImportError as exc:
            raise VideoEditorError(
                "incompatible-dependency",
                f"the deepfilternet backend import failed: {exc}; run "
                "`video-edit-cli doctor --workflow audio-restoration`",
                exit_code=5,
            ) from exc
        try:
            model, df_state, _ = enhance_mod.init_df()
            audio, _ = enhance_mod.load_audio(str(source), sr=df_state.sr())
            enhanced = enhance_mod.enhance(model, df_state, audio)
            enhance_mod.save_audio(str(output), enhanced, df_state.sr())
        except Exception as exc:
            raise ToolFailureError(
                f"deepfilternet failed while processing '{source}': "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        return {"model": "DeepFilterNet3", "sample_rate": df_state.sr()}


def get_backend(name: str) -> DenoiseBackend:
    if name == "deepfilternet":
        return DeepFilterNetBackend()
    raise InvalidInputError(f"unknown denoise backend '{name}'")


def denoise(source: Path, output: Path, backend_name: str) -> dict[str, Any]:
    if not source.is_file():
        raise InvalidInputError(f"input file not found: {source}")
    if output.suffix.lower() != ".wav":
        raise InvalidInputError("audio denoise output must be a .wav path (lossless)")
    backend = get_backend(backend_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    details = backend.denoise(source, output)
    if not output.is_file():
        raise VideoEditorError(
            "tool-failure", f"backend produced no output at {output}"
        )
    return {"backend": backend.name, **details}
