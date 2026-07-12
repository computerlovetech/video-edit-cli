"""Subtitles derived from transcripts mapped through an edited timeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from video_editor import ffmpeg
from video_editor.errors import InvalidInputError, ToolFailureError


def _fmt_srt(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_vtt(seconds: float) -> str:
    return _fmt_srt(seconds).replace(",", ".")


def map_cues(
    transcripts: dict[str, dict[str, Any]], segments: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Map transcript segments through kept ranges into output-time cues.

    `transcripts` is keyed by plan source id. Words outside kept ranges are
    dropped; partially kept transcript segments are clamped.
    """
    cues: list[dict[str, Any]] = []
    for segment in segments:
        transcript = transcripts.get(segment["source"])
        if transcript is None:
            continue
        kept_in, kept_out = segment["in"], segment["out"]
        offset = segment["output_start"] - kept_in
        for ts in transcript["segments"]:
            words = [
                w for w in ts["words"] if kept_in <= w["start"] and w["end"] <= kept_out
            ]
            if not words:
                continue
            cues.append(
                {
                    "start": round(words[0]["start"] + offset, 3),
                    "end": round(words[-1]["end"] + offset, 3),
                    "text": " ".join(w["text"] for w in words).strip(),
                }
            )
    cues.sort(key=lambda cue: cue["start"])
    return cues


def write_srt(cues: list[dict[str, Any]], output: Path) -> None:
    lines = []
    for i, cue in enumerate(cues, start=1):
        lines.append(str(i))
        lines.append(f"{_fmt_srt(cue['start'])} --> {_fmt_srt(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines))


def write_vtt(cues: list[dict[str, Any]], output: Path) -> None:
    lines = ["WEBVTT", ""]
    for cue in cues:
        lines.append(f"{_fmt_vtt(cue['start'])} --> {_fmt_vtt(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines))


def parse_srt_last_end(path: Path) -> float:
    """Last cue end time in seconds, for output validation."""
    import re

    text = path.read_text()
    times = re.findall(r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d)", text)
    if not times:
        raise InvalidInputError(f"no cue timestamps found in {path}")
    h, m, s, ms = times[-1]
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def render_subtitles(
    video: Path, subtitle_file: Path, output: Path, mode: str
) -> list[str]:
    """Attach subtitles to a video: mux a subtitle track, or burn if supported."""
    if not video.is_file():
        raise InvalidInputError(f"video not found: {video}")
    if not subtitle_file.is_file():
        raise InvalidInputError(f"subtitle file not found: {subtitle_file}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if mode == "mux":
        codec = (
            "mov_text" if output.suffix.lower() in (".mp4", ".m4v", ".mov") else "srt"
        )
        args = [
            "-i",
            str(video),
            "-i",
            str(subtitle_file),
            "-map",
            "0",
            "-map",
            "1:0",
            "-c",
            "copy",
            "-c:s",
            codec,
            str(output),
        ]
        ffmpeg.run_ffmpeg(args)
        return args
    if mode == "burn":
        filters = ffmpeg.run("ffmpeg", ["-hide_banner", "-filters"]).stdout
        if " subtitles " not in filters:
            raise ToolFailureError(
                "this ffmpeg build has no 'subtitles' filter (libass); "
                "use --mode mux or install a full ffmpeg build"
            )
        args = [
            "-i",
            str(video),
            "-vf",
            f"subtitles={subtitle_file}",
            "-c:a",
            "copy",
            str(output),
        ]
        ffmpeg.run_ffmpeg(args)
        return args
    raise InvalidInputError(f"unknown subtitles render mode '{mode}' (mux|burn)")
