"""External asset inspection and final-output validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from video_editor import media, subtitles
from video_editor.audio.analysis import measure_loudness
from video_editor.errors import InvalidInputError

MEDIA_SUFFIXES = {
    ".mp4",
    ".mov",
    ".mkv",
    ".m4v",
    ".webm",
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
FONT_SUFFIXES = {".ttf", ".otf", ".ttc", ".woff", ".woff2"}


def inspect_asset(path: Path) -> dict[str, Any]:
    """Classify and validate one external asset (media, image, font, subtitle)."""
    if not path.is_file():
        raise InvalidInputError(f"asset not found: {path}")
    suffix = path.suffix.lower()
    if suffix in FONT_SUFFIXES:
        return {"path": str(path), "kind": "font", "size_bytes": path.stat().st_size}
    if suffix in (".srt", ".vtt"):
        last_end = subtitles.parse_srt_last_end(path)
        return {"path": str(path), "kind": "subtitles", "last_cue_end": last_end}
    if suffix in MEDIA_SUFFIXES or suffix in IMAGE_SUFFIXES:
        info = media.probe(path)
        types = {s["type"] for s in info["streams"]}
        if suffix in IMAGE_SUFFIXES:
            kind = "image"
        elif "video" in types:
            kind = "video"
        else:
            kind = "audio"
        return {"kind": kind, **info}
    raise InvalidInputError(
        f"unrecognized asset type '{suffix}' for {path}; "
        "expected media, image, font, or subtitle file"
    )


def validate_output(
    path: Path,
    profile: dict[str, Any] | None = None,
    expect_duration: float | None = None,
    duration_tolerance: float = 0.5,
    loudness_tolerance: float = 1.5,
    expect_subtitles: bool = False,
    subtitle_file: Path | None = None,
    expect_canvas: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Check a final render against expected streams, canvas, duration, loudness."""
    info = media.probe(path)
    issues: list[str] = []
    types = [s["type"] for s in info["streams"]]
    if "video" not in types:
        issues.append("no video stream")
    if "audio" not in types:
        issues.append("no audio stream")

    video = next((s for s in info["streams"] if s["type"] == "video"), None)
    checks: dict[str, Any] = {"streams": types}

    if expect_canvas and video:
        actual_canvas = (video["width"], video["height"])
        checks["canvas"] = f"{video['width']}x{video['height']}@{video['frame_rate']}"
        if actual_canvas != expect_canvas:
            issues.append(
                f"canvas {video['width']}x{video['height']} != "
                f"expected {expect_canvas[0]}x{expect_canvas[1]}"
            )

    if profile and video:
        canvas = profile["canvas"]
        if (video["width"], video["height"]) != (canvas["width"], canvas["height"]):
            issues.append(
                f"canvas {video['width']}x{video['height']} != "
                f"expected {canvas['width']}x{canvas['height']}"
            )
        expected_fps = canvas.get("frame_rate")
        if (
            expected_fps
            and video["frame_rate"]
            and abs(video["frame_rate"] - expected_fps) > 0.1
        ):
            issues.append(
                f"frame rate {video['frame_rate']} != expected {expected_fps}"
            )
        checks["canvas"] = f"{video['width']}x{video['height']}@{video['frame_rate']}"

    duration = info["duration_seconds"] or 0.0
    checks["duration_seconds"] = duration
    if (
        expect_duration is not None
        and abs(duration - expect_duration) > duration_tolerance
    ):
        issues.append(
            f"duration {duration:.3f}s differs from expected "
            f"{expect_duration:.3f}s by more than {duration_tolerance}s"
        )

    if profile and profile.get("loudness") and "audio" in types:
        loudness = measure_loudness(path)
        checks["loudness"] = {k: v for k, v in loudness.items() if k != "raw"}
        target = profile["loudness"]
        if (
            abs(loudness["integrated_lufs"] - target["integrated_lufs"])
            > loudness_tolerance
        ):
            issues.append(
                f"integrated loudness {loudness['integrated_lufs']} LUFS outside "
                f"±{loudness_tolerance} of target {target['integrated_lufs']}"
            )
        if loudness["true_peak_dbtp"] > target["true_peak_dbtp"] + 0.3:
            issues.append(
                f"true peak {loudness['true_peak_dbtp']} dBTP above "
                f"target {target['true_peak_dbtp']}"
            )

    if expect_subtitles and "subtitle" not in types:
        issues.append("no subtitle stream in output")
    if subtitle_file is not None:
        last_end = subtitles.parse_srt_last_end(subtitle_file)
        checks["subtitle_last_cue_end"] = last_end
        if last_end > duration + 0.5:
            issues.append(
                f"subtitle timing runs to {last_end:.3f}s beyond output duration {duration:.3f}s"
            )

    return {
        "path": str(path),
        "passed": not issues,
        "validation_scope": {
            "technical": "performed",
            "visual_framing": "not_performed",
            "editorial": "not_performed",
        },
        "issues": issues,
        "checks": checks,
    }
