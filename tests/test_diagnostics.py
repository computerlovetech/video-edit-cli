from __future__ import annotations

from conftest import run_cli


def test_doctor_base_reports_binary_readiness() -> None:
    code, envelope = run_cli(["doctor", "--workflow", "base"])
    assert code == 0
    data = envelope["data"]
    assert data["workflow"] == "base"
    assert {check["name"] for check in data["checks"]} == {"ffmpeg", "ffprobe"}
    assert isinstance(data["passed"], bool)


def test_doctor_audio_restoration_reports_runtime_imports() -> None:
    code, envelope = run_cli(["doctor", "--workflow", "audio-restoration"])
    assert code == 0
    data = envelope["data"]
    assert data["workflow"] == "audio-restoration"
    names = {check["name"] for check in data["checks"]}
    assert {"ffmpeg", "ffprobe"}.issubset(names)
    assert {
        "python-import:torch",
        "python-import:torchaudio",
        "python-import:soundfile",
        "python-import:df.enhance",
    }.issubset(names)
    assert all("detail" in check for check in data["checks"])
