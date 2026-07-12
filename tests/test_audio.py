from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest

from conftest import run_cli
from video_editor import media


def test_audio_analyze(audio_only: Path) -> None:
    code, envelope = run_cli(["audio", "analyze", "--input", str(audio_only)])
    assert code == 0
    data = envelope["data"]
    assert -70 < data["loudness"]["integrated_lufs"] < 0
    assert data["loudness"]["true_peak_dbtp"] < 0
    # Fixture has bursts separated by silence
    assert data["silence"]["count"] >= 1
    assert data["clipping"]["likely_clipped"] is False
    assert data["bandwidth"]["high_frequency_dropoff_db"] is not None


def test_audio_master_hits_targets(audio_only: Path, tmp_path: Path) -> None:
    out = tmp_path / "mastered.wav"
    code, envelope = run_cli(
        [
            "audio",
            "master",
            "--input",
            str(audio_only),
            "--output",
            str(out),
            "--target-lufs",
            "-16",
            "--true-peak",
            "-1.5",
        ]
    )
    assert code == 0
    metrics = envelope["data"]["output"]
    assert metrics["integrated_lufs"] == pytest.approx(-16.0, abs=1.5)
    assert metrics["true_peak_dbtp"] <= -1.0
    stream = media.probe(out)["streams"][0]
    assert stream["codec"] == "pcm_s24le"
    assert stream["sample_rate"] == 48000
    assert (tmp_path / "mastered.wav.provenance.json").is_file()


def test_audio_master_rejects_lossy_output(audio_only: Path, tmp_path: Path) -> None:
    code, envelope = run_cli(
        [
            "audio",
            "master",
            "--input",
            str(audio_only),
            "--output",
            str(tmp_path / "m.mp3"),
        ]
    )
    assert code != 0
    assert "lossless" in envelope["error"]["message"]


def test_audio_denoise_missing_dependency(audio_only: Path, tmp_path: Path) -> None:
    code, envelope = run_cli(
        [
            "audio",
            "denoise",
            "--input",
            str(audio_only),
            "--output",
            str(tmp_path / "d.wav"),
            "--backend",
            "deepfilternet",
        ]
    )
    # DeepFilterNet is not installed in the test environment
    assert code == 5
    assert envelope["error"]["code"] == "missing-dependency"


def test_audio_denoise_with_fake_backend(
    audio_only: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mock df.enhance so the wrapper is exercised without model weights."""
    import shutil

    class FakeState:
        def sr(self) -> int:
            return 48000

    fake = types.ModuleType("df.enhance")

    def init_df() -> tuple[Any, Any, Any]:
        return object(), FakeState(), None

    captured: dict[str, str] = {}

    def load_audio(path: str, sr: int) -> tuple[Any, Any]:
        captured["source"] = path
        return "audio-tensor", None

    def enhance(model: Any, state: Any, audio: Any) -> Any:
        assert audio == "audio-tensor"
        return "enhanced-tensor"

    def save_audio(path: str, audio: Any, sr: int) -> None:
        assert audio == "enhanced-tensor"
        shutil.copyfile(captured["source"], path)

    fake_any: Any = fake
    fake_any.init_df = init_df
    fake_any.load_audio = load_audio
    fake_any.enhance = enhance
    fake_any.save_audio = save_audio
    monkeypatch.setitem(sys.modules, "df.enhance", fake)

    out = tmp_path / "denoised.wav"
    code, envelope = run_cli(
        [
            "audio",
            "denoise",
            "--input",
            str(audio_only),
            "--output",
            str(out),
            "--backend",
            "deepfilternet",
        ]
    )
    assert code == 0
    assert out.is_file()
    assert envelope["data"]["backend"] == "deepfilternet"
    assert (tmp_path / "denoised.wav.provenance.json").is_file()


def test_audio_compare(audio_only: Path, tmp_path: Path) -> None:
    quiet = tmp_path / "quiet.wav"
    import subprocess

    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostdin",
            "-y",
            "-i",
            str(audio_only),
            "-af",
            "volume=-10dB",
            str(quiet),
        ],
        check=True,
        capture_output=True,
    )
    out_dir = tmp_path / "ab"
    code, envelope = run_cli(
        [
            "audio",
            "compare",
            "--input",
            str(audio_only),
            "--input",
            str(quiet),
            "--output-dir",
            str(out_dir),
            "--duration",
            "4",
        ]
    )
    assert code == 0
    data = envelope["data"]
    assert len(data["candidates"]) == 2
    gains = [c["match_gain_db"] for c in data["candidates"]]
    assert gains[1] - gains[0] == pytest.approx(10.0, abs=1.0)
    for candidate in data["candidates"]:
        sample = Path(candidate["ab_sample"])
        assert sample.is_file()
    # Matched samples should measure within ~1.5 LU of each other
    from video_editor.audio.analysis import measure_loudness

    matched = [
        measure_loudness(Path(c["ab_sample"]))["integrated_lufs"]
        for c in data["candidates"]
    ]
    assert abs(matched[0] - matched[1]) < 1.5
    assert (out_dir / "audio-compare-report.json").is_file()


def test_audio_compare_needs_two_inputs(audio_only: Path, tmp_path: Path) -> None:
    code, envelope = run_cli(
        [
            "audio",
            "compare",
            "--input",
            str(audio_only),
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert code != 0
    assert "at least two" in envelope["error"]["message"]
