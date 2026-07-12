"""Loudness-matched A/B comparison of candidate audio treatments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from video_editor import ffmpeg
from video_editor.audio.analysis import measure_loudness
from video_editor.errors import InvalidInputError
from video_editor.provenance import utc_now


def compare(
    candidates: list[Path],
    output_dir: Path,
    match_lufs: float = -20.0,
    sample_start: float = 0.0,
    sample_duration: float = 12.0,
) -> dict[str, Any]:
    """Measure candidates and write loudness-matched review excerpts + report."""
    if len(candidates) < 2:
        raise InvalidInputError("audio compare needs at least two --input candidates")
    for path in candidates:
        if not path.is_file():
            raise InvalidInputError(f"candidate not found: {path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for index, path in enumerate(candidates):
        loudness = measure_loudness(path)
        gain = round(match_lufs - loudness["integrated_lufs"], 3)
        sample = output_dir / f"candidate-{index}-{path.stem}-ab.wav"
        ffmpeg.run_ffmpeg(
            [
                "-ss",
                f"{sample_start:.3f}",
                "-t",
                f"{sample_duration:.3f}",
                "-i",
                str(path),
                "-af",
                f"volume={gain}dB",
                "-c:a",
                "pcm_s24le",
                str(sample),
            ]
        )
        entries.append(
            {
                "index": index,
                "path": str(path),
                "metrics": {k: v for k, v in loudness.items() if k != "raw"},
                "match_gain_db": gain,
                "ab_sample": str(sample),
            }
        )

    report = {
        "created_at": utc_now(),
        "match_lufs": match_lufs,
        "sample": {"start": sample_start, "duration": sample_duration},
        "candidates": entries,
        "note": "A/B samples are loudness-matched; metrics rank candidates but "
        "do not prove speech remains natural — listen before choosing.",
    }
    report_path = output_dir / "audio-compare-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    report["report_path"] = str(report_path)
    return report
