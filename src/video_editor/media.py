"""Normalized media inspection built on ffprobe."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

from video_editor import ffmpeg
from video_editor.errors import InvalidInputError


def _parse_rate(rate: str | None) -> float | None:
    if not rate or rate in ("0/0", "N/A"):
        return None
    try:
        return float(Fraction(rate))
    except (ValueError, ZeroDivisionError):
        return None


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def probe(path: Path) -> dict[str, Any]:
    """Return normalized container and per-stream metadata for one media file."""
    if not path.is_file():
        raise InvalidInputError(f"input file not found: {path}")
    raw = ffmpeg.ffprobe_json(["-show_format", "-show_streams", str(path)])
    fmt = raw.get("format", {})
    streams: list[dict[str, Any]] = []
    for stream in raw.get("streams", []):
        kind = stream.get("codec_type")
        normalized: dict[str, Any] = {
            "index": stream.get("index"),
            "type": kind,
            "codec": stream.get("codec_name"),
            "duration_seconds": _float(stream.get("duration")),
        }
        if kind == "video":
            normalized.update(
                {
                    "width": stream.get("width"),
                    "height": stream.get("height"),
                    "frame_rate": _parse_rate(stream.get("r_frame_rate")),
                    "pixel_format": stream.get("pix_fmt"),
                }
            )
        elif kind == "audio":
            normalized.update(
                {
                    "sample_rate": int(stream["sample_rate"])
                    if stream.get("sample_rate")
                    else None,
                    "channels": stream.get("channels"),
                    "channel_layout": stream.get("channel_layout"),
                }
            )
        streams.append(normalized)
    return {
        "path": str(path.resolve()),
        "container": fmt.get("format_name"),
        "duration_seconds": _float(fmt.get("duration")),
        "size_bytes": int(fmt["size"]) if fmt.get("size") else None,
        "bit_rate": int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
        "streams": streams,
    }


def duration_of(path: Path) -> float:
    info = probe(path)
    duration = info["duration_seconds"]
    if duration is None:
        raise InvalidInputError(f"could not determine duration of {path}")
    return float(duration)


def require_range(path: Path, start: float, end: float) -> None:
    """Validate that [start, end) is a sane range within the media duration."""
    if start < 0 or end <= start:
        raise InvalidInputError(
            f"invalid range [{start}, {end}): start must be >= 0 and end > start"
        )
    duration = duration_of(path)
    if start >= duration:
        raise InvalidInputError(
            f"range start {start}s is beyond media duration {duration:.3f}s"
        )
