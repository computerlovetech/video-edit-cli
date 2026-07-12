"""Deterministic audio quality measurement (BS.1770 loudness, peaks, silence)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from video_editor import ffmpeg
from video_editor.errors import InvalidInputError, ToolFailureError


def measure_loudness(
    path: Path,
    target_i: float = -16.0,
    target_tp: float = -1.5,
    target_lra: float = 11.0,
) -> dict[str, Any]:
    """First-pass loudnorm measurement: integrated LUFS, true peak, LRA, threshold."""
    if not path.is_file():
        raise InvalidInputError(f"input file not found: {path}")
    proc = ffmpeg.run(
        "ffmpeg",
        [
            "-hide_banner",
            "-nostdin",
            "-i",
            str(path),
            "-af",
            f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json",
            "-f",
            "null",
            "-",
        ],
    )
    match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", proc.stderr, re.DOTALL)
    if not match:
        raise ToolFailureError("loudnorm did not report measurement JSON")
    raw = json.loads(match.group(0))
    return {
        "integrated_lufs": float(raw["input_i"]),
        "true_peak_dbtp": float(raw["input_tp"]),
        "loudness_range_lu": float(raw["input_lra"]),
        "threshold_lufs": float(raw["input_thresh"]),
        "raw": raw,
    }


def analyze(path: Path) -> dict[str, Any]:
    """Loudness, true peak, clipping indicators, silence spans, bandwidth signal."""
    loudness = measure_loudness(path)

    proc = ffmpeg.run(
        "ffmpeg",
        [
            "-hide_banner",
            "-nostdin",
            "-i",
            str(path),
            "-af",
            "astats=measure_perchannel=none:measure_overall="
            "Peak_level+Flat_factor+Peak_count+RMS_level,"
            "silencedetect=n=-40dB:d=0.5",
            "-f",
            "null",
            "-",
        ],
    )
    log = proc.stderr

    def stat(name: str) -> float | None:
        found = re.search(rf"{name}: (-?[\d.]+|-inf)", log)
        if not found or found.group(1) == "-inf":
            return None
        return float(found.group(1))

    silence_starts = [float(t) for t in re.findall(r"silence_start: (-?[\d.]+)", log)]
    silence_durations = [
        float(t) for t in re.findall(r"silence_duration: ([\d.]+)", log)
    ]

    # Crude bandwidth signal: energy remaining above 8 kHz relative to full band.
    hf = ffmpeg.run(
        "ffmpeg",
        [
            "-hide_banner",
            "-nostdin",
            "-i",
            str(path),
            "-af",
            "highpass=f=8000,volumedetect",
            "-f",
            "null",
            "-",
        ],
    )
    hf_mean = re.search(r"mean_volume: (-?[\d.]+)", hf.stderr)
    full = ffmpeg.run(
        "ffmpeg",
        [
            "-hide_banner",
            "-nostdin",
            "-i",
            str(path),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ],
    )
    full_mean = re.search(r"mean_volume: (-?[\d.]+)", full.stderr)
    hf_drop = (
        round(float(full_mean.group(1)) - float(hf_mean.group(1)), 2)
        if hf_mean and full_mean
        else None
    )

    flat_factor = stat("Flat factor")
    peak_level = stat("Peak level dB")
    return {
        "loudness": {k: v for k, v in loudness.items() if k != "raw"},
        "peak_level_dbfs": peak_level,
        "rms_level_dbfs": stat("RMS level dB"),
        "clipping": {
            "flat_factor": flat_factor,
            "peak_count": stat("Peak count"),
            "likely_clipped": bool(
                flat_factor
                and flat_factor > 0.1
                and peak_level is not None
                and peak_level > -0.2
            ),
        },
        "silence": {
            "spans": [
                {"start": s, "duration": d}
                for s, d in zip(silence_starts, silence_durations)
            ],
            "count": len(silence_starts),
        },
        "bandwidth": {
            "high_frequency_dropoff_db": hf_drop,
            "note": "full-band mean volume minus >8kHz mean volume; larger = duller",
        },
    }
