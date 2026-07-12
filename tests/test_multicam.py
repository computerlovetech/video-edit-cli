from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import run_cli
from generate_fixtures import KNOWN_OFFSET, generate_offset
from video_editor import media


@pytest.fixture(scope="module")
def offset_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return generate_offset(tmp_path_factory.mktemp("sync") / "offset.mp4")


def test_sync_analyze_recovers_known_offset(
    main_video_module: Path, offset_video: Path
) -> None:
    code, envelope = run_cli(
        [
            "sync",
            "analyze",
            "--reference",
            str(main_video_module),
            "--other",
            str(offset_video),
            "--max-offset",
            "5",
        ]
    )
    assert code == 0
    data = envelope["data"]
    assert data["offset_seconds"] == pytest.approx(KNOWN_OFFSET, abs=0.05)
    assert data["candidates"]


def test_sync_apply_trim_and_metadata(offset_video: Path, tmp_path: Path) -> None:
    aligned = tmp_path / "aligned.mp4"
    code, _ = run_cli(
        [
            "sync",
            "apply",
            "--input",
            str(offset_video),
            "--offset",
            str(KNOWN_OFFSET),
            "--output",
            str(aligned),
        ]
    )
    assert code == 0
    original = media.duration_of(offset_video)
    assert media.duration_of(aligned) == pytest.approx(original - KNOWN_OFFSET, abs=0.2)

    mapping = tmp_path / "mapping.json"
    code, envelope = run_cli(
        [
            "sync",
            "apply",
            "--input",
            str(offset_video),
            "--offset",
            str(KNOWN_OFFSET),
            "--output",
            str(mapping),
        ]
    )
    assert code == 0
    assert envelope["data"]["mode"] == "metadata"
    assert json.loads(mapping.read_text())["offset_seconds"] == KNOWN_OFFSET


def test_camera_switching_plan_renders(
    main_video_module: Path, offset_video: Path, tmp_path: Path
) -> None:
    """Audio from cam A throughout; video switches to aligned cam B mid-way."""
    aligned = tmp_path / "aligned.mp4"
    run_cli(
        [
            "sync",
            "apply",
            "--input",
            str(offset_video),
            "--offset",
            str(KNOWN_OFFSET),
            "--output",
            str(aligned),
        ]
    )
    plan = {
        "schema_version": "1",
        "plan_id": "multicam",
        "sources": [
            {"id": "cam-a", "path": str(main_video_module)},
            {"id": "cam-b", "path": str(aligned)},
        ],
        "timeline": [
            {"source": "cam-a", "in": 0.5, "out": 2.3, "reason": "wide shot"},
            {
                "source": "cam-a",
                "in": 3.0,
                "out": 4.4,
                "video_source": "cam-b",
                "reason": "cut to camera B for reaction",
            },
            {"source": "cam-a", "in": 5.2, "out": 6.8, "reason": "back to wide"},
        ],
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    out = tmp_path / "multicam.mp4"
    code, envelope = run_cli(
        ["render", "preview", "--plan", str(plan_path), "--output", str(out)]
    )
    assert code == 0
    assert media.duration_of(out) == pytest.approx(4.8, abs=0.2)
    assert envelope["data"]["boundaries"] == [pytest.approx(1.8), pytest.approx(3.2)]


def test_reframe_preview(main_video_module: Path, tmp_path: Path) -> None:
    out = tmp_path / "reframed.mp4"
    code, envelope = run_cli(
        [
            "reframe",
            "preview",
            "--input",
            str(main_video_module),
            "--start",
            "1",
            "--end",
            "3",
            "--crop",
            "160:0:202:360",
            "--canvas",
            "270x480",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    video = next(s for s in media.probe(out)["streams"] if s["type"] == "video")
    assert (video["width"], video["height"]) == (270, 480)


def test_reframe_preview_rejects_out_of_frame_crop(
    main_video_module: Path, tmp_path: Path
) -> None:
    code, envelope = run_cli(
        [
            "reframe",
            "preview",
            "--input",
            str(main_video_module),
            "--start",
            "1",
            "--end",
            "3",
            "--crop",
            "600:0:202:360",
            "--canvas",
            "270x480",
            "--output",
            str(tmp_path / "x.mp4"),
        ]
    )
    assert code != 0
    assert "exceeds source frame" in envelope["error"]["message"]


def test_short_create_plan_and_render(main_video_module: Path, tmp_path: Path) -> None:
    plan_path = tmp_path / "short.json"
    code, envelope = run_cli(
        [
            "short",
            "create-plan",
            "--input",
            str(main_video_module),
            "--start",
            "3.0",
            "--end",
            "4.4",
            "--canvas",
            "270x480",
            "--crop",
            "160:0:202:360",
            "--reason",
            "strong moment chosen by the agent",
            "--output",
            str(plan_path),
        ]
    )
    assert code == 0
    plan = json.loads(plan_path.read_text())
    assert plan["output_canvas"]["width"] == 270
    assert plan["timeline"][0]["in"] == 3.0

    out = tmp_path / "short.mp4"
    code, _ = run_cli(
        ["render", "preview", "--plan", str(plan_path), "--output", str(out)]
    )
    assert code == 0
    video = next(s for s in media.probe(out)["streams"] if s["type"] == "video")
    assert (video["width"], video["height"]) == (270, 480)
    assert media.duration_of(out) == pytest.approx(1.4, abs=0.2)
