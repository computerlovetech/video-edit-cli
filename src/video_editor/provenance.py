"""Provenance sidecars: enough recorded detail to reproduce any derived artifact."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from video_editor import SCHEMA_VERSION
from video_editor import ffmpeg


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_sidecar(
    output: Path,
    command: str,
    inputs: list[Path],
    parameters: dict[str, Any],
    tool_commands: list[list[str]] | None = None,
) -> Path:
    """Write `<output>.provenance.json` describing how `output` was produced."""
    record = {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "created_at": utc_now(),
        "inputs": [
            {"path": str(p), "sha256": sha256_file(p)} for p in inputs if p.is_file()
        ],
        "parameters": parameters,
        "tools": {name: ffmpeg.version(name) for name in ("ffmpeg", "ffprobe")},
        "tool_commands": tool_commands or [],
        "output": {"path": str(output), "sha256": sha256_file(output)},
    }
    sidecar = output.with_name(output.name + ".provenance.json")
    sidecar.write_text(json.dumps(record, indent=2) + "\n")
    return sidecar
