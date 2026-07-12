"""Derived inspection artifacts: audio, proxies, frames, filmstrips, waveforms, previews.

Every function writes new files, never touches inputs, and returns the ffmpeg
argument lists it ran so callers can record provenance.
"""

from __future__ import annotations

from pathlib import Path

from video_editor import ffmpeg, media
from video_editor.errors import InvalidInputError


def _prepare_output(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)


def extract_audio(source: Path, output: Path) -> list[str]:
    """Extract the first audio stream as lossless PCM WAV at its native sample rate."""
    info = media.probe(source)
    if not any(s["type"] == "audio" for s in info["streams"]):
        raise InvalidInputError(f"no audio stream in {source}")
    if output.suffix.lower() != ".wav":
        raise InvalidInputError("audio extract output must be a .wav path")
    _prepare_output(output)
    args = ["-i", str(source), "-vn", "-map", "0:a:0", "-c:a", "pcm_s24le", str(output)]
    ffmpeg.run_ffmpeg(args)
    return args


def create_proxy(source: Path, output: Path, height: int = 360) -> list[str]:
    """Create a low-cost H.264 proxy for inspection."""
    info = media.probe(source)
    if not any(s["type"] == "video" for s in info["streams"]):
        raise InvalidInputError(f"no video stream in {source}")
    _prepare_output(output)
    args = [
        "-i",
        str(source),
        "-vf",
        f"scale=-2:{height}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "28",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        str(output),
    ]
    ffmpeg.run_ffmpeg(args)
    return args


def extract_frame(source: Path, time: float, output: Path) -> list[str]:
    """Extract a single frame at the requested source time."""
    duration = media.duration_of(source)
    if time < 0 or time >= duration:
        raise InvalidInputError(
            f"time {time}s is outside media duration {duration:.3f}s"
        )
    _prepare_output(output)
    args = ["-ss", f"{time:.3f}", "-i", str(source), "-frames:v", "1", str(output)]
    ffmpeg.run_ffmpeg(args)
    return args


def create_filmstrip(
    source: Path,
    start: float,
    end: float,
    output: Path,
    columns: int = 6,
    frames: int = 12,
) -> tuple[list[str], list[float]]:
    """Create a contact sheet of `frames` evenly sampled frames from [start, end).

    Returns the ffmpeg args and the source times of the sampled tiles
    (row-major order), so callers can map tiles back to timestamps.
    """
    media.require_range(source, start, end)
    if frames < 1 or columns < 1:
        raise InvalidInputError("frames and columns must be >= 1")
    _prepare_output(output)
    span = end - start
    fps = frames / span
    rows = -((-frames) // columns)
    times = [round(start + i / fps, 3) for i in range(frames)]
    args = [
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{span:.3f}",
        "-i",
        str(source),
        "-vf",
        f"fps={fps:.6f},scale=320:-2,tile={columns}x{rows}",
        "-frames:v",
        "1",
        str(output),
    ]
    ffmpeg.run_ffmpeg(args)
    return args, times


def create_waveform(
    source: Path,
    start: float,
    end: float,
    output: Path,
    width: int = 1600,
    height: int = 300,
) -> list[str]:
    """Render a waveform image for the requested audio range."""
    media.require_range(source, start, end)
    _prepare_output(output)
    span = end - start
    args = [
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{span:.3f}",
        "-i",
        str(source),
        "-filter_complex",
        f"[0:a:0]showwavespic=s={width}x{height}:split_channels=1[w]",
        "-map",
        "[w]",
        "-frames:v",
        "1",
        str(output),
    ]
    ffmpeg.run_ffmpeg(args)
    return args


def create_preview(source: Path, start: float, end: float, output: Path) -> list[str]:
    """Render a short low-cost preview of a range without altering any plan."""
    media.require_range(source, start, end)
    _prepare_output(output)
    span = end - start
    info = media.probe(source)
    has_video = any(s["type"] == "video" for s in info["streams"])
    args = ["-ss", f"{start:.3f}", "-t", f"{span:.3f}", "-i", str(source)]
    if has_video:
        args += [
            "-vf",
            "scale=-2:360",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
        ]
    else:
        args += ["-c:a", "aac", "-b:a", "128k"]
    args.append(str(output))
    ffmpeg.run_ffmpeg(args)
    return args
