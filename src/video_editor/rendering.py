"""Compile validated edit plans into deterministic FFmpeg renders.

Each render writes the output plus a `<output>.manifest.json` recording the
plan, cut boundaries with their source mapping, and provenance — enough for
`cuts list` / `cut inspect` to enumerate and review every boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import tempfile

from video_editor import SCHEMA_VERSION, ffmpeg, plans, profiles
from video_editor.audio.analysis import measure_loudness
from video_editor.provenance import sha256_file, utc_now

PREVIEW_HEIGHT = 360
PREVIEW_FPS = 30


def _clip_segments(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Output-timeline segments: clip + output_start/output_end."""
    segments = []
    cursor = 0.0
    for index, clip in enumerate(plan["timeline"]):
        duration = clip["out"] - clip["in"]
        segments.append(
            {
                "index": index,
                "source": clip["source"],
                "video_source": clip.get("video_source"),
                "in": clip["in"],
                "out": clip["out"],
                "reason": clip["reason"],
                "crop": clip.get("crop"),
                "gain_db": clip.get("gain_db"),
                "output_start": round(cursor, 6),
                "output_end": round(cursor + duration, 6),
            }
        )
        cursor += duration
    return segments


def _concat_args(
    plan: dict[str, Any],
    sources: dict[str, str],
    video_filter: str,
    fps: float,
) -> list[str]:
    """Input args + filter_complex for the per-clip trim/normalize/concat graph."""
    args: list[str] = []
    filters: list[str] = []
    concat_inputs: list[str] = []
    input_index = 0
    for i, clip in enumerate(plan["timeline"]):
        span = clip["out"] - clip["in"]
        args += [
            "-ss",
            f"{clip['in']:.6f}",
            "-t",
            f"{span:.6f}",
            "-i",
            str(sources[clip["source"]]),
        ]
        audio_index = input_index
        input_index += 1
        video_id = clip.get("video_source")
        if video_id and video_id != clip["source"]:
            args += [
                "-ss",
                f"{clip['in']:.6f}",
                "-t",
                f"{span:.6f}",
                "-i",
                str(sources[video_id]),
            ]
            video_index = input_index
            input_index += 1
        else:
            video_index = audio_index
        crop = clip.get("crop")
        crop_filter = (
            f"crop={crop['width']}:{crop['height']}:{crop['x']}:{crop['y']},"
            if crop
            else ""
        )
        gain = clip.get("gain_db")
        gain_filter = f",volume={gain}dB" if gain else ""
        filters.append(
            f"[{video_index}:v]{crop_filter}{video_filter},setsar=1,fps={fps},"
            f"format=yuv420p[v{i}]"
        )
        filters.append(
            f"[{audio_index}:a]aresample=48000,"
            f"aformat=channel_layouts=stereo{gain_filter}[a{i}]"
        )
        concat_inputs.append(f"[v{i}][a{i}]")
    n = len(plan["timeline"])
    filter_complex = (
        ";".join(filters)
        + ";"
        + "".join(concat_inputs)
        + f"concat=n={n}:v=1:a=1[outv][outa]"
    )
    return [
        *args,
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "[outa]",
    ]


