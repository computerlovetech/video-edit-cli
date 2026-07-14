"""Subtitles derived from transcripts mapped through an edited timeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from video_editor import ffmpeg
from video_editor.errors import InvalidInputError, ToolFailureError


def reflow_cues(
    cues: list[dict[str, Any]],
    max_words: int | None = None,
    max_chars: int | None = None,
    max_duration: float | None = None,
) -> list[dict[str, Any]]:
    """Split long cues deterministically for short-form readability.

    Timing is apportioned by word count inside each authoritative mapped cue;
    the outer cue boundaries remain unchanged.
    """
    for name, value in (
        ("max_words", max_words),
        ("max_chars", max_chars),
        ("max_duration", max_duration),
    ):
        if value is not None and value <= 0:
            raise InvalidInputError(f"{name} must be greater than zero")
    if max_words is None and max_chars is None and max_duration is None:
        return cues
    output: list[dict[str, Any]] = []
    for cue in cues:
        words = cue["text"].split()
        if not words:
            continue
        groups: list[list[str]] = []
        current: list[str] = []
        for word in words:
            candidate = [*current, word]
            over_words = max_words is not None and len(candidate) > max_words
            over_chars = max_chars is not None and len(" ".join(candidate)) > max_chars
            if current and (over_words or over_chars):
                groups.append(current)
                current = [word]
            else:
                current = candidate
        if current:
            groups.append(current)

        if max_duration is not None:
            duration = cue["end"] - cue["start"]
            minimum_groups = max(1, int(duration / max_duration + 0.999999))
            while len(groups) < minimum_groups:
                index = max(range(len(groups)), key=lambda i: len(groups[i]))
                group = groups[index]
                if len(group) < 2:
                    break
                midpoint = (len(group) + 1) // 2
                groups[index : index + 1] = [group[:midpoint], group[midpoint:]]

        total_words = sum(len(group) for group in groups)
        cursor = cue["start"]
        span = cue["end"] - cue["start"]
        for index, group in enumerate(groups):
            end = (
                cue["end"]
                if index == len(groups) - 1
                else cursor + span * len(group) / total_words
            )
            output.append(
                {
                    "start": round(cursor, 3),
                    "end": round(end, 3),
                    "text": " ".join(group),
                }
            )
            cursor = end
    return output


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
    video: Path,
    subtitle_file: Path,
    output: Path,
    mode: str,
    force_style: str | None = None,
) -> list[str]:
    """Attach subtitles to a video: mux a subtitle track, or burn if supported."""
    if not video.is_file():
        raise InvalidInputError(f"video not found: {video}")
    if not subtitle_file.is_file():
        raise InvalidInputError(f"subtitle file not found: {subtitle_file}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if mode == "mux":
        if force_style:
            raise InvalidInputError("subtitle style options require --mode burn")
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
        subtitle_filter = f"subtitles={subtitle_file}"
        if force_style:
            escaped_style = force_style.replace("'", r"\'")
            subtitle_filter += f":force_style='{escaped_style}'"
        args = [
            "-i",
            str(video),
            "-vf",
            subtitle_filter,
            "-c:a",
            "copy",
            str(output),
        ]
        ffmpeg.run_ffmpeg(args)
        return args
    raise InvalidInputError(f"unknown subtitles render mode '{mode}' (mux|burn)")
