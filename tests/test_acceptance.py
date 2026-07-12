"""Scripted end-to-end acceptance test (GOAL section 8).

Walks the complete workflow on generated fixtures: workspace, inspection,
transcription (fixture backend), rough cut, cut review, audio mastering,
subtitles + packaged long-form output, synchronization + camera switching,
vertical derivation, and final validation of both outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from conftest import run_cli
from generate_fixtures import (
    KNOWN_OFFSET,
    generate_main,
    generate_music,
    generate_offset,
)
from video_editor import media
from video_editor.provenance import sha256_file


def run_ok(argv: list[str]) -> dict[str, Any]:
    code, envelope = run_cli(argv)
    assert code == 0, envelope.get("error")
    data: dict[str, Any] = envelope["data"]
    return data


def test_end_to_end_acceptance(tmp_path: Path) -> None:
    # 1. Generate fixture sources.
    cam_a = generate_main(tmp_path / "cam_a.mp4")
    cam_b_raw = generate_offset(tmp_path / "cam_b.mp4")
    music = generate_music(tmp_path / "music.wav")

    # 2. Create a workspace and register sources.
    ws = tmp_path / "ws"
    data = run_ok(
        [
            "workspace",
            "init",
            "--root",
            str(ws),
            "--source",
            str(cam_a),
            "--source",
            str(cam_b_raw),
            "--role",
            "camera-a",
            "--role",
            "camera-b",
        ]
    )
    hash_before = sha256_file(cam_a)
    assert data["sources"][0]["sha256"] == hash_before

    # 3. Probe and create inspection artifacts.
    probe = run_ok(["probe", "--input", str(cam_a)])
    assert {s["type"] for s in probe["streams"]} == {"video", "audio"}
    run_ok(
        [
            "audio",
            "extract",
            "--input",
            str(cam_a),
            "--output",
            str(ws / "analysis" / "audio.wav"),
            "--workspace",
            str(ws),
        ]
    )
    run_ok(
        [
            "filmstrip",
            "create",
            "--input",
            str(cam_a),
            "--start",
            "0",
            "--end",
            "8",
            "--output",
            str(ws / "analysis" / "strip.png"),
        ]
    )
    run_ok(
        [
            "waveform",
            "create",
            "--input",
            str(cam_a),
            "--start",
            "0",
            "--end",
            "8",
            "--output",
            str(ws / "analysis" / "wave.png"),
        ]
    )
    run_ok(
        [
            "preview",
            "create",
            "--input",
            str(cam_a),
            "--start",
            "1",
            "--end",
            "3",
            "--output",
            str(ws / "previews" / "range.mp4"),
        ]
    )

    # 4. Deterministic transcript fixture; pack and search it.
    raw = {
        "language": "en",
        "model": "fake",
        "segments": [
            {
                "start": 0.5,
                "end": 2.3,
                "text": "hello hello again",
                "words": [
                    {"text": "hello", "start": 0.6, "end": 1.1, "confidence": 0.9},
                    {"text": "hello", "start": 1.7, "end": 2.2, "confidence": 0.9},
                ],
            },
            {
                "start": 3.0,
                "end": 4.4,
                "text": "the main point",
                "words": [
                    {"text": "the", "start": 3.0, "end": 3.2, "confidence": 0.9},
                    {"text": "main", "start": 3.3, "end": 3.8, "confidence": 0.9},
                    {"text": "point", "start": 3.9, "end": 4.3, "confidence": 0.9},
                ],
            },
            {
                "start": 5.2,
                "end": 6.8,
                "text": "closing words",
                "words": [
                    {"text": "closing", "start": 5.3, "end": 5.9, "confidence": 0.9},
                    {"text": "words", "start": 6.0, "end": 6.7, "confidence": 0.9},
                ],
            },
        ],
    }
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(json.dumps(raw))
    transcript = ws / "analysis" / "transcript.json"
    run_ok(
        [
            "transcript",
            "create",
            "--input",
            str(cam_a),
            "--output",
            str(transcript),
            "--backend",
            "fixture",
            "--fixture",
            str(raw_path),
            "--source-id",
            "src-1",
        ]
    )
    run_ok(
        [
            "transcript",
            "pack",
            "--transcript",
            str(transcript),
            "--output",
            str(ws / "analysis" / "transcript.txt"),
        ]
    )
    search = run_ok(
        [
            "transcript",
            "search",
            "--transcript",
            str(transcript),
            "--query",
            "main point",
        ]
    )
    assert search["match_count"] == 1

    # 5. Validate and render a rough-cut plan (drops the false start at 0.6-1.1).
    plan = {
        "schema_version": "1",
        "plan_id": "acceptance-rough",
        "sources": [{"id": "src-1", "path": str(cam_a)}],
        "timeline": [
            {"source": "src-1", "in": 1.6, "out": 2.3, "reason": "keep second take"},
            {"source": "src-1", "in": 3.0, "out": 4.4, "reason": "keep main point"},
            {"source": "src-1", "in": 5.2, "out": 6.8, "reason": "keep closing"},
        ],
    }
    plan_path = ws / "plans" / "rough.json"
    plan_path.parent.mkdir(exist_ok=True)
    plan_path.write_text(json.dumps(plan))
    run_ok(["plan", "validate", "--plan", str(plan_path)])
    rough = ws / "previews" / "rough.mp4"
    render = run_ok(
        ["render", "preview", "--plan", str(plan_path), "--output", str(rough)]
    )
    manifest = ws / "previews" / "rough.mp4.manifest.json"

    # 6. Inspect every cut.
    cuts = run_ok(["cuts", "list", "--manifest", str(manifest)])
    assert cuts["cut_count"] == 2
    for cut in cuts["cuts"]:
        report = run_ok(
            [
                "cut",
                "inspect",
                "--manifest",
                str(manifest),
                "--cut",
                str(cut["cut_index"]),
                "--output-dir",
                str(ws / "reports"),
                "--transcript",
                str(transcript),
            ]
        )
        assert report["passed"] is True, report["checks"]

    # 7. Analyzed and mastered audio (deterministic baseline).
    analysis = run_ok(
        ["audio", "analyze", "--input", str(ws / "analysis" / "audio.wav")]
    )
    assert analysis["loudness"]["integrated_lufs"] < 0
    mastered = run_ok(
        [
            "audio",
            "master",
            "--input",
            str(ws / "analysis" / "audio.wav"),
            "--output",
            str(ws / "renders" / "mastered.wav"),
        ]
    )
    assert mastered["output"]["integrated_lufs"] == pytest.approx(-16.0, abs=1.5)

    # 8. Subtitles and a packaged neutral long-form output.
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        f"""
schema_version: "1"
profiles:
  master:
    canvas: {{width: 640, height: 360, frame_rate: 30}}
    video_codec: {{name: libx264, crf: 22, preset: veryfast}}
    audio_codec: {{name: aac, bitrate: 160k}}
    loudness: {{integrated_lufs: -16, true_peak_dbtp: -1.5, lra: 11}}
