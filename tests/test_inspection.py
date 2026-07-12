from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import run_cli
from video_editor import media


def test_probe_reports_streams(main_video: Path) -> None:
    code, envelope = run_cli(["probe", "--input", str(main_video)])
    assert code == 0
    data = envelope["data"]
    assert 7.5 < data["duration_seconds"] < 8.6
    types = {s["type"] for s in data["streams"]}
    assert types == {"video", "audio"}
    video = next(s for s in data["streams"] if s["type"] == "video")
    assert (video["width"], video["height"]) == (640, 360)
    assert video["frame_rate"] == 30.0
    audio = next(s for s in data["streams"] if s["type"] == "audio")
    assert audio["sample_rate"] == 48000


def test_probe_missing_file(tmp_path: Path) -> None:
    code, envelope = run_cli(["probe", "--input", str(tmp_path / "missing.mp4")])
    assert code != 0
    assert envelope["error"]["code"] == "invalid-input"


def test_audio_extract_lossless_wav(main_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "audio.wav"
    code, envelope = run_cli(
        ["audio", "extract", "--input", str(main_video), "--output", str(out)]
    )
    assert code == 0
    info = media.probe(out)
    stream = info["streams"][0]
    assert stream["codec"] == "pcm_s24le"
    assert stream["sample_rate"] == 48000
    sidecar = json.loads((tmp_path / "audio.wav.provenance.json").read_text())
    assert sidecar["inputs"][0]["path"] == str(main_video)
    assert {a["kind"] for a in envelope["artifacts"]} == {"audio", "provenance"}


def test_proxy_create(main_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "proxy.mp4"
    code, _ = run_cli(
        [
            "proxy",
            "create",
            "--input",
            str(main_video),
            "--output",
            str(out),
            "--height",
            "180",
        ]
    )
    assert code == 0
    video = next(s for s in media.probe(out)["streams"] if s["type"] == "video")
    assert video["height"] == 180


def test_frame_extract(main_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "frame.png"
    code, _ = run_cli(
        [
            "frame",
            "extract",
            "--input",
            str(main_video),
            "--time",
            "2.0",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    video = next(s for s in media.probe(out)["streams"] if s["type"] == "video")
    assert (video["width"], video["height"]) == (640, 360)


def test_frame_extract_out_of_range(main_video: Path, tmp_path: Path) -> None:
    code, envelope = run_cli(
        [
            "frame",
            "extract",
            "--input",
            str(main_video),
            "--time",
            "99",
            "--output",
            str(tmp_path / "frame.png"),
        ]
    )
    assert code != 0
    assert envelope["error"]["code"] == "invalid-input"


def test_filmstrip_create(main_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "strip.png"
    code, _ = run_cli(
        [
            "filmstrip",
            "create",
            "--input",
            str(main_video),
            "--start",
            "1",
            "--end",
            "5",
            "--columns",
            "4",
            "--frames",
            "8",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    video = next(s for s in media.probe(out)["streams"] if s["type"] == "video")
    assert video["width"] == 4 * 320


def test_waveform_create(main_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "wave.png"
    code, _ = run_cli(
        [
            "waveform",
            "create",
            "--input",
            str(main_video),
            "--start",
            "0",
            "--end",
            "8",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    assert out.stat().st_size > 0
    video = next(s for s in media.probe(out)["streams"] if s["type"] == "video")
    assert video["width"] == 1600


def test_preview_create_video(main_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "preview.mp4"
    code, _ = run_cli(
        [
            "preview",
            "create",
            "--input",
            str(main_video),
            "--start",
            "2",
            "--end",
            "4",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    info = media.probe(out)
    assert info["duration_seconds"] == pytest.approx(2.0, abs=0.2)


def test_preview_create_audio_only(audio_only: Path, tmp_path: Path) -> None:
    out = tmp_path / "preview.m4a"
    code, _ = run_cli(
        [
            "preview",
            "create",
            "--input",
            str(audio_only),
            "--start",
            "0.5",
            "--end",
            "2.5",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    info = media.probe(out)
    assert info["duration_seconds"] == pytest.approx(2.0, abs=0.2)


def test_invalid_range_rejected(main_video: Path, tmp_path: Path) -> None:
    code, envelope = run_cli(
        [
            "preview",
            "create",
            "--input",
            str(main_video),
            "--start",
            "5",
            "--end",
            "3",
            "--output",
            str(tmp_path / "p.mp4"),
        ]
    )
    assert code != 0
    assert envelope["error"]["code"] == "invalid-input"


def test_workspace_registration(main_video: Path, tmp_path: Path) -> None:
    root = tmp_path / "ws"
    run_cli(["workspace", "init", "--root", str(root), "--source", str(main_video)])
    out = root / "proxies" / "proxy.mp4"
    code, _ = run_cli(
        [
            "proxy",
            "create",
            "--input",
            str(main_video),
            "--output",
            str(out),
            "--workspace",
            str(root),
        ]
    )
    assert code == 0
    manifest = json.loads((root / "workspace.json").read_text())
    assert any(a["kind"] == "proxy" for a in manifest["artifacts"])


def test_missing_binary_fails_cleanly(
    main_video: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "/nonexistent")
    code, envelope = run_cli(["probe", "--input", str(main_video)])
    assert code == 3
    assert envelope["error"]["code"] == "missing-binary"
