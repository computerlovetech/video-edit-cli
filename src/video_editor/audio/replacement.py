"""Replace a video's audio stream without changing its video stream."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from video_editor import ffmpeg, media
from video_editor.errors import InvalidInputError


def replace(
    video: Path,
    audio: Path,
    output: Path,
    *,
    audio_codec: str = "aac",
    audio_bitrate: str = "192k",
    duration_tolerance: float = 0.1,
) -> tuple[list[str], dict[str, Any]]:
    """Mux one audio stream with copied video, requiring aligned durations."""
    for label, path in (("video", video), ("audio", audio)):
        if not path.is_file():
            raise InvalidInputError(f"{label} input not found: {path}")
    if output.resolve() in {video.resolve(), audio.resolve()}:
        raise InvalidInputError("audio replace output must be a new file")
    if duration_tolerance < 0:
        raise InvalidInputError("duration tolerance must be >= 0")

    video_info = media.probe(video)
    audio_info = media.probe(audio)
    if not any(stream["type"] == "video" for stream in video_info["streams"]):
        raise InvalidInputError(f"video input has no video stream: {video}")
    if not any(stream["type"] == "audio" for stream in audio_info["streams"]):
        raise InvalidInputError(f"audio input has no audio stream: {audio}")
    video_duration = media.duration_of(video)
    audio_duration = media.duration_of(audio)
    difference = abs(video_duration - audio_duration)
    if difference > duration_tolerance:
        raise InvalidInputError(
            f"audio/video duration difference {difference:.3f}s exceeds "
            f"tolerance {duration_tolerance:.3f}s"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "-i",
        str(video),
        "-i",
        str(audio),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        audio_codec,
        "-b:a",
        audio_bitrate,
        "-movflags",
        "+faststart",
        "-shortest",
        str(output),
    ]
    ffmpeg.run_ffmpeg(args)
    return args, {
        "audio_codec": audio_codec,
        "audio_bitrate": audio_bitrate,
        "duration_tolerance": duration_tolerance,
        "video_duration": video_duration,
        "audio_duration": audio_duration,
        "duration_difference": difference,
    }
