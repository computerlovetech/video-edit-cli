from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from generate_fixtures import generate_audio_only, generate_main  # noqa: E402

from video_editor import cli, schemas  # noqa: E402


@pytest.fixture(scope="session")
def fixtures_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("fixtures")


@pytest.fixture(scope="session")
def main_video(fixtures_dir: Path) -> Path:
    return generate_main(fixtures_dir / "main.mp4")


@pytest.fixture(scope="module")
def main_video_module(main_video: Path) -> Path:
    return main_video


@pytest.fixture(scope="session")
def audio_only(fixtures_dir: Path) -> Path:
    return generate_audio_only(fixtures_dir / "audio_only.wav")


def run_cli(argv: list[str]) -> tuple[int, dict[str, Any]]:
    """Run the CLI in-process; return (exit_code, parsed JSON envelope)."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = cli.run(argv)
    envelope: dict[str, Any] = json.loads(buffer.getvalue())
    schemas.validate(envelope, "result.schema.json")
    return code, envelope


@pytest.fixture
def cli_runner() -> Any:
    return run_cli
