from __future__ import annotations

from pathlib import Path

from conftest import run_cli
from video_editor import skills


def test_list_reports_every_shipped_skill() -> None:
    code, envelope = run_cli(["skills", "list"])
    assert code == 0
    names = [entry["name"] for entry in envelope["data"]["skills"]]
    assert names == list(skills.SHIPPED_SKILLS)


def test_install_copies_skills_and_replaces_stale_copies(tmp_path: Path) -> None:
    target = tmp_path / ".claude" / "skills"
    stale = target / "video-edit-cli"
    stale.mkdir(parents=True)
    (stale / "obsolete.md").write_text("stale")

    code, envelope = run_cli(["skills", "install", "--target", str(target)])
    assert code == 0
    installed = envelope["data"]["installed"]
    assert [entry["name"] for entry in installed] == list(skills.SHIPPED_SKILLS)
    assert (target / "video-edit-cli" / "SKILL.md").is_file()
    assert (target / "video-edit-cli" / "references").is_dir()
    assert not (target / "video-edit-cli" / "obsolete.md").exists()


def test_shipped_skills_match_wheel_force_include() -> None:
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text()
    for name in skills.SHIPPED_SKILLS:
        assert f'"skills/{name}" = "video_editor/skills/{name}"' in pyproject
