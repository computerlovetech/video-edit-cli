from __future__ import annotations

import json
from pathlib import Path

from conftest import run_cli
from video_editor.provenance import sha256_file


def test_workspace_init_registers_sources_without_modifying_them(
    main_video: Path, tmp_path: Path
) -> None:
    before = sha256_file(main_video)
    root = tmp_path / "ws"
    code, envelope = run_cli(
        ["workspace", "init", "--root", str(root), "--source", str(main_video)]
    )
    assert code == 0
    assert envelope["ok"] is True
    assert sha256_file(main_video) == before

    manifest = json.loads((root / "workspace.json").read_text())
    assert manifest["sources"][0]["sha256"] == before
    assert manifest["sources"][0]["id"] == "src-1"
    for sub in (
        "sources",
        "analysis",
        "proxies",
        "plans",
        "previews",
        "renders",
        "reports",
    ):
        assert (root / sub).is_dir()
    link = root / "sources" / "src-1.mp4"
    assert link.is_symlink() and link.resolve() == main_video.resolve()


def test_workspace_init_rejects_existing_root(main_video: Path, tmp_path: Path) -> None:
    root = tmp_path / "ws"
    run_cli(["workspace", "init", "--root", str(root), "--source", str(main_video)])
    code, envelope = run_cli(
        ["workspace", "init", "--root", str(root), "--source", str(main_video)]
    )
    assert code != 0
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "invalid-input"


def test_workspace_init_rejects_missing_source(tmp_path: Path) -> None:
    code, envelope = run_cli(
        [
            "workspace",
            "init",
            "--root",
            str(tmp_path / "ws"),
            "--source",
            str(tmp_path / "nope.mp4"),
        ]
    )
    assert code != 0
    assert envelope["error"]["code"] == "invalid-input"
