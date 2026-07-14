from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from conftest import run_cli
from generate_fixtures import generate_image, generate_music
from video_editor import media

TIMELINE = [
    {"source": "src-1", "in": 0.5, "out": 2.3, "reason": "a"},
    {"source": "src-1", "in": 3.0, "out": 4.4, "reason": "b"},
    {"source": "src-1", "in": 5.2, "out": 6.8, "reason": "c"},
]


@pytest.fixture(scope="module")
def pkg(
    main_video_module: Path, tmp_path_factory: pytest.TempPathFactory
) -> dict[str, Any]:
    """Profile YAML, music asset, plan, preview render manifest, transcript."""
    tmp = tmp_path_factory.mktemp("packaging")
    music = generate_music(tmp / "music.wav")
    profile_path = tmp / "profile.yaml"
    profile_path.write_text(
        f"""
schema_version: "1"
profiles:
  master:
    canvas: {{width: 640, height: 360, frame_rate: 30}}
    video_codec: {{name: libx264, crf: 22, preset: veryfast}}
    audio_codec: {{name: aac, bitrate: 160k}}
    loudness: {{integrated_lufs: -16, true_peak_dbtp: -1.5, lra: 11}}
    subtitles: {{mode: mux}}
music:
  path: {music.name}
  gain_db: -20
  ducking: {{threshold: 0.02, ratio: 8}}
"""
    )
    plan = {
        "schema_version": "1",
        "plan_id": "pkg-plan",
        "sources": [{"id": "src-1", "path": str(main_video_module)}],
        "timeline": TIMELINE,
    }
    plan_path = tmp / "plan.json"
    plan_path.write_text(json.dumps(plan))

    preview = tmp / "preview.mp4"
    code, _ = run_cli(
        ["render", "preview", "--plan", str(plan_path), "--output", str(preview)]
    )
    assert code == 0

    from video_editor.provenance import sha256_file

    transcript = {
        "schema_version": "1",
        "source": {
            "path": str(main_video_module),
            "sha256": sha256_file(main_video_module),
            "source_id": "src-1",
        },
        "language": "en",
        "backend": "fixture",
        "model": "fake",
        "created_at": "2026-07-12T00:00:00+00:00",
        "segments": [
            {
                "start": 0.5,
                "end": 2.3,
                "text": "hello there world",
                "words": [
                    {"text": "hello", "start": 0.6, "end": 1.0, "confidence": 0.9},
                    {"text": "there", "start": 1.1, "end": 1.5, "confidence": 0.9},
                    {"text": "world", "start": 1.6, "end": 2.2, "confidence": 0.9},
                ],
            },
            {
                "start": 2.4,
                "end": 2.9,
                "text": "dropped words",
                "words": [
                    {"text": "dropped", "start": 2.4, "end": 2.6, "confidence": 0.9},
                    {"text": "words", "start": 2.65, "end": 2.9, "confidence": 0.9},
                ],
            },
            {
                "start": 3.1,
                "end": 4.3,
                "text": "second kept segment",
                "words": [
                    {"text": "second", "start": 3.1, "end": 3.5, "confidence": 0.9},
                    {"text": "kept", "start": 3.6, "end": 3.9, "confidence": 0.9},
                    {"text": "segment", "start": 4.0, "end": 4.3, "confidence": 0.9},
                ],
            },
        ],
    }
    transcript_path = tmp / "transcript.json"
    transcript_path.write_text(json.dumps(transcript))
    return {
        "tmp": tmp,
        "profile": profile_path,
        "plan": plan_path,
        "manifest": tmp / "preview.mp4.manifest.json",
        "transcript": transcript_path,
    }


