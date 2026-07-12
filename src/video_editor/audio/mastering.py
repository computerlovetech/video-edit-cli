"""Deterministic mastering: filtering, dynamics, and two-pass loudness normalization.

This is the mastering-only baseline: no neural processing, fully reproducible
from explicit parameters. Output is lossless WAV.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from video_editor import ffmpeg
from video_editor.audio.analysis import measure_loudness
from video_editor.errors import InvalidInputError


def master(
    source: Path,
    output: Path,
    target_i: float = -16.0,
    target_tp: float = -1.5,
    target_lra: float = 11.0,
    highpass_hz: int = 70,
    compress: bool = True,
) -> tuple[list[str], dict[str, Any]]:
    """Two-pass loudnorm mastering chain; returns (ffmpeg args, result metrics)."""
    if output.suffix.lower() != ".wav":
        raise InvalidInputError("audio master output must be a .wav path (lossless)")
    measured = measure_loudness(source, target_i, target_tp, target_lra)["raw"]
    output.parent.mkdir(parents=True, exist_ok=True)

    chain = [f"highpass=f={highpass_hz}"]
    if compress:
        chain.append(
            "acompressor=threshold=-18dB:ratio=2:attack=15:release=200:makeup=2"
        )
    chain.append(
        "loudnorm=I={i}:TP={tp}:LRA={lra}:measured_I={mi}:measured_TP={mtp}:"
        "measured_LRA={mlra}:measured_thresh={mth}:offset={off}:linear=true".format(
            i=target_i,
            tp=target_tp,
            lra=target_lra,
            mi=measured["input_i"],
            mtp=measured["input_tp"],
            mlra=measured["input_lra"],
            mth=measured["input_thresh"],
            off=measured["target_offset"],
        )
    )
    args = [
        "-i",
        str(source),
        "-af",
        ",".join(chain),
        "-ar",
        "48000",
        "-c:a",
        "pcm_s24le",
        str(output),
    ]
    ffmpeg.run_ffmpeg(args)

    result_loudness = measure_loudness(output, target_i, target_tp, target_lra)
    metrics = {
        "target": {
            "integrated_lufs": target_i,
            "true_peak_dbtp": target_tp,
            "lra": target_lra,
        },
        "input": {
            "integrated_lufs": float(measured["input_i"]),
            "true_peak_dbtp": float(measured["input_tp"]),
        },
        "output": {k: v for k, v in result_loudness.items() if k != "raw"},
        "chain": chain,
    }
    return args, metrics