def _write_manifest(
    kind: str,
    plan: dict[str, Any],
    summary: dict[str, Any],
    sources: dict[str, str],
    output: Path,
    tool_commands: list[list[str]],
    profile_info: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "created_at": utc_now(),
        "plan": plan,
        "summary": summary,
        "segments": _clip_segments(plan),
        "sources": [
            {"id": sid, "path": str(path), "sha256": sha256_file(Path(path))}
            for sid, path in sources.items()
        ],
        "tools": {name: ffmpeg.version(name) for name in ("ffmpeg", "ffprobe")},
        "tool_commands": tool_commands,
        "output": {"path": str(output), "sha256": sha256_file(output)},
        "profile": profile_info,
    }
    manifest_path = output.with_name(output.name + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path, manifest


def render_master(
    plan: dict[str, Any],
    output: Path,
    profile_document: dict[str, Any],
    profile_name: str,
) -> tuple[Path, dict[str, Any]]:
    """Render a validated plan with a named external profile (canvas, codecs,
    music/ducking, loudness), via a lossless-audio intermediate."""
    summary = plans.validate(plan)
    profile = profiles.named_profile(profile_document, profile_name)
    sources = {record["id"]: record["path"] for record in plan["sources"]}
    output.parent.mkdir(parents=True, exist_ok=True)

    canvas = profile["canvas"]
    width, height = canvas["width"], canvas["height"]
    fps = canvas.get("frame_rate") or 30
    vcodec = profile.get("video_codec") or {}
    acodec = profile.get("audio_codec") or {}
    loudness_target = profile.get("loudness") or {}
    commands: list[list[str]] = []

    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    )
    with tempfile.TemporaryDirectory(prefix="video-edit-cli-master-") as tmp:
        intermediate = Path(tmp) / "intermediate.mov"
        args = _concat_args(plan, sources, video_filter, fps) + [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "14",
            "-c:a",
            "pcm_s24le",
            str(intermediate),
        ]
        ffmpeg.run_ffmpeg(args)
        commands.append(["ffmpeg", *args])

        mixed = Path(tmp) / "mixed.wav"
        music = profile_document.get("music")
        duration = summary["output_duration"]
        if music:
            ducking = music.get("ducking") or {}
            threshold = ducking.get("threshold", 0.02)
            ratio = ducking.get("ratio", 8)
            gain = music.get("gain_db", -18)
            mix_args = [
                "-i",
                str(intermediate),
                "-stream_loop",
                "-1",
                "-i",
                str(music["path"]),
                "-filter_complex",
                (
                    f"[1:a]atrim=0:{duration:.6f},aresample=48000,"
                    f"aformat=channel_layouts=stereo,volume={gain}dB[m];"
                    f"[0:a]asplit=2[key][dry];"
                    f"[m][key]sidechaincompress=threshold={threshold}:ratio={ratio}:"
                    f"attack=5:release=250[duck];"
                    f"[dry][duck]amix=inputs=2:duration=first:normalize=0[aout]"
                ),
                "-map",
                "[aout]",
                "-c:a",
                "pcm_s24le",
                str(mixed),
            ]
        else:
            mix_args = ["-i", str(intermediate), "-vn", "-c:a", "pcm_s24le", str(mixed)]
        ffmpeg.run_ffmpeg(mix_args)
        commands.append(["ffmpeg", *mix_args])

        target_i = loudness_target.get("integrated_lufs", -16.0)
        target_tp = loudness_target.get("true_peak_dbtp", -1.5)
        target_lra = loudness_target.get("lra", 11.0)
        measured = measure_loudness(mixed, target_i, target_tp, target_lra)["raw"]
        loudnorm = (
            f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
            f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
            f"measured_LRA={measured['input_lra']}:"
            f"measured_thresh={measured['input_thresh']}:"
            f"offset={measured['target_offset']}:linear=true"
        )
        final_args = [
            "-i",
            str(intermediate),
            "-i",
            str(mixed),
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-af",
            loudnorm,
            "-c:v",
            vcodec.get("name", "libx264"),
            "-preset",
            str(vcodec.get("preset", "medium")),
            "-crf",
            str(vcodec.get("crf", 20)),
            "-c:a",
            acodec.get("name", "aac"),
            "-b:a",
            acodec.get("bitrate", "192k"),
            "-ar",
            "48000",
            str(output),
        ]
        ffmpeg.run_ffmpeg(final_args)
        commands.append(["ffmpeg", *final_args])

    return _write_manifest(
        "render-master",
        plan,
        summary,
        sources,
        output,
        commands,
        {
            "name": profile_name,
            "canvas": canvas,
            "loudness": loudness_target,
            "music": bool(profile_document.get("music")),
        },
    )


def render_preview(
    plan: dict[str, Any], output: Path, height: int = PREVIEW_HEIGHT
) -> tuple[Path, dict[str, Any]]:
    """Render a low-cost rough cut of a validated plan; returns (manifest_path, manifest)."""
    summary = plans.validate(plan)
    sources = {record["id"]: record["path"] for record in plan["sources"]}
    output.parent.mkdir(parents=True, exist_ok=True)

    canvas = plan.get("output_canvas")
    if canvas:
        # A plan-declared canvas (e.g. a vertical short) wins over the preview
        # height so the preview shows the real framing.
        video_filter = (
            f"scale={canvas['width']}:{canvas['height']}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={canvas['width']}:{canvas['height']}:(ow-iw)/2:(oh-ih)/2"
        )
        fps = canvas.get("frame_rate") or PREVIEW_FPS
    else:
        # Concat requires identical frame sizes, so normalize every clip to one
        # 16:9 letterboxed preview canvas even when sources differ.
        width = int(height * 16 / 9) // 2 * 2
        video_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        )
        fps = PREVIEW_FPS
    args = _concat_args(plan, sources, video_filter, fps) + [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "26",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(output),
    ]
    ffmpeg.run_ffmpeg(args)
    return _write_manifest(
        "render-preview",
        plan,
        summary,
        sources,
        output,
        [["ffmpeg", *args]],
        {"height": height, "fps": fps, "canvas": canvas, "codec": "h264/aac"},
    )