def test_render_master_with_profile_and_music(pkg: dict[str, Any]) -> None:
    out = pkg["tmp"] / "master.mp4"
    code, envelope = run_cli(
        [
            "render",
            "master",
            "--plan",
            str(pkg["plan"]),
            "--profile",
            str(pkg["profile"]),
            "--profile-name",
            "master",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    info = media.probe(out)
    video = next(s for s in info["streams"] if s["type"] == "video")
    assert (video["width"], video["height"]) == (640, 360)
    assert info["duration_seconds"] == pytest.approx(4.8, abs=0.3)

    code, envelope = run_cli(
        [
            "output",
            "validate",
            "--input",
            str(out),
            "--profile",
            str(pkg["profile"]),
            "--profile-name",
            "master",
            "--expect-duration",
            "4.8",
        ]
    )
    assert code == 0
    assert envelope["data"]["passed"] is True, envelope["data"]["issues"]


def test_render_master_unknown_profile(pkg: dict[str, Any]) -> None:
    code, envelope = run_cli(
        [
            "render",
            "master",
            "--plan",
            str(pkg["plan"]),
            "--profile",
            str(pkg["profile"]),
            "--profile-name",
            "nope",
            "--output",
            str(pkg["tmp"] / "x.mp4"),
        ]
    )
    assert code != 0
    assert "unknown render profile" in envelope["error"]["message"]


def test_profile_missing_music_rejected(pkg: dict[str, Any], tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        'schema_version: "1"\n'
        "profiles:\n  master:\n    canvas: {width: 640, height: 360}\n"
        "music:\n  path: missing.wav\n"
    )
    code, envelope = run_cli(
        [
            "render",
            "master",
            "--plan",
            str(pkg["plan"]),
            "--profile",
            str(bad),
            "--profile-name",
            "master",
            "--output",
            str(tmp_path / "x.mp4"),
        ]
    )
    assert code != 0
    assert "music file not found" in envelope["error"]["message"]


def test_subtitles_create_maps_through_cuts(
    pkg: dict[str, Any], tmp_path: Path
) -> None:
    srt, vtt = tmp_path / "subs.srt", tmp_path / "subs.vtt"
    code, envelope = run_cli(
        [
            "subtitles",
            "create",
            "--manifest",
            str(pkg["manifest"]),
            "--transcript",
            str(pkg["transcript"]),
            "--output-srt",
            str(srt),
            "--output-vtt",
            str(vtt),
        ]
    )
    assert code == 0
    data = envelope["data"]
    # "dropped words" (2.4-2.9) is removed; two cues survive.
    assert data["cue_count"] == 2
    # First cue: words 0.6-2.2 in a clip starting at source 0.5 -> output 0.1-1.7
    assert data["first_cue_start"] == pytest.approx(0.1, abs=0.01)
    # Second cue: words 3.1-4.3 in clip [3.0, 4.4) at output offset 1.8 -> 1.9-3.1
    assert data["last_cue_end"] == pytest.approx(3.1, abs=0.01)
    text = srt.read_text()
    assert "hello there world" in text
    assert "dropped" not in text
    assert vtt.read_text().startswith("WEBVTT")


def test_subtitles_create_reflows_for_short_form(
    pkg: dict[str, Any], tmp_path: Path
) -> None:
    srt = tmp_path / "short.srt"
    code, envelope = run_cli(
        [
            "subtitles",
            "create",
            "--manifest",
            str(pkg["manifest"]),
            "--transcript",
            str(pkg["transcript"]),
            "--output-srt",
            str(srt),
            "--output-vtt",
            str(tmp_path / "short.vtt"),
            "--max-words",
            "2",
            "--max-chars",
            "12",
            "--max-duration",
            "1.0",
        ]
    )
    assert code == 0
    assert envelope["data"]["cue_count"] > 2
    cue_lines = [
        line
        for line in srt.read_text().splitlines()
        if line and "-->" not in line and not line.isdigit()
    ]
    assert all(len(line.split()) <= 2 for line in cue_lines)
    assert all(len(line) <= 12 for line in cue_lines)


def test_subtitles_render_mux_and_validate(pkg: dict[str, Any], tmp_path: Path) -> None:
    srt = tmp_path / "subs.srt"
    run_cli(
        [
            "subtitles",
            "create",
            "--manifest",
            str(pkg["manifest"]),
            "--transcript",
            str(pkg["transcript"]),
            "--output-srt",
            str(srt),
            "--output-vtt",
            str(tmp_path / "subs.vtt"),
        ]
    )
    out = tmp_path / "subtitled.mp4"
    code, _ = run_cli(
        [
            "subtitles",
            "render",
            "--input",
            str(pkg["tmp"] / "preview.mp4"),
            "--subtitles",
            str(srt),
            "--output",
            str(out),
            "--mode",
            "mux",
        ]
    )
    assert code == 0
    types = {s["type"] for s in media.probe(out)["streams"]}
    assert "subtitle" in types

    code, envelope = run_cli(
        [
            "output",
            "validate",
            "--input",
            str(out),
            "--expect-subtitles",
            "--subtitles",
            str(srt),
        ]
    )
    assert code == 0
    assert envelope["data"]["passed"] is True, envelope["data"]["issues"]


def test_subtitles_render_rejects_style_in_mux_mode(
    pkg: dict[str, Any], tmp_path: Path
) -> None:
    srt = tmp_path / "subs.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n")
    code, envelope = run_cli(
        [
            "subtitles",
            "render",
            "--input",
            str(pkg["tmp"] / "preview.mp4"),
            "--subtitles",
            str(srt),
            "--output",
            str(tmp_path / "styled.mp4"),
            "--mode",
            "mux",
            "--font",
            "Arial",
        ]
    )
    assert code != 0
    assert "style options require --mode burn" in envelope["error"]["message"]


def test_asset_inspect(tmp_path: Path, audio_only: Path) -> None:
    image = generate_image(tmp_path / "logo.png")
    code, envelope = run_cli(["asset", "inspect", "--input", str(image)])
    assert code == 0
    assert envelope["data"]["kind"] == "image"

    code, envelope = run_cli(["asset", "inspect", "--input", str(audio_only)])
    assert code == 0
    assert envelope["data"]["kind"] == "audio"

    font = tmp_path / "font.ttf"
    font.write_bytes(b"\x00\x01\x00\x00fake")
    code, envelope = run_cli(["asset", "inspect", "--input", str(font)])
    assert code == 0
    assert envelope["data"]["kind"] == "font"

    weird = tmp_path / "thing.xyz"
    weird.write_text("x")
    code, envelope = run_cli(["asset", "inspect", "--input", str(weird)])
    assert code != 0
    assert "unrecognized asset type" in envelope["error"]["message"]


def test_output_validate_flags_duration_mismatch(pkg: dict[str, Any]) -> None:
    code, envelope = run_cli(
        [
            "output",
            "validate",
            "--input",
            str(pkg["tmp"] / "preview.mp4"),
            "--expect-duration",
            "60",
        ]
    )
    assert code == 0
    data = envelope["data"]
    assert data["passed"] is False
    assert any("duration" in issue for issue in data["issues"])
    assert data["validation_scope"] == {
        "technical": "performed",
        "visual_framing": "not_performed",
        "editorial": "not_performed",
    }


def test_output_validate_expect_canvas(pkg: dict[str, Any]) -> None:
    preview = str(pkg["tmp"] / "preview.mp4")
    code, envelope = run_cli(
        ["output", "validate", "--input", preview, "--expect-canvas", "640x360"]
    )
    assert code == 0
    assert envelope["data"]["passed"] is True

    code, envelope = run_cli(
        ["output", "validate", "--input", preview, "--expect-canvas", "1080x1920"]
    )
    assert code == 0
    assert envelope["data"]["passed"] is False
    assert any("canvas" in issue for issue in envelope["data"]["issues"])
