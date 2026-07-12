from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from conftest import run_cli
from video_editor import media


def make_plan(main_video: Path, timeline: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "plan_id": "plan-test",
        "sources": [{"id": "src-1", "path": str(main_video)}],
        "timeline": timeline,
    }


def write_plan(tmp_path: Path, plan: dict[str, Any]) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return path


GOOD_TIMELINE = [
    {"source": "src-1", "in": 0.5, "out": 2.3, "reason": "keep first burst"},
    {"source": "src-1", "in": 3.0, "out": 4.4, "reason": "keep second sentence"},
    {"source": "src-1", "in": 5.2, "out": 6.8, "reason": "keep closing sentence"},
]


def test_plan_validate_good(main_video: Path, tmp_path: Path) -> None:
    path = write_plan(tmp_path, make_plan(main_video, GOOD_TIMELINE))
    code, envelope = run_cli(["plan", "validate", "--plan", str(path)])
    assert code == 0
    data = envelope["data"]
    assert data["valid"] is True
    assert data["clip_count"] == 3
    assert data["output_duration"] == pytest.approx(4.8)
    assert data["boundaries"] == [pytest.approx(1.8), pytest.approx(3.2)]


@pytest.mark.parametrize(
    ("timeline", "fragment"),
    [
        ([{"source": "src-9", "in": 0, "out": 1, "reason": "x"}], "unknown source"),
        ([{"source": "src-1", "in": 2, "out": 1, "reason": "x"}], "must be <"),
        ([{"source": "src-1", "in": 0, "out": 999, "reason": "x"}], "exceeds source"),
        (
            [
                {"source": "src-1", "in": 1, "out": 3, "reason": "x"},
                {"source": "src-1", "in": 2, "out": 4, "reason": "y"},
            ],
            "overlaps or reorders",
        ),
        (
            [
                {"source": "src-1", "in": 4, "out": 5, "reason": "x"},
                {"source": "src-1", "in": 1, "out": 2, "reason": "y"},
            ],
            "overlaps or reorders",
        ),
    ],
)
def test_plan_validate_rejects(
    main_video: Path, tmp_path: Path, timeline: list[dict[str, Any]], fragment: str
) -> None:
    path = write_plan(tmp_path, make_plan(main_video, timeline))
    code, envelope = run_cli(["plan", "validate", "--plan", str(path)])
    assert code != 0
    assert envelope["error"]["code"] == "invalid-input"
    assert fragment in envelope["error"]["message"]


def test_plan_validate_rejects_missing_reason(main_video: Path, tmp_path: Path) -> None:
    plan = make_plan(main_video, [{"source": "src-1", "in": 0, "out": 1}])
    path = write_plan(tmp_path, plan)
    code, envelope = run_cli(["plan", "validate", "--plan", str(path)])
    assert code != 0
    assert "reason" in envelope["error"]["message"]


def test_plan_validate_rejects_unknown_operation(
    main_video: Path, tmp_path: Path
) -> None:
    plan = make_plan(main_video, json.loads(json.dumps(GOOD_TIMELINE)))
    plan["timeline"][0]["explode"] = True
    path = write_plan(tmp_path, plan)
    code, envelope = run_cli(["plan", "validate", "--plan", str(path)])
    assert code != 0
    assert envelope["error"]["code"] == "invalid-input"


def test_plan_validate_rejects_missing_source_file(tmp_path: Path) -> None:
    plan = {
        "schema_version": "1",
        "plan_id": "p",
        "sources": [{"id": "src-1", "path": str(tmp_path / "gone.mp4")}],
        "timeline": [{"source": "src-1", "in": 0, "out": 1, "reason": "x"}],
    }
    path = write_plan(tmp_path, plan)
    code, envelope = run_cli(["plan", "validate", "--plan", str(path)])
    assert code != 0
    assert "not found" in envelope["error"]["message"]


def test_render_preview_rough_cut(main_video: Path, tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path, make_plan(main_video, GOOD_TIMELINE))
    out = tmp_path / "rough.mp4"
    code, envelope = run_cli(
        ["render", "preview", "--plan", str(plan_path), "--output", str(out)]
    )
    assert code == 0
    info = media.probe(out)
    assert info["duration_seconds"] == pytest.approx(4.8, abs=0.2)
    video = next(s for s in info["streams"] if s["type"] == "video")
    assert video["height"] == 360
    assert envelope["data"]["boundaries"] == [pytest.approx(1.8), pytest.approx(3.2)]

    manifest = json.loads((tmp_path / "rough.mp4.manifest.json").read_text())
    assert manifest["kind"] == "render-preview"
    assert len(manifest["segments"]) == 3
    assert manifest["segments"][1]["output_start"] == pytest.approx(1.8)
    assert manifest["segments"][1]["in"] == 3.0
    assert manifest["output"]["path"] == str(out)
    # Source untouched
    assert media.duration_of(main_video) > 7.5


def test_render_preview_rejects_invalid_plan(main_video: Path, tmp_path: Path) -> None:
    plan_path = write_plan(
        tmp_path,
        make_plan(main_video, [{"source": "src-1", "in": 5, "out": 4, "reason": "x"}]),
    )
    code, envelope = run_cli(
        [
            "render",
            "preview",
            "--plan",
            str(plan_path),
            "--output",
            str(tmp_path / "o.mp4"),
        ]
    )
    assert code != 0
    assert envelope["error"]["code"] == "invalid-input"
    assert not (tmp_path / "o.mp4").exists()
