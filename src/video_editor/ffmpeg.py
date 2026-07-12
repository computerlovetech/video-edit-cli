"""Locate and run the required external FFmpeg binaries."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from video_editor.errors import MissingBinaryError, ToolFailureError


def binary_path(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise MissingBinaryError(name)
    return path


def run(binary: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run ffmpeg/ffprobe non-interactively; raise ToolFailureError on non-zero exit."""
    path = binary_path(binary)
    cmd = [path, *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()[-8:]
        raise ToolFailureError(
            f"{binary} exited with {proc.returncode}: " + " | ".join(tail)
        )
    return proc


def run_ffmpeg(args: list[str]) -> subprocess.CompletedProcess[str]:
    return run("ffmpeg", ["-hide_banner", "-nostdin", "-y", *args])


def ffprobe_json(args: list[str]) -> dict[str, Any]:
    proc = run("ffprobe", ["-v", "error", "-of", "json", *args])
    try:
        result: dict[str, Any] = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ToolFailureError(f"ffprobe produced invalid JSON: {exc}") from exc
    return result


def version(binary: str) -> str:
    proc = run(binary, ["-version"])
    return proc.stdout.splitlines()[0] if proc.stdout else "unknown"
