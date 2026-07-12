"""Audio-based synchronization between separately recorded sources.

`analyze` estimates the offset by cross-correlating low-rate loudness
envelopes — pure evidence, it never rewrites sources. `apply` creates an
aligned derivative or a mapping file from an explicitly approved offset.
"""

from __future__ import annotations

import array
import json
import math
import subprocess
from pathlib import Path
from typing import Any

from video_editor import ffmpeg
from video_editor.errors import InvalidInputError, ToolFailureError
from video_editor.provenance import utc_now

ENVELOPE_HZ = 100
SAMPLE_RATE = 8000


def _envelope(path: Path) -> list[float]:
    """RMS envelope at ENVELOPE_HZ from mono 8 kHz PCM."""
    if not path.is_file():
        raise InvalidInputError(f"input file not found: {path}")
    binary = ffmpeg.binary_path("ffmpeg")
    proc = subprocess.run(
        [
            binary,
            "-hide_banner",
            "-nostdin",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-f",
            "s16le",
            "-",
        ],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ToolFailureError(
            f"ffmpeg failed extracting audio from {path}: "
            + proc.stderr.decode(errors="replace").strip().splitlines()[-1]
        )
    samples = array.array("h")
    samples.frombytes(proc.stdout[: len(proc.stdout) // 2 * 2])
    window = SAMPLE_RATE // ENVELOPE_HZ
    envelope = []
    for i in range(0, len(samples) - window, window):
        acc = 0.0
        for j in range(i, i + window):
            value = samples[j] / 32768.0
            acc += value * value
        envelope.append(math.sqrt(acc / window))
    return envelope


def _normalize(env: list[float]) -> list[float]:
    mean = sum(env) / len(env)
    centered = [v - mean for v in env]
    norm = math.sqrt(sum(v * v for v in centered)) or 1.0
    return [v / norm for v in centered]


def analyze(reference: Path, other: Path, max_offset: float = 30.0) -> dict[str, Any]:
    """Estimated offset in seconds such that `other` content = reference + offset."""
    env_ref = _normalize(_envelope(reference))
    env_other = _normalize(_envelope(other))
    if len(env_ref) < ENVELOPE_HZ or len(env_other) < ENVELOPE_HZ:
        raise InvalidInputError("sources are too short to synchronize (<1s of audio)")

    max_lag = int(max_offset * ENVELOPE_HZ)
    scores: list[tuple[float, int]] = []
    for lag in range(-max_lag, max_lag + 1):
        acc = 0.0
        for i, value in enumerate(env_ref):
            j = i + lag
            if 0 <= j < len(env_other):
                acc += value * env_other[j]
        scores.append((acc, lag))
    scores.sort(reverse=True)
    best_score, best_lag = scores[0]
    runner_up = next(
        (score for score, lag in scores[1:] if abs(lag - best_lag) > ENVELOPE_HZ // 5),
        0.0,
    )
    confidence = best_score / runner_up if runner_up > 0 else float("inf")
    return {
        "reference": str(reference),
        "other": str(other),
        "offset_seconds": round(best_lag / ENVELOPE_HZ, 3),
        "peak_correlation": round(best_score, 4),
        "confidence_ratio": round(confidence, 3) if math.isfinite(confidence) else None,
        "candidates": [
            {"offset_seconds": lag / ENVELOPE_HZ, "correlation": round(score, 4)}
            for score, lag in scores[:5]
        ],
        "note": "offset is where reference content appears in the other source; "
        "trim that many seconds from the other source to align",
    }


def apply(source: Path, offset: float, output: Path) -> dict[str, Any]:
    """Create an aligned derivative (or a .json mapping) from an approved offset."""
    if not source.is_file():
        raise InvalidInputError(f"input file not found: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".json":
        mapping = {
            "kind": "sync-mapping",
            "created_at": utc_now(),
            "source": str(source),
            "offset_seconds": offset,
            "aligned_time": "source_time - offset",
        }
        output.write_text(json.dumps(mapping, indent=2) + "\n")
        return {"mode": "metadata", "output": str(output), "offset_seconds": offset}
    if offset < 0:
        raise InvalidInputError(
            "negative offset: swap arguments so the trimmed source is the later one, "
            "or write a .json mapping instead"
        )
    args = [
        "-ss",
        f"{offset:.6f}",
        "-i",
        str(source),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-c:a",
        "pcm_s24le" if output.suffix.lower() == ".mov" else "aac",
        str(output),
    ]
    ffmpeg.run_ffmpeg(args)
    return {"mode": "trim", "output": str(output), "offset_seconds": offset}
