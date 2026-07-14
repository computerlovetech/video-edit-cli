"""video-edit-cli CLI: headless atomic subcommands with a structured JSON contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable

import json

from video_editor import (
    __version__,
    assets,
    diagnostics,
    inspection,
    media,
    plans,
    profiles,
    provenance,
    reframe,
    rendering,
    result,
    review,
    skills,
    subtitles,
    sync,
    workspace,
)
from video_editor.audio import analysis as audio_analysis
from video_editor.audio import comparison as audio_comparison
from video_editor.audio import denoise as audio_denoise
from video_editor.audio import mastering as audio_mastering
from video_editor.audio import replacement as audio_replacement
from video_editor.errors import VideoEditorError
from video_editor.transcription import base as transcription_base
from video_editor.transcription import views as transcript_views

Handler = Callable[[argparse.Namespace], tuple[dict[str, Any], list[dict[str, str]]]]


def _register_if_workspace(
    args: argparse.Namespace, output: Path, kind: str, command: str
) -> None:
    root = getattr(args, "workspace", None)
    if root is not None:
        workspace.register_artifact(Path(root), output, kind, command)


def _derived_artifact(
    args: argparse.Namespace,
    command: str,
    source: Path,
    output: Path,
    kind: str,
    parameters: dict[str, Any],
    tool_args: list[str],
) -> list[dict[str, str]]:
    sidecar = provenance.write_sidecar(
        output, command, [source], parameters, [["ffmpeg", *tool_args]]
    )
    _register_if_workspace(args, output, kind, command)
    return [result.artifact(output, kind), result.artifact(sidecar, "provenance")]


def cmd_workspace_init(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest = workspace.init(
        Path(args.root),
        [Path(p) for p in args.source],
        list(args.role) if args.role else None,
    )
    root = Path(args.root).resolve()
    return (
        {
            "workspace_id": manifest["workspace_id"],
            "root": str(root),
            "sources": manifest["sources"],
        },
        [result.artifact(root / "workspace.json", "workspace-manifest")],
    )


def cmd_probe(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, str]]]:
    return media.probe(Path(args.input)), []


def cmd_audio_extract(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    tool_args = inspection.extract_audio(source, output)
    artifacts = _derived_artifact(
        args, "audio extract", source, output, "audio", {}, tool_args
    )
    return {"output": str(output)}, artifacts


def cmd_proxy_create(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    tool_args = inspection.create_proxy(source, output, args.height)
    artifacts = _derived_artifact(
        args,
        "proxy create",
        source,
        output,
        "proxy",
        {"height": args.height},
        tool_args,
    )
    return {"output": str(output), "height": args.height}, artifacts


def cmd_frame_extract(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    tool_args = inspection.extract_frame(source, args.time, output)
    artifacts = _derived_artifact(
        args, "frame extract", source, output, "frame", {"time": args.time}, tool_args
    )
    return {"output": str(output), "time": args.time}, artifacts


def cmd_filmstrip_create(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    params = {
        "start": args.start,
        "end": args.end,
        "columns": args.columns,
        "frames": args.frames,
    }
    tool_args, tile_times = inspection.create_filmstrip(
        source, args.start, args.end, output, args.columns, args.frames
    )
    artifacts = _derived_artifact(
        args, "filmstrip create", source, output, "filmstrip", params, tool_args
    )
    return {"output": str(output), "tile_times": tile_times, **params}, artifacts


def cmd_waveform_create(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    params = {"start": args.start, "end": args.end}
    tool_args = inspection.create_waveform(source, args.start, args.end, output)
    artifacts = _derived_artifact(
        args, "waveform create", source, output, "waveform", params, tool_args
    )
    return {"output": str(output), **params}, artifacts


def cmd_preview_create(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    params = {"start": args.start, "end": args.end}
    tool_args = inspection.create_preview(source, args.start, args.end, output)
    artifacts = _derived_artifact(
        args, "preview create", source, output, "preview", params, tool_args
    )
    return {"output": str(output), **params}, artifacts


def cmd_transcript_create(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    backend = transcription_base.get_backend(
        args.backend, Path(args.fixture) if args.fixture else None
    )
    document = transcription_base.transcribe_to_document(
        backend, source, args.model, args.language, args.source_id
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2) + "\n")
    sidecar = provenance.write_sidecar(
        output,
        "transcript create",
        [source],
        {
            "backend": args.backend,
            "model": document["model"],
            "language": document["language"],
        },
    )
    _register_if_workspace(args, output, "transcript", "transcript create")
    return (
        {
            "output": str(output),
            "backend": document["backend"],
            "model": document["model"],
            "language": document["language"],
            "segment_count": len(document["segments"]),
            "word_count": sum(len(s["words"]) for s in document["segments"]),
        },
        [result.artifact(output, "transcript"), result.artifact(sidecar, "provenance")],
    )


def cmd_transcript_pack(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    transcript_path, output = Path(args.transcript), Path(args.output)
    document = transcript_views.load_transcript(transcript_path)
    packed = transcript_views.pack(document)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(packed)
    _register_if_workspace(args, output, "transcript-packed", "transcript pack")
    return (
        {"output": str(output), "line_count": packed.count("\n")},
        [result.artifact(output, "transcript-packed")],
    )


def cmd_transcript_search(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    document = transcript_views.load_transcript(Path(args.transcript))
    matches = transcript_views.search(document, args.query, args.max_results)
    return {"query": args.query, "match_count": len(matches), "matches": matches}, []


def cmd_plan_validate(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    plan = plans.load(Path(args.plan))
    summary = plans.validate(plan)
    return {"valid": True, **summary}, []


def cmd_render_preview(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    plan = plans.load(Path(args.plan))
    output = Path(args.output)
    manifest_path, manifest = rendering.render_preview(plan, output, args.height)
    _register_if_workspace(args, output, "render-preview", "render preview")
    return (
        {
            "output": str(output),
            "manifest": str(manifest_path),
            "plan_id": plan["plan_id"],
            "output_duration": manifest["summary"]["output_duration"],
            "clip_count": manifest["summary"]["clip_count"],
            "boundaries": manifest["summary"]["boundaries"],
        },
        [
            result.artifact(output, "render-preview"),
            result.artifact(manifest_path, "render-manifest"),
        ],
    )


def cmd_cuts_list(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest = review.load_manifest(Path(args.manifest))
    cuts = review.list_cuts(manifest)
    return {"cut_count": len(cuts), "cuts": cuts}, []


def cmd_cut_inspect(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest = review.load_manifest(Path(args.manifest))
    cut_indexes = range(len(review.list_cuts(manifest))) if args.all else [args.cut]
    reports = [
        review.inspect_cut(
            manifest,
            cut_index,
            Path(args.output_dir),
            args.window,
            Path(args.transcript) if args.transcript else None,
        )
        for cut_index in cut_indexes
    ]
    artifacts: list[dict[str, str]] = []
    for report in reports:
        artifacts.extend(
            result.artifact(path, kind) for kind, path in report["artifacts"].items()
        )
        artifacts.append(result.artifact(report["report_path"], "cut-report"))
    if args.all:
        return {
            "cut_count": len(reports),
            "passed": all(report["passed"] for report in reports),
            "reports": reports,
        }, artifacts
    return reports[0], artifacts


def cmd_audio_analyze(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    return audio_analysis.analyze(Path(args.input)), []


def cmd_audio_master(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    tool_args, metrics = audio_mastering.master(
        source,
        output,
        target_i=args.target_lufs,
        target_tp=args.true_peak,
        target_lra=args.lra,
        highpass_hz=args.highpass,
        compress=not args.no_compressor,
    )
    params = {
        "target_lufs": args.target_lufs,
        "true_peak": args.true_peak,
        "lra": args.lra,
        "highpass": args.highpass,
        "compressor": not args.no_compressor,
    }
    artifacts = _derived_artifact(
        args, "audio master", source, output, "audio-mastered", params, tool_args
    )
    return {"output": str(output), **metrics}, artifacts


def cmd_audio_denoise(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    details = audio_denoise.denoise(source, output, args.backend)
    sidecar = provenance.write_sidecar(output, "audio denoise", [source], details)
    _register_if_workspace(args, output, "audio-denoised", "audio denoise")
    return (
        {"output": str(output), **details},
        [
            result.artifact(output, "audio-denoised"),
            result.artifact(sidecar, "provenance"),
        ],
    )


def cmd_audio_compare(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    report = audio_comparison.compare(
        [Path(p) for p in args.input],
        Path(args.output_dir),
        match_lufs=args.match_lufs,
        sample_start=args.start,
        sample_duration=args.duration,
    )
    artifacts = [
        result.artifact(entry["ab_sample"], "ab-sample")
        for entry in report["candidates"]
    ]
    artifacts.append(result.artifact(report["report_path"], "compare-report"))
    return report, artifacts


def cmd_audio_replace(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    video, audio, output = Path(args.video), Path(args.audio), Path(args.output)
    tool_args, details = audio_replacement.replace(
        video,
        audio,
        output,
        audio_codec=args.audio_codec,
        audio_bitrate=args.audio_bitrate,
        duration_tolerance=args.duration_tolerance,
    )
    sidecar = provenance.write_sidecar(
        output, "audio replace", [video, audio], details, [["ffmpeg", *tool_args]]
    )
    _register_if_workspace(args, output, "video-audio-replaced", "audio replace")
    return (
        {"output": str(output), **details},
        [
            result.artifact(output, "video-audio-replaced"),
            result.artifact(sidecar, "provenance"),
        ],
    )


def cmd_render_master(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    plan = plans.load(Path(args.plan))
    profile_document = profiles.load(Path(args.profile))
    output = Path(args.output)
    manifest_path, manifest = rendering.render_master(
        plan, output, profile_document, args.profile_name
    )
    _register_if_workspace(args, output, "render-master", "render master")
    return (
        {
            "output": str(output),
            "manifest": str(manifest_path),
            "plan_id": plan["plan_id"],
            "profile": args.profile_name,
            "output_duration": manifest["summary"]["output_duration"],
            "boundaries": manifest["summary"]["boundaries"],
        },
        [
            result.artifact(output, "render-master"),
            result.artifact(manifest_path, "render-manifest"),
        ],
    )


def cmd_subtitles_create(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest = review.load_manifest(Path(args.manifest))
    plan_sources = {s["id"]: s["path"] for s in manifest["sources"]}
    transcripts: dict[str, Any] = {}
    for transcript_path in args.transcript:
        document = transcript_views.load_transcript(Path(transcript_path))
        source_id = document["source"].get("source_id")
        if source_id is None:
            matches = [
                sid
                for sid, path in plan_sources.items()
                if Path(path).resolve() == Path(document["source"]["path"]).resolve()
            ]
            if len(matches) != 1:
                raise VideoEditorError(
                    "invalid-input",
                    f"cannot map transcript {transcript_path} to a plan source; "
                    "set source_id when creating the transcript",
                    exit_code=2,
                )
            source_id = matches[0]
        transcripts[source_id] = document
    cues = subtitles.map_cues(transcripts, manifest["segments"])
    cues = subtitles.reflow_cues(
        cues,
        max_words=args.max_words,
        max_chars=args.max_chars,
        max_duration=args.max_duration,
    )
    if not cues:
        raise VideoEditorError(
            "invalid-input",
            "no transcript words fall inside the kept ranges",
            exit_code=2,
        )
    srt_path, vtt_path = Path(args.output_srt), Path(args.output_vtt)
    subtitles.write_srt(cues, srt_path)
    subtitles.write_vtt(cues, vtt_path)
    _register_if_workspace(args, srt_path, "subtitles-srt", "subtitles create")
    return (
        {
            "cue_count": len(cues),
            "first_cue_start": cues[0]["start"],
            "last_cue_end": cues[-1]["end"],
            "srt": str(srt_path),
            "vtt": str(vtt_path),
        },
        [
            result.artifact(srt_path, "subtitles-srt"),
            result.artifact(vtt_path, "subtitles-vtt"),
        ],
    )


def cmd_subtitles_render(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    video, subtitle_file, output = (
        Path(args.input),
        Path(args.subtitles),
        Path(args.output),
    )
    style_fields = {
        "FontName": args.font,
        "FontSize": args.font_size,
        "PrimaryColour": args.primary_color,
        "OutlineColour": args.outline_color,
        "Outline": args.outline_width,
        "Shadow": args.shadow,
        "Alignment": args.alignment,
        "MarginV": args.margin_v,
    }
    force_style = (
        ",".join(
            f"{key}={value}" for key, value in style_fields.items() if value is not None
        )
        or None
    )
    tool_args = subtitles.render_subtitles(
        video, subtitle_file, output, args.mode, force_style=force_style
    )
    sidecar = provenance.write_sidecar(
        output,
        "subtitles render",
        [video, subtitle_file],
        {"mode": args.mode, "force_style": force_style},
        [["ffmpeg", *tool_args]],
    )
    _register_if_workspace(args, output, "video-subtitled", "subtitles render")
    return (
        {"output": str(output), "mode": args.mode, "force_style": force_style},
        [
            result.artifact(output, "video-subtitled"),
            result.artifact(sidecar, "provenance"),
        ],
    )


def cmd_asset_inspect(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    return assets.inspect_asset(Path(args.input)), []


def cmd_output_validate(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    profile = None
    if args.profile:
        document = profiles.load(Path(args.profile))
        profile = profiles.named_profile(document, args.profile_name)
    report = assets.validate_output(
        Path(args.input),
        profile=profile,
        expect_duration=args.expect_duration,
        duration_tolerance=args.duration_tolerance,
        loudness_tolerance=args.loudness_tolerance,
        expect_subtitles=args.expect_subtitles,
        subtitle_file=Path(args.subtitles) if args.subtitles else None,
        expect_canvas=(
            (
                reframe.parse_canvas(args.expect_canvas)["width"],
                reframe.parse_canvas(args.expect_canvas)["height"],
            )
            if args.expect_canvas
            else None
        ),
    )
    return report, []


def cmd_doctor(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, str]]]:
    return diagnostics.inspect(args.workflow), []


def cmd_sync_analyze(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    return sync.analyze(Path(args.reference), Path(args.other), args.max_offset), []


def cmd_sync_apply(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    data = sync.apply(source, args.offset, output)
    kind = "sync-mapping" if data["mode"] == "metadata" else "aligned-media"
    artifacts = [result.artifact(output, kind)]
    if data["mode"] == "trim":
        sidecar = provenance.write_sidecar(
            output, "sync apply", [source], {"offset": args.offset}
        )
        artifacts.append(result.artifact(sidecar, "provenance"))
    _register_if_workspace(args, output, kind, "sync apply")
    return data, artifacts


def cmd_reframe_preview(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    source, output = Path(args.input), Path(args.output)
    crop = reframe.parse_crop(args.crop)
    canvas = reframe.parse_canvas(args.canvas)
    params = {"start": args.start, "end": args.end, "crop": crop, "canvas": canvas}
    tool_args = reframe.preview_reframe(
        source, args.start, args.end, crop, canvas, output
    )
    artifacts = _derived_artifact(
        args, "reframe preview", source, output, "reframe-preview", params, tool_args
    )
    return {"output": str(output), **params}, artifacts


def cmd_short_create_plan(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    output = Path(args.output)
    plan = reframe.derive_short_plan(
        Path(args.input),
        args.source_id,
        args.start,
        args.end,
        reframe.parse_canvas(args.canvas),
        args.reason,
        crop=reframe.parse_crop(args.crop) if args.crop else None,
        parent_plan=args.parent_plan,
        created_by=args.created_by,
    )
    plans.validate(plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2) + "\n")
    _register_if_workspace(args, output, "edit-plan", "short create-plan")
    return (
        {
            "output": str(output),
            "plan_id": plan["plan_id"],
            "canvas": plan["output_canvas"],
            "range": {"start": args.start, "end": args.end},
        },
        [result.artifact(output, "edit-plan")],
    )


def _add_io(parser: argparse.ArgumentParser, needs_output: bool = True) -> None:
    parser.add_argument("--input", required=True, help="path to the source media file")
    if needs_output:
        parser.add_argument(
            "--output", required=True, help="path for the new derived file"
        )
    parser.add_argument(
        "--workspace",
        help="optional workspace root; records the derived artifact in workspace.json",
    )


def _add_range(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--start", type=float, required=True, help="range start in seconds"
    )
    parser.add_argument("--end", type=float, required=True, help="range end in seconds")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video-edit-cli",
        description=(
            "Atomic, non-interactive video-editing primitives for agents. "
            "Every command prints one JSON result object on stdout."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    top = parser.add_subparsers(dest="group", required=True)

    doctor = top.add_parser(
        "doctor", help="check local dependencies for an editing workflow"
    )
    doctor.add_argument("--workflow", choices=diagnostics.WORKFLOWS, default="base")
    doctor.set_defaults(handler=cmd_doctor, command_name="doctor")

    ws = top.add_parser("workspace", help="manage an editing workspace").add_subparsers(
        dest="action", required=True
    )
    ws_init = ws.add_parser(
        "init", help="create a workspace and register immutable sources"
    )
    ws_init.add_argument(
        "--root", required=True, help="directory to create the workspace in"
    )
    ws_init.add_argument(
        "--source",
        action="append",
        required=True,
        help="source media path (repeatable)",
    )
    ws_init.add_argument(
        "--role", action="append", help="role label per source, in --source order"
    )
    ws_init.set_defaults(handler=cmd_workspace_init, command_name="workspace init")

    probe = top.add_parser("probe", help="inspect streams and container metadata")
    probe.add_argument("--input", required=True, help="path to the media file")
    probe.set_defaults(handler=cmd_probe, command_name="probe")

    audio = top.add_parser("audio", help="audio operations").add_subparsers(
        dest="action", required=True
    )
    extract = audio.add_parser("extract", help="extract lossless canonical WAV audio")
    _add_io(extract)
    extract.set_defaults(handler=cmd_audio_extract, command_name="audio extract")

    analyze = audio.add_parser(
        "analyze", help="measure loudness, peaks, clipping, silence, bandwidth"
    )
    analyze.add_argument(
        "--input", required=True, help="audio or video file to measure"
    )
    analyze.set_defaults(handler=cmd_audio_analyze, command_name="audio analyze")

    master = audio.add_parser(
        "master", help="deterministic mastering with two-pass loudness normalization"
    )
    _add_io(master)
    master.add_argument(
        "--target-lufs", type=float, default=-16.0, help="integrated target"
    )
    master.add_argument(
        "--true-peak", type=float, default=-1.5, help="true-peak ceiling dBTP"
    )
    master.add_argument("--lra", type=float, default=11.0, help="loudness range target")
    master.add_argument("--highpass", type=int, default=70, help="rumble highpass Hz")
    master.add_argument(
        "--no-compressor", action="store_true", help="skip the gentle speech compressor"
    )
    master.set_defaults(handler=cmd_audio_master, command_name="audio master")

    denoise = audio.add_parser(
        "denoise", help="run one explicitly selected local denoising backend"
    )
    _add_io(denoise)
    denoise.add_argument(
        "--backend",
        required=True,
        choices=["deepfilternet"],
        help="denoising backend (explicit; never applied implicitly)",
    )
    denoise.set_defaults(handler=cmd_audio_denoise, command_name="audio denoise")

    compare = audio.add_parser(
        "compare", help="loudness-matched A/B artifacts and metrics for candidates"
    )
    compare.add_argument(
        "--input",
        action="append",
        required=True,
        help="candidate audio (repeat 2+ times)",
    )
    compare.add_argument(
        "--output-dir", required=True, help="directory for samples + report"
    )
    compare.add_argument("--match-lufs", type=float, default=-20.0)
    compare.add_argument(
        "--start", type=float, default=0.0, help="excerpt start seconds"
    )
    compare.add_argument("--duration", type=float, default=12.0, help="excerpt seconds")
    compare.set_defaults(handler=cmd_audio_compare, command_name="audio compare")

    replace = audio.add_parser(
        "replace", help="replace a video's audio stream while copying its video"
    )
    replace.add_argument(
        "--video", required=True, help="video whose video stream is kept"
    )
    replace.add_argument("--audio", required=True, help="replacement audio input")
    replace.add_argument("--output", required=True, help="new output video path")
    replace.add_argument("--audio-codec", default="aac", help="output audio codec")
    replace.add_argument("--audio-bitrate", default="192k", help="output audio bitrate")
    replace.add_argument(
        "--duration-tolerance",
        type=float,
        default=0.1,
        help="maximum allowed audio/video duration difference in seconds",
    )
    replace.add_argument(
        "--workspace", help="optional workspace root; records the derived artifact"
    )
    replace.set_defaults(handler=cmd_audio_replace, command_name="audio replace")

    proxy = top.add_parser("proxy", help="inspection proxies").add_subparsers(
        dest="action", required=True
    )
    proxy_create = proxy.add_parser("create", help="create a low-resolution proxy")
    _add_io(proxy_create)
    proxy_create.add_argument(
        "--height", type=int, default=360, help="proxy height in pixels"
    )
    proxy_create.set_defaults(handler=cmd_proxy_create, command_name="proxy create")

    frame = top.add_parser("frame", help="single frames").add_subparsers(
        dest="action", required=True
    )
    frame_extract = frame.add_parser(
        "extract", help="extract one frame at a source time"
    )
    _add_io(frame_extract)
    frame_extract.add_argument(
        "--time", type=float, required=True, help="source time in seconds"
    )
    frame_extract.set_defaults(handler=cmd_frame_extract, command_name="frame extract")

    filmstrip = top.add_parser("filmstrip", help="contact sheets").add_subparsers(
        dest="action", required=True
    )
    filmstrip_create = filmstrip.add_parser(
        "create", help="create a timestamped contact sheet for a range"
    )
    _add_io(filmstrip_create)
    _add_range(filmstrip_create)
    filmstrip_create.add_argument(
        "--columns", type=int, default=6, help="tiles per row"
    )
    filmstrip_create.add_argument(
        "--frames", type=int, default=12, help="frames to sample"
    )
    filmstrip_create.set_defaults(
        handler=cmd_filmstrip_create, command_name="filmstrip create"
    )

    waveform = top.add_parser("waveform", help="waveform images").add_subparsers(
        dest="action", required=True
    )
    waveform_create = waveform.add_parser(
        "create", help="render a waveform for a range"
    )
    _add_io(waveform_create)
    _add_range(waveform_create)
    waveform_create.set_defaults(
        handler=cmd_waveform_create, command_name="waveform create"
    )

    preview = top.add_parser("preview", help="range previews").add_subparsers(
        dest="action", required=True
    )
    preview_create = preview.add_parser(
        "create", help="render a short low-cost preview of a range"
    )
    _add_io(preview_create)
    _add_range(preview_create)
    preview_create.set_defaults(
        handler=cmd_preview_create, command_name="preview create"
    )

    transcript = top.add_parser(
        "transcript", help="word-level transcripts (JSON is authoritative)"
    ).add_subparsers(dest="action", required=True)
    t_create = transcript.add_parser(
        "create", help="transcribe with a local backend and write detailed JSON"
    )
    _add_io(t_create)
    t_create.add_argument(
        "--backend",
        default="mlx-whisper",
        choices=["mlx-whisper", "fixture"],
        help="transcription backend (fixture replays a prepared raw JSON, for tests/dev)",
    )
    t_create.add_argument("--model", help="backend model name")
    t_create.add_argument("--language", help="spoken language hint (e.g. en, da)")
    t_create.add_argument(
        "--fixture", help="raw transcription JSON for --backend fixture"
    )
    t_create.add_argument(
        "--source-id", help="workspace source id to record in the transcript"
    )
    t_create.set_defaults(
        handler=cmd_transcript_create, command_name="transcript create"
    )

    t_pack = transcript.add_parser(
        "pack", help="derive the compact agent-readable text view"
    )
    t_pack.add_argument(
        "--transcript", required=True, help="authoritative transcript JSON path"
    )
    t_pack.add_argument("--output", required=True, help="path for the packed text view")
    t_pack.add_argument(
        "--workspace",
        help="optional workspace root; records the artifact in workspace.json",
    )
    t_pack.set_defaults(handler=cmd_transcript_pack, command_name="transcript pack")

    t_search = transcript.add_parser(
        "search", help="find time-aligned matches for a spoken phrase"
    )
    t_search.add_argument(
        "--transcript", required=True, help="authoritative transcript JSON path"
    )
    t_search.add_argument("--query", required=True, help="phrase to search for")
    t_search.add_argument("--max-results", type=int, default=20)
    t_search.set_defaults(
        handler=cmd_transcript_search, command_name="transcript search"
    )

    plan = top.add_parser("plan", help="edit plans").add_subparsers(
        dest="action", required=True
    )
    p_validate = plan.add_parser(
        "validate", help="validate a plan's schema, references, and ranges"
    )
    p_validate.add_argument("--plan", required=True, help="edit-plan JSON path")
    p_validate.set_defaults(handler=cmd_plan_validate, command_name="plan validate")

    render = top.add_parser("render", help="render validated plans").add_subparsers(
        dest="action", required=True
    )
    r_preview = render.add_parser(
        "preview", help="render a plan with the low-cost preview profile"
    )
    r_preview.add_argument("--plan", required=True, help="edit-plan JSON path")
    r_preview.add_argument(
        "--output", required=True, help="path for the rendered preview"
    )
    r_preview.add_argument(
        "--height", type=int, default=360, help="preview height in pixels"
    )
    r_preview.add_argument(
        "--workspace",
        help="optional workspace root; records the artifact in workspace.json",
    )
    r_preview.set_defaults(handler=cmd_render_preview, command_name="render preview")

    r_master = render.add_parser(
        "master", help="render a plan using a named external project profile"
    )
    r_master.add_argument("--plan", required=True, help="edit-plan JSON path")
    r_master.add_argument("--profile", required=True, help="project profile YAML path")
    r_master.add_argument(
        "--profile-name", required=True, help="named render profile inside the YAML"
    )
    r_master.add_argument("--output", required=True, help="path for the master render")
    r_master.add_argument(
        "--workspace",
        help="optional workspace root; records the artifact in workspace.json",
    )
    r_master.set_defaults(handler=cmd_render_master, command_name="render master")

    cuts = top.add_parser("cuts", help="edit boundaries of a render").add_subparsers(
        dest="action", required=True
    )
    c_list = cuts.add_parser(
        "list", help="enumerate cut boundaries from a render manifest"
    )
    c_list.add_argument("--manifest", required=True, help="render manifest JSON path")
    c_list.set_defaults(handler=cmd_cuts_list, command_name="cuts list")

    cut = top.add_parser("cut", help="single-boundary review").add_subparsers(
        dest="action", required=True
    )
    c_inspect = cut.add_parser(
        "inspect",
        help="gather frames, waveform, preview, transcript context, and checks around one cut",
    )
    c_inspect.add_argument(
        "--manifest", required=True, help="render manifest JSON path"
    )
    cut_selection = c_inspect.add_mutually_exclusive_group(required=True)
    cut_selection.add_argument(
        "--cut", type=int, help="zero-based cut index from `cuts list`"
    )
    cut_selection.add_argument(
        "--all", action="store_true", help="inspect every cut in the manifest"
    )
    c_inspect.add_argument(
        "--output-dir", required=True, help="directory for the evidence bundle"
    )
    c_inspect.add_argument(
        "--window", type=float, default=2.0, help="seconds of context on each side"
    )
    c_inspect.add_argument(
        "--transcript", help="source transcript JSON for clipped-word checks"
    )
    c_inspect.set_defaults(handler=cmd_cut_inspect, command_name="cut inspect")

    subs = top.add_parser(
        "subtitles", help="subtitle derivation and rendering"
    ).add_subparsers(dest="action", required=True)
    s_create = subs.add_parser(
        "create", help="derive SRT+WebVTT from transcripts mapped through a render"
    )
    s_create.add_argument("--manifest", required=True, help="render manifest JSON path")
    s_create.add_argument(
        "--transcript",
        action="append",
        required=True,
        help="source transcript JSON (repeatable, one per source)",
    )
    s_create.add_argument("--output-srt", required=True)
    s_create.add_argument("--output-vtt", required=True)
    s_create.add_argument(
        "--max-words", type=int, help="maximum words per cue for short-form reflow"
    )
    s_create.add_argument(
        "--max-chars", type=int, help="maximum characters per cue for short-form reflow"
    )
    s_create.add_argument(
        "--max-duration", type=float, help="maximum approximate cue duration in seconds"
    )
    s_create.add_argument(
        "--workspace",
        help="optional workspace root; records the artifact in workspace.json",
    )
    s_create.set_defaults(handler=cmd_subtitles_create, command_name="subtitles create")

    s_render = subs.add_parser("render", help="mux or burn subtitles into a video")
    s_render.add_argument("--input", required=True, help="video path")
    s_render.add_argument("--subtitles", required=True, help="SRT, VTT, or ASS path")
    s_render.add_argument("--output", required=True)
    s_render.add_argument("--mode", default="mux", choices=["mux", "burn"])
    s_render.add_argument("--font", help="burn mode ASS font name")
    s_render.add_argument(
        "--font-size",
        type=float,
        help=(
            "burn mode ASS font size in libass script units, not output pixels "
            "(SRT/VTT commonly use a 288-unit-high script canvas)"
        ),
    )
    s_render.add_argument(
        "--primary-color", help="burn mode ASS color, e.g. &H00FFFFFF"
    )
    s_render.add_argument("--outline-color", help="burn mode ASS outline color")
    s_render.add_argument(
        "--outline-width", type=float, help="burn mode outline width in ASS units"
    )
    s_render.add_argument(
        "--shadow", type=float, help="burn mode shadow depth in ASS units"
    )
    s_render.add_argument(
        "--alignment", type=int, choices=range(1, 10), help="ASS alignment 1-9"
    )
    s_render.add_argument(
        "--margin-v",
        type=int,
        help=(
            "burn mode vertical margin in ASS script units, not output pixels "
            "(for SRT/VTT, values around 35-50 suit lower-third captions)"
        ),
    )
    s_render.add_argument(
        "--workspace",
        help="optional workspace root; records the artifact in workspace.json",
    )
    s_render.set_defaults(handler=cmd_subtitles_render, command_name="subtitles render")

    asset = top.add_parser("asset", help="external assets").add_subparsers(
        dest="action", required=True
    )
    a_inspect = asset.add_parser(
        "inspect",
        help="validate an intro, outro, music, font, image, or subtitle asset",
    )
    a_inspect.add_argument("--input", required=True, help="asset path")
    a_inspect.set_defaults(handler=cmd_asset_inspect, command_name="asset inspect")

    out = top.add_parser("output", help="final output checks").add_subparsers(
        dest="action", required=True
    )
    o_validate = out.add_parser(
        "validate",
        help="technical checks only: streams, canvas, duration, loudness, subtitles",
    )
    o_validate.add_argument("--input", required=True, help="rendered output path")
    o_validate.add_argument("--profile", help="project profile YAML path")
    o_validate.add_argument(
        "--profile-name", default="master", help="named profile to validate against"
    )
    o_validate.add_argument(
        "--expect-duration", type=float, help="expected duration seconds"
    )
    o_validate.add_argument(
        "--expect-canvas", help="expected WIDTHxHEIGHT without requiring a profile"
    )
    o_validate.add_argument("--duration-tolerance", type=float, default=0.5)
    o_validate.add_argument("--loudness-tolerance", type=float, default=1.5)
    o_validate.add_argument(
        "--expect-subtitles", action="store_true", help="require a subtitle stream"
    )
    o_validate.add_argument(
        "--subtitles", help="subtitle file to check against duration"
    )
    o_validate.set_defaults(handler=cmd_output_validate, command_name="output validate")

    sync_group = top.add_parser(
        "sync", help="multi-source synchronization"
    ).add_subparsers(dest="action", required=True)
    sy_analyze = sync_group.add_parser(
        "analyze", help="estimate the audio offset between two sources (evidence only)"
    )
    sy_analyze.add_argument("--reference", required=True, help="reference source path")
    sy_analyze.add_argument(
        "--other", required=True, help="source to align to the reference"
    )
    sy_analyze.add_argument(
        "--max-offset",
        type=float,
        default=30.0,
        help="largest offset to search, seconds",
    )
    sy_analyze.set_defaults(handler=cmd_sync_analyze, command_name="sync analyze")

    sy_apply = sync_group.add_parser(
        "apply",
        help="create an aligned derivative or .json mapping from an approved offset",
    )
    sy_apply.add_argument("--input", required=True, help="source to align")
    sy_apply.add_argument(
        "--offset", type=float, required=True, help="approved offset seconds"
    )
    sy_apply.add_argument(
        "--output",
        required=True,
        help="aligned media path, or .json for mapping metadata",
    )
    sy_apply.add_argument(
        "--workspace",
        help="optional workspace root; records the artifact in workspace.json",
    )
    sy_apply.set_defaults(handler=cmd_sync_apply, command_name="sync apply")

    reframe_group = top.add_parser(
        "reframe", help="crop/reframe previews"
    ).add_subparsers(dest="action", required=True)
    rf_preview = reframe_group.add_parser(
        "preview", help="preview an explicit crop scaled onto a canvas"
    )
    _add_io(rf_preview)
    _add_range(rf_preview)
    rf_preview.add_argument(
        "--crop", required=True, help="x:y:width:height in source pixels"
    )
    rf_preview.add_argument(
        "--canvas", required=True, help="output canvas WIDTHxHEIGHT"
    )
    rf_preview.set_defaults(handler=cmd_reframe_preview, command_name="reframe preview")

    short = top.add_parser("short", help="derived short-form plans").add_subparsers(
        dest="action", required=True
    )
    sh_plan = short.add_parser(
        "create-plan",
        help="derive an editable vertical plan from an explicit source range "
        "(you choose the range; this command never picks highlights)",
    )
    sh_plan.add_argument("--input", required=True, help="source media path")
    sh_plan.add_argument(
        "--source-id", default="src-1", help="source id used inside the plan"
    )
    sh_plan.add_argument("--start", type=float, required=True)
    sh_plan.add_argument("--end", type=float, required=True)
    sh_plan.add_argument(
        "--canvas", default="1080x1920", help="vertical canvas WIDTHxHEIGHT"
    )
    sh_plan.add_argument("--crop", help="optional x:y:width:height framing")
    sh_plan.add_argument(
        "--reason", required=True, help="editorial reason for choosing this range"
    )
    sh_plan.add_argument("--parent-plan", help="plan id this short derives from")
    sh_plan.add_argument("--created-by", help="authoring agent identifier")
    sh_plan.add_argument("--output", required=True, help="path for the new plan JSON")
    sh_plan.add_argument(
        "--workspace",
        help="optional workspace root; records the artifact in workspace.json",
    )
    sh_plan.set_defaults(
        handler=cmd_short_create_plan, command_name="short create-plan"
    )

    skills_group = top.add_parser(
        "skills", help="agent skills bundled with the CLI"
    ).add_subparsers(dest="action", required=True)
    sk_list = skills_group.add_parser("list", help="list the bundled skills")
    sk_list.set_defaults(handler=cmd_skills_list, command_name="skills list")
    sk_install = skills_group.add_parser(
        "install", help="copy the bundled skills into an agent skills directory"
    )
    sk_install.add_argument(
        "--target",
        default=".claude/skills",
        help="skills directory to install into (default: .claude/skills)",
    )
    sk_install.set_defaults(handler=cmd_skills_install, command_name="skills install")

    return parser


def cmd_skills_list(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    return {"skills": skills.list_skills()}, []


def cmd_skills_install(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    target = Path(args.target)
    target.mkdir(parents=True, exist_ok=True)
    installed = skills.install_skills(target)
    artifacts = [result.artifact(entry["path"], "skill") for entry in installed]
    return {"installed": installed, "target": str(target.resolve())}, artifacts


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command_name: str = args.command_name
    handler: Handler = args.handler
    try:
        data, artifacts = handler(args)
    except VideoEditorError as exc:
        result.emit_error(command_name, exc.code, exc.message)
        return exc.exit_code
    result.emit_success(command_name, data, artifacts)
    return 0


def main() -> None:
    sys.exit(run())
