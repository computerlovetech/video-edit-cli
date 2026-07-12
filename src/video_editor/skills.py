"""Locate and install the agent skills bundled with the video-edit-cli package."""

from __future__ import annotations

import shutil
from pathlib import Path

from video_editor.errors import VideoEditorError

# Skills shipped with the CLI. Must match the force-include entries in
# pyproject.toml; repository-only skills are distributed via agr instead.
SHIPPED_SKILLS = ("video-editor",)


def bundled_skills_dir() -> Path:
    """Return the directory holding the skills shipped with this package.

    Installed wheels carry the skills at ``video_editor/skills``; a source
    checkout keeps the canonical copies in the repository-root ``skills/``
    directory instead.
    """
    packaged = Path(__file__).parent / "skills"
    if packaged.is_dir():
        return packaged
    repo_root = Path(__file__).parents[2] / "skills"
    if repo_root.is_dir():
        return repo_root
    raise VideoEditorError(
        "skills-not-found",
        "no bundled skills directory is present in this installation",
    )


def list_skills() -> list[dict[str, str]]:
    root = bundled_skills_dir()
    skills = []
    for name in SHIPPED_SKILLS:
        entry = root / name
        if (entry / "SKILL.md").is_file():
            skills.append({"name": name, "path": str(entry)})
    return skills


def install_skills(target: Path) -> list[dict[str, str]]:
    """Copy every bundled skill into ``target`` (e.g. ``.claude/skills``).

    Existing copies of the same skills are replaced so upgrades of the CLI
    propagate; unrelated skills in the target directory are left untouched.
    """
    installed = []
    for skill in list_skills():
        destination = target / skill["name"]
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(skill["path"], destination)
        installed.append({"name": skill["name"], "path": str(destination.resolve())})
    if not installed:
        raise VideoEditorError(
            "skills-not-found", "the bundled skills directory contains no skills"
        )
    return installed
