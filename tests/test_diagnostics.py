from __future__ import annotations

from conftest import run_cli


def test_doctor_base_reports_binary_readiness() -> None:
    code, envelope = run_cli(["doctor", "--workflow", "base"])
    assert code == 0
    data = envelope["data"]
    assert data["workflow"] == "base"
    assert {check["name"] for check in data["checks"]} == {"ffmpeg", "ffprobe"}
    assert isinstance(data["passed"], bool)
