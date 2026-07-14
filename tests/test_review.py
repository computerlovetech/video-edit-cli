from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from conftest import run_cli


@pytest.fixture(scope="module")
def rendered(main_video_module: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Render a 3-clip rough cut; return the manifest path."""
    tmp = tmp_path_factory.mktemp("render")
    plan = {
        "schema_version": "1",
        "plan_id": "review-plan",
        "sources": [{"id": "src-1", "path": str(main_video_module)}],
        "timeline": [
            {"source": "src-1", "in": 0.5, "out": 2.3, "reason": "a"},
            {"source": "src-1", "in": 3.0, "out": 3.7, "reason": "b"},
            {"source": "src-1", "in": 5.2, "out": 6.8, "reason": "c"},
        ],
    }
    plan_path = tmp / "plan.json"
    plan_path.write_text(json.dumps(plan))
    out = tmp / "rough.mp4"
    code, _ = run_cli(
        ["render", "preview", "--plan", str(plan_path), "--output", str(out)]
    )
    assert code == 0
    return tmp / "rough.mp4.manifest.json"


def test_cuts_list(rendered: Path) -> None:
    code, envelope = run_cli(["cuts", "list", "--manifest", str(rendered)])
    assert code == 0
    data = envelope["data"]
    assert data["cut_count"] == 2
    first = data["cuts"][0]
    assert first["output_time"] == pytest.approx(1.8)
    assert first["before"]["source_out"] == 2.3
    assert first["after"]["source_in"] == 3.0
    assert first["boundary_type"] == "temporal-cut"
    assert first["source_continuous"] is False


def test_transform_boundary_skips_clipped_word_check(
    main_video: Path, tmp_path: Path
) -> None:
    plan = {
        "schema_version": "1",
        "plan_id": "transform-plan",
        "sources": [{"id": "src-1", "path": str(main_video)}],
        "timeline": [
            {
                "source": "src-1",
                "in": 0.5,
                "out": 2.3,
                "reason": "first crop",
                "crop": {"x": 0, "y": 0, "width": 320, "height": 360},
            },
            {
                "source": "src-1",
                "in": 2.3,
                "out": 4.0,
                "reason": "second crop",
                "crop": {"x": 320, "y": 0, "width": 320, "height": 360},
            },
        ],
    }
    plan_path = tmp_path / "transform.json"
    plan_path.write_text(json.dumps(plan))
    render_path = tmp_path / "transform.mp4"
    code, _ = run_cli(
        ["render", "preview", "--plan", str(plan_path), "--output", str(render_path)]
    )
    assert code == 0
    manifest = render_path.with_name(render_path.name + ".manifest.json")
    code, envelope = run_cli(["cuts", "list", "--manifest", str(manifest)])
    assert code == 0
    assert envelope["data"]["cuts"][0]["boundary_type"] == "transform"

    transcript = make_transcript(tmp_path, main_video)
    code, envelope = run_cli(
        [
            "cut",
            "inspect",
            "--manifest",
            str(manifest),
            "--all",
            "--output-dir",
            str(tmp_path / "reports"),
            "--transcript",
            str(transcript),
        ]
    )
    assert code == 0
    assert envelope["data"]["cut_count"] == 1
    checks = envelope["data"]["reports"][0]["checks"]
    assert checks["clipped_word_check"] == "skipped-continuous-source"
    assert checks["clipped_word_before"] is None


def test_cut_inspect_bundle(rendered: Path, tmp_path: Path) -> None:
    code, envelope = run_cli(
        [
            "cut",
            "inspect",
            "--manifest",
            str(rendered),
            "--cut",
            "0",
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert code == 0
    data = envelope["data"]
    for kind in ("filmstrip", "waveform", "preview", "frame_before", "frame_after"):
        assert Path(data["artifacts"][kind]).is_file(), kind
    assert Path(data["report_path"]).is_file()
    assert "black_frames_near_cut" in data["checks"]
    # testsrc video has no black frames and no words are clipped
    assert data["checks"]["black_frames_near_cut"] == []


def test_cut_inspect_out_of_range(rendered: Path, tmp_path: Path) -> None:
    code, envelope = run_cli(
        [
            "cut",
            "inspect",
            "--manifest",
            str(rendered),
            "--cut",
            "9",
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert code != 0
    assert "out of range" in envelope["error"]["message"]


def make_transcript(tmp_path: Path, source: Path) -> Path:
    """Transcript where a word spans source time 3.7 (the second clip's out)."""
    from video_editor.provenance import sha256_file

    document: dict[str, Any] = {
        "schema_version": "1",
        "source": {
            "path": str(source),
            "sha256": sha256_file(source),
            "source_id": "src-1",
        },
        "language": "en",
        "backend": "fixture",
        "model": "fake",
        "created_at": "2026-07-12T00:00:00+00:00",
        "segments": [
            {
                "start": 3.0,
                "end": 4.4,
                "text": "word spanning the cut",
                "words": [
                    {"text": "spanning", "start": 3.6, "end": 3.9, "confidence": 0.9}
                ],
            }
        ],
    }
    path = tmp_path / "transcript.json"
    path.write_text(json.dumps(document))
    return path


def test_cut_inspect_detects_clipped_word(
    rendered: Path, main_video_module: Path, tmp_path: Path
) -> None:
    transcript = make_transcript(tmp_path, main_video_module)
    code, envelope = run_cli(
        [
            "cut",
            "inspect",
            "--manifest",
            str(rendered),
            "--cut",
            "1",
            "--output-dir",
            str(tmp_path),
            "--transcript",
            str(transcript),
        ]
    )
    assert code == 0
    checks = envelope["data"]["checks"]
    assert checks["clipped_word_before"] == {
        "text": "spanning",
        "start": 3.6,
        "end": 3.9,
    }
    assert envelope["data"]["passed"] is False
