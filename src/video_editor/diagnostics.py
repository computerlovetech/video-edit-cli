"""Workflow preflight checks for optional backends and FFmpeg capabilities."""

from __future__ import annotations

import importlib.util
from typing import Any

from video_editor import ffmpeg
from video_editor.errors import VideoEditorError


WORKFLOWS = ("base", "transcription", "vertical-captioned")


def _binary_check(name: str) -> dict[str, Any]:
    try:
        return {"name": name, "passed": True, "detail": ffmpeg.version(name)}
    except VideoEditorError as exc:
        return {"name": name, "passed": False, "detail": exc.message}


def _ffmpeg_filter_check(filter_name: str) -> dict[str, Any]:
    try:
        filters = ffmpeg.run("ffmpeg", ["-hide_banner", "-filters"]).stdout
        passed = any(
            line.split()[1:2] == [filter_name]
            for line in filters.splitlines()
            if line.strip() and not line.lstrip().startswith("Filters:")
        )
        detail = (
            f"FFmpeg filter '{filter_name}' is available"
            if passed
            else f"FFmpeg filter '{filter_name}' is unavailable; install a libass-enabled FFmpeg build"
        )
        return {
            "name": f"ffmpeg-filter:{filter_name}",
            "passed": passed,
            "detail": detail,
        }
    except VideoEditorError as exc:
        return {
            "name": f"ffmpeg-filter:{filter_name}",
            "passed": False,
            "detail": exc.message,
        }


def _python_module_check(module: str, install_hint: str) -> dict[str, Any]:
    passed = importlib.util.find_spec(module) is not None
    return {
        "name": f"python-module:{module}",
        "passed": passed,
        "detail": f"{module} is available" if passed else install_hint,
    }


def inspect(workflow: str) -> dict[str, Any]:
    """Return non-mutating readiness checks for one editing workflow."""
    checks = [_binary_check("ffmpeg"), _binary_check("ffprobe")]
    if workflow == "transcription":
        checks.append(
            _python_module_check(
                "mlx_whisper",
                "mlx-whisper is unavailable; install with `uv sync --extra mlx` on Apple Silicon",
            )
        )
    if workflow == "vertical-captioned":
        checks.append(_ffmpeg_filter_check("subtitles"))
    return {
        "workflow": workflow,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
