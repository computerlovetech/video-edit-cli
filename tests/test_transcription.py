from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import run_cli

RAW_FIXTURE = {
    "language": "en",
    "model": "fake-model",
    "segments": [
        {
            "start": 0.5,
            "end": 2.3,
            "text": "Hello there, welcome back.",
            "words": [
                {"text": "Hello", "start": 0.5, "end": 0.9, "confidence": 0.98},
                {"text": "there,", "start": 0.95, "end": 1.2, "confidence": 0.97},
                {"text": "welcome", "start": 1.5, "end": 1.9, "confidence": 0.99},
                {"text": "back.", "start": 1.95, "end": 2.3, "confidence": 0.96},
            ],
        },
        {
            "start": 3.0,
            "end": 4.4,
            "text": "Welcome back to the show.",
            "words": [
                {"text": "Welcome", "start": 3.0, "end": 3.3, "confidence": 0.99},
                {"text": "back", "start": 3.35, "end": 3.6, "confidence": 0.98},
                {"text": "to", "start": 3.65, "end": 3.75, "confidence": 0.99},
                {"text": "the", "start": 3.8, "end": 3.9, "confidence": 0.99},
                {"text": "show.", "start": 3.95, "end": 4.4, "confidence": 0.97},
            ],
        },
    ],
}


@pytest.fixture
def raw_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(RAW_FIXTURE))
    return path


@pytest.fixture
def transcript(audio_only: Path, raw_fixture: Path, tmp_path: Path) -> Path:
    out = tmp_path / "transcript.json"
    code, _ = run_cli(
        [
            "transcript",
            "create",
            "--input",
            str(audio_only),
            "--output",
            str(out),
            "--backend",
            "fixture",
            "--fixture",
            str(raw_fixture),
        ]
    )
    assert code == 0
    return out


def test_transcript_create_writes_valid_document(
    transcript: Path, audio_only: Path
) -> None:
    document = json.loads(transcript.read_text())
    assert document["backend"] == "fixture"
    assert document["language"] == "en"
    assert document["source"]["path"] == str(audio_only.resolve())
    assert len(document["source"]["sha256"]) == 64
    assert len(document["segments"]) == 2
    assert transcript.with_name("transcript.json.provenance.json").is_file()


def test_transcript_create_requires_fixture_path(
    audio_only: Path, tmp_path: Path
) -> None:
    code, envelope = run_cli(
        [
            "transcript",
            "create",
            "--input",
            str(audio_only),
            "--output",
            str(tmp_path / "t.json"),
            "--backend",
            "fixture",
        ]
    )
    assert code != 0
    assert envelope["error"]["code"] == "invalid-input"


def test_transcript_pack(transcript: Path, tmp_path: Path) -> None:
    out = tmp_path / "packed.txt"
    code, _ = run_cli(
        ["transcript", "pack", "--transcript", str(transcript), "--output", str(out)]
    )
    assert code == 0
    text = out.read_text()
    assert "[0.50-2.30] Hello there, welcome back." in text
    assert "[3.00-4.40] Welcome back to the show." in text


def test_transcript_search_time_aligned(transcript: Path) -> None:
    code, envelope = run_cli(
        [
            "transcript",
            "search",
            "--transcript",
            str(transcript),
            "--query",
            "welcome back",
        ]
    )
    assert code == 0
    matches = envelope["data"]["matches"]
    assert len(matches) == 2
    first, second = matches
    assert first["start"] == 1.5 and first["end"] == 2.3
    assert second["start"] == 3.0 and second["end"] == 3.6
    assert second["segment_text"] == "Welcome back to the show."


def test_transcript_search_no_match(transcript: Path) -> None:
    code, envelope = run_cli(
        [
            "transcript",
            "search",
            "--transcript",
            str(transcript),
            "--query",
            "nonexistent phrase",
        ]
    )
    assert code == 0
    assert envelope["data"]["match_count"] == 0


def test_mlx_backend_missing_dependency_fails_cleanly(
    audio_only: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    # A None entry makes any import of the module raise ImportError, whether
    # or not the optional dependency is installed in this environment.
    monkeypatch.setitem(sys.modules, "mlx_whisper", None)
    code, envelope = run_cli(
        [
            "transcript",
            "create",
            "--input",
            str(audio_only),
            "--output",
            str(tmp_path / "t.json"),
            "--backend",
            "mlx-whisper",
        ]
    )
    assert code == 5
    assert envelope["error"]["code"] == "missing-dependency"


@pytest.mark.integration
def test_mlx_backend_real_inference(audio_only: Path, tmp_path: Path) -> None:
    """Opt-in: run with `uv run pytest -m integration` after `uv sync --extra mlx`."""
    out = tmp_path / "t.json"
    code, envelope = run_cli(
        [
            "transcript",
            "create",
            "--input",
            str(audio_only),
            "--output",
            str(out),
            "--backend",
            "mlx-whisper",
        ]
    )
    assert code == 0
    assert envelope["data"]["segment_count"] >= 0
