"""Cut review: enumerate render boundaries and gather evidence around each one.

Works from a render manifest (written by rendering). Continuity checks are
deterministic signals (black frames, silence gaps, words clipped by the cut);
they guide review but the agent judges the evidence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from video_editor import ffmpeg, inspection
from video_editor.errors import InvalidInputError
from video_editor.transcription import views as transcript_views


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InvalidInputError(f"render manifest not found: {path}")
    manifest: dict[str, Any] = json.loads(path.read_text())
    if "segments" not in manifest or "output" not in manifest:
        raise InvalidInputError(f"{path} is not a render manifest")
    return manifest


def list_cuts(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Each cut joins segment i (before) and segment i+1 (after)."""
    segments = manifest["segments"]
    cuts = []
    for i in range(len(segments) - 1):
        before, after = segments[i], segments[i + 1]
        cuts.append(
            {
                "cut_index": i,
                "output_time": before["output_end"],
                "before": {
                    "segment_index": before["index"],
                    "source": before["source"],
                    "source_out": before["out"],
                    "reason": before["reason"],
                },
                "after": {
                    "segment_index": after["index"],
                    "source": after["source"],
                    "source_in": after["in"],
                    "reason": after["reason"],
                },
            }
        )
    return cuts


def _detect(render: Path, start: float, end: float, filters: dict[str, str]) -> str:
    """Run detection filters over a render range and return ffmpeg's stderr log."""
    span = end - start
    args = ["-ss", f"{start:.3f}", "-t", f"{span:.3f}", "-i", str(render)]
    if "video" in filters:
        args += ["-vf", filters["video"]]
    if "audio" in filters:
        args += ["-af", filters["audio"]]
    args += ["-f", "null", "-"]
    proc = ffmpeg.run("ffmpeg", ["-hide_banner", "-nostdin", "-y", *args])
    return proc.stderr


def _clipped_word(
    transcript: dict[str, Any] | None, source_time: float
) -> dict[str, Any] | None:
    """Word whose span straddles `source_time` in the source transcript."""
    if transcript is None:
        return None
    for segment in transcript["segments"]:
        for word in segment["words"]:
            if word["start"] < source_time < word["end"]:
                return {
                    "text": word["text"],
                    "start": word["start"],
                    "end": word["end"],
                }
    return None


def inspect_cut(
    manifest: dict[str, Any],
    cut_index: int,
    output_dir: Path,
    window: float = 2.0,
    transcript_path: Path | None = None,
) -> dict[str, Any]:
    cuts = list_cuts(manifest)
    if not 0 <= cut_index < len(cuts):
        raise InvalidInputError(
            f"cut index {cut_index} out of range (render has {len(cuts)} cuts)"
        )
    cut = cuts[cut_index]
    render = Path(manifest["output"]["path"])
    if not render.is_file():
        raise InvalidInputError(f"rendered output not found: {render}")
    output_dir.mkdir(parents=True, exist_ok=True)

    boundary = cut["output_time"]
    total = manifest["segments"][-1]["output_end"]
    start = max(0.0, boundary - window)
    end = min(total, boundary + window)

    prefix = output_dir / f"cut-{cut_index}"
    artifacts: dict[str, str] = {}

    _, _times = inspection.create_filmstrip(
        render, start, end, Path(f"{prefix}-filmstrip.png"), columns=6, frames=12
    )
    artifacts["filmstrip"] = f"{prefix}-filmstrip.png"
    inspection.create_waveform(render, start, end, Path(f"{prefix}-waveform.png"))
    artifacts["waveform"] = f"{prefix}-waveform.png"
    inspection.create_preview(render, start, end, Path(f"{prefix}-preview.mp4"))
    artifacts["preview"] = f"{prefix}-preview.mp4"
    frame_offset = min(0.04, total - boundary)
    inspection.extract_frame(
        render, max(0.0, boundary - 0.04), Path(f"{prefix}-frame-before.png")
    )
    artifacts["frame_before"] = f"{prefix}-frame-before.png"
    inspection.extract_frame(
        render,
        min(total - 0.001, boundary + frame_offset),
        Path(f"{prefix}-frame-after.png"),
    )
    artifacts["frame_after"] = f"{prefix}-frame-after.png"

    log = _detect(
        render,
        start,
        end,
        {"video": "blackdetect=d=0.1", "audio": "silencedetect=n=-45dB:d=0.4"},
    )
    black_events = re.findall(r"black_start:(\d+\.?\d*)", log)
    silence_events = re.findall(r"silence_start: (-?\d+\.?\d*)", log)

    transcript = (
        transcript_views.load_transcript(transcript_path) if transcript_path else None
    )
    clipped_before = _clipped_word(transcript, cut["before"]["source_out"])
    clipped_after = _clipped_word(transcript, cut["after"]["source_in"])

    checks = {
        "black_frames_near_cut": [float(t) + start for t in black_events],
        "silence_near_cut": [float(t) + start for t in silence_events],
        "clipped_word_before": clipped_before,
        "clipped_word_after": clipped_after,
    }
    passed = (
        not checks["black_frames_near_cut"]
        and clipped_before is None
        and clipped_after is None
    )

    report = {
        "cut": cut,
        "window": {"start": start, "end": end},
        "artifacts": artifacts,
        "checks": checks,
        "passed": passed,
    }
    report_path = Path(f"{prefix}-report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    report["report_path"] = str(report_path)
    return report
