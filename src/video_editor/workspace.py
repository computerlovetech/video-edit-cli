"""Workspace: organized directories plus a manifest of immutable sources and artifacts."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from video_editor import SCHEMA_VERSION, schemas
from video_editor.errors import InvalidInputError
from video_editor.provenance import sha256_file, utc_now

SUBDIRS = (
    "sources",
    "analysis",
    "proxies",
    "plans",
    "previews",
    "renders",
    "reports",
)


def manifest_path(root: Path) -> Path:
    return root / "workspace.json"


def load(root: Path) -> dict[str, Any]:
    path = manifest_path(root)
    if not path.is_file():
        raise InvalidInputError(f"no workspace manifest at {path}")
    manifest: dict[str, Any] = json.loads(path.read_text())
    schemas.validate(manifest, "workspace.schema.json")
    return manifest


def save(root: Path, manifest: dict[str, Any]) -> None:
    schemas.validate(manifest, "workspace.schema.json")
    manifest_path(root).write_text(json.dumps(manifest, indent=2) + "\n")


def init(
    root: Path, sources: list[Path], roles: list[str] | None = None
) -> dict[str, Any]:
    """Create workspace directories and register sources without modifying them."""
    if manifest_path(root).exists():
        raise InvalidInputError(f"workspace already exists at {root}")
    role_list = roles or []
    if role_list and len(role_list) != len(sources):
        raise InvalidInputError("--role count must match --source count when provided")

    root.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (root / sub).mkdir(exist_ok=True)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "workspace_id": uuid.uuid4().hex[:12],
        "created_at": utc_now(),
        "sources": [],
        "artifacts": [],
    }
    for index, source in enumerate(sources):
        source = source.resolve()
        if not source.is_file():
            raise InvalidInputError(f"source file not found: {source}")
        source_id = f"src-{index + 1}"
        manifest["sources"].append(
            {
                "id": source_id,
                "path": str(source),
                "sha256": sha256_file(source),
                "role": role_list[index] if role_list else None,
                "registered_at": utc_now(),
            }
        )
        link = root / "sources" / f"{source_id}{source.suffix}"
        if not link.exists():
            link.symlink_to(source)
    save(root, manifest)
    return manifest


def register_artifact(root: Path, path: Path, kind: str, command: str) -> None:
    manifest = load(root)
    manifest["artifacts"].append(
        {
            "path": str(path.resolve()),
            "kind": kind,
            "command": command,
            "created_at": utc_now(),
        }
    )
    save(root, manifest)


def resolve_source(root: Path, ref: str) -> Path:
    """Resolve a source id from the manifest to its immutable path."""
    manifest = load(root)
    for record in manifest["sources"]:
        if record["id"] == ref:
            return Path(record["path"])
    known = ", ".join(record["id"] for record in manifest["sources"])
    raise InvalidInputError(f"unknown source id '{ref}' (known: {known or 'none'})")