music:
  path: {music.name}
  gain_db: -22
"""
    )
    long_master = ws / "renders" / "episode.mp4"
    run_ok(
        [
            "render",
            "master",
            "--plan",
            str(plan_path),
            "--profile",
            str(profile_path),
            "--profile-name",
            "master",
            "--output",
            str(long_master),
        ]
    )
    srt = ws / "renders" / "episode.srt"
    subs = run_ok(
        [
            "subtitles",
            "create",
            "--manifest",
            str(ws / "renders" / "episode.mp4.manifest.json"),
            "--transcript",
            str(transcript),
            "--output-srt",
            str(srt),
            "--output-vtt",
            str(ws / "renders" / "episode.vtt"),
        ]
    )
    assert subs["cue_count"] == 3
    packaged = ws / "renders" / "episode-subs.mp4"
    run_ok(
        [
            "subtitles",
            "render",
            "--input",
            str(long_master),
            "--subtitles",
            str(srt),
            "--output",
            str(packaged),
            "--mode",
            "mux",
        ]
    )

    # 9. Synchronize the two sources and render a camera-switching plan.
    sync = run_ok(
        [
            "sync",
            "analyze",
            "--reference",
            str(cam_a),
            "--other",
            str(cam_b_raw),
            "--max-offset",
            "5",
        ]
    )
    assert sync["offset_seconds"] == pytest.approx(KNOWN_OFFSET, abs=0.05)
    aligned = ws / "renders" / "cam_b_aligned.mp4"
    run_ok(
        [
            "sync",
            "apply",
            "--input",
            str(cam_b_raw),
            "--offset",
            str(sync["offset_seconds"]),
            "--output",
            str(aligned),
        ]
    )
    multicam_plan = {
        "schema_version": "1",
        "plan_id": "acceptance-multicam",
        "sources": [
            {"id": "cam-a", "path": str(cam_a)},
            {"id": "cam-b", "path": str(aligned)},
        ],
        "timeline": [
            {"source": "cam-a", "in": 1.6, "out": 2.3, "reason": "wide"},
            {
                "source": "cam-a",
                "in": 3.0,
                "out": 4.4,
                "video_source": "cam-b",
                "reason": "camera B for the main point",
            },
            {"source": "cam-a", "in": 5.2, "out": 6.8, "reason": "back to wide"},
        ],
    }
    multicam_path = ws / "plans" / "multicam.json"
    multicam_path.write_text(json.dumps(multicam_plan))
    multicam_out = ws / "renders" / "multicam.mp4"
    run_ok(
        [
            "render",
            "preview",
            "--plan",
            str(multicam_path),
            "--output",
            str(multicam_out),
        ]
    )
    assert media.duration_of(multicam_out) == pytest.approx(3.7, abs=0.2)

    # 10. Derive and render a captioned vertical output from an explicit range.
    short_plan = ws / "plans" / "short.json"
    run_ok(
        [
            "short",
            "create-plan",
            "--input",
            str(cam_a),
            "--start",
            "3.0",
            "--end",
            "4.4",
            "--canvas",
            "270x480",
            "--crop",
            "160:0:202:360",
            "--reason",
            "main point chosen as the short",
            "--output",
            str(short_plan),
        ]
    )
    short_out = ws / "renders" / "short.mp4"
    run_ok(["render", "preview", "--plan", str(short_plan), "--output", str(short_out)])
    short_srt = ws / "renders" / "short.srt"
    run_ok(
        [
            "subtitles",
            "create",
            "--manifest",
            str(ws / "renders" / "short.mp4.manifest.json"),
            "--transcript",
            str(transcript),
            "--output-srt",
            str(short_srt),
            "--output-vtt",
            str(ws / "renders" / "short.vtt"),
        ]
    )
    captioned_short = ws / "renders" / "short-captioned.mp4"
    run_ok(
        [
            "subtitles",
            "render",
            "--input",
            str(short_out),
            "--subtitles",
            str(short_srt),
            "--output",
            str(captioned_short),
            "--mode",
            "mux",
        ]
    )

    # 11. Validate both final outputs.
    episode_report = run_ok(
        [
            "output",
            "validate",
            "--input",
            str(packaged),
            "--profile",
            str(profile_path),
            "--profile-name",
            "master",
            "--expect-duration",
            str(render["output_duration"]),
            "--expect-subtitles",
            "--subtitles",
            str(srt),
        ]
    )
    assert episode_report["passed"] is True, episode_report["issues"]

    short_report = run_ok(
        [
            "output",
            "validate",
            "--input",
            str(captioned_short),
            "--expect-duration",
            "1.4",
            "--expect-subtitles",
            "--subtitles",
            str(short_srt),
        ]
    )
    assert short_report["passed"] is True, short_report["issues"]
    video = next(
        s for s in media.probe(captioned_short)["streams"] if s["type"] == "video"
    )
    assert (video["width"], video["height"]) == (270, 480)

    # Sources remain untouched throughout.
    assert sha256_file(cam_a) == hash_before
