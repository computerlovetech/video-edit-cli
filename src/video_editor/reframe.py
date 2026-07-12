"""Explicit crop/reframe previews and vertical plan derivation.

The agent decides where to look; these helpers only execute explicit
instructions — `derive_short_plan` never chooses the highlight.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from video_editor import SCHEMA_VERSION, ffmpeg, media
from video_editor.errors import InvalidInputError


def parse_crop(text: str) -> dict[str, int]:
    match = re.fullmatch(r"(\d+):(\d+):(\d+):(\d+)", text)
    if not match:
        raise InvalidInputError(f"crop must be x:y:width:height, got '{text}'")
    x, y, width, height = (int(g) for g in match.groups())
    return {"x": x, "y": y, "width": width, "height": height}


def parse_canvas(text: str) -> dict[str, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", text)
    if not match:
        raise InvalidInputError(f"canvas must be WIDTHxHEIGHT, got '{text}'")
    return {"width": int(match.group(1)), "height": int(match.group(2))}


def preview_reframe(
    source: Path,
    start: float,
    end: float,
    crop: dict[str, int],
    canvas: dict[str, int],
    output: Path,
) -> list[str]:
    """Render a short preview of one explicit crop scaled onto a canvas."""
    media.require_range(source, start, end)
    info = media.probe(source)
    video = next((s for s in info["streams"] if s["type"] == "video"), None)
    if video is None:
        raise InvalidInputError(f"no video stream in {source}")
    if (
        crop["x"] + crop["width"] > video["width"]
        or crop["y"] + crop["height"] > video["height"]
    ):
        raise InvalidInputError(
            f"crop {crop} exceeds source frame {video['width']}x{video['height']}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    span = end - start
    args = [
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{span:.3f}",
        "-i",
        str(source),
        "-vf",
        (
            f"crop={crop['width']}:{crop['height']}:{crop['x']}:{crop['y']},"
            f"scale={canvas['width']}:{canvas['height']}:force_original_aspect_ratio=decrease,"
            f"pad={canvas['width']}:{canvas['height']}:(ow-iw)/2:(oh-ih)/2,setsar=1"
        ),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "26",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        str(output),
    ]
    ffmpeg.run_ffmpeg(args)
    return args


def derive_short_plan(
    source_path: Path,
    source_id: str,
    start: float,
    end: float,
    canvas: dict[str, int],
    reason: str,
    crop: dict[str, int] | None = None,
    parent_plan: str | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """New editable vertical plan for one explicit, agent-chosen source range."""
    media.require_range(source_path, start, end)
    duration = media.duration_of(source_path)
    if end > duration + 0.05:
        raise InvalidInputError(
            f"range end {end}s exceeds source duration {duration:.3f}s"
        )
    clip: dict[str, Any] = {
        "source": source_id,
        "in": start,
        "out": end,
        "reason": reason,
    }
    if crop:
        clip["crop"] = crop
    return {
        "schema_version": SCHEMA_VERSION,
        "plan_id": f"short-{uuid.uuid4().hex[:8]}",
        "created_by": created_by,
        "parent_plan": parent_plan,
        "output_canvas": {**canvas, "frame_rate": None},
        "sources": [{"id": source_id, "path": str(source_path.resolve())}],
        "timeline": [clip],
    }
