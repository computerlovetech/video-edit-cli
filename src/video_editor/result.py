"""Command result envelope: one JSON object on stdout per command."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from video_editor import SCHEMA_VERSION


def artifact(path: Path | str, kind: str) -> dict[str, str]:
    return {"path": str(path), "kind": kind}


def emit_success(
    command: str,
    data: dict[str, Any],
    artifacts: list[dict[str, str]] | None = None,
) -> None:
    envelope = {
        "ok": True,
        "command": command,
        "schema_version": SCHEMA_VERSION,
        "artifacts": artifacts or [],
        "data": data,
    }
    json.dump(envelope, sys.stdout, indent=2)
    sys.stdout.write("\n")


def emit_error(command: str, code: str, message: str) -> None:
    envelope = {
        "ok": False,
        "command": command,
        "schema_version": SCHEMA_VERSION,
        "error": {"code": code, "message": message},
    }
    json.dump(envelope, sys.stdout, indent=2)
    sys.stdout.write("\n")
    print(f"error [{code}]: {message}", file=sys.stderr)
