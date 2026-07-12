---
name: release
description: >
  Release process for the video-edit-cli package. Handles version bumping
  (major/minor/patch/beta), changelog updates, pre-release quality checks, wheel
  verification (including the bundled agent skills), publishing to PyPI, git tagging,
  and the GitHub Release. Use this skill whenever the user wants to cut a release,
  bump the version, or publish to PyPI — even if they just say "let's ship it".
---

# video-edit-cli Release Process

Releases are published locally with `uv publish` (authenticated via the
`UV_PUBLISH_TOKEN` environment variable), then tagged and mirrored as a GitHub
Release. CI (`test.yml`) is the quality gate but does not publish.

## Before you start

Verify the preconditions. If any fail, stop and tell the user.

1. **Clean working tree** — `git status` shows no uncommitted changes
2. **On `main` and up to date** — `git pull`; releases only come from main
3. **CI green on HEAD** — `gh run list --branch main --limit 1` shows success
4. **Publish token present** — `test -n "$UV_PUBLISH_TOKEN"`

Ask the user what kind of release this is (patch / minor / major / beta). If
they already said, don't ask again.

## Step 1: Figure out what changed

```bash
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

Cross-reference with the `[Unreleased]` section of `CHANGELOG.md`; add any
missing entries under the Keep a Changelog categories (Added / Changed /
Fixed / Removed / Docs).

## Step 2: Run quality checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

Fix any failure before continuing.

## Step 3: Bump the version

The version lives in **two** places; they must match:

1. `pyproject.toml` — `version = "X.Y.Z"`
2. `src/video_editor/__init__.py` — `__version__ = "X.Y.Z"`

Beta convention: `0.2.0` → `0.2.1b1` → `0.2.1b2` → `0.2.1`.

## Step 4: Update the changelog

In `CHANGELOG.md`: rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`,
add a fresh empty `## [Unreleased]` section on top, and review the entries
for user-facing clarity. The release notes are taken from this section.

## Step 5: Build and verify the artifacts

```bash
rm -rf dist && uv build
```

Then verify the wheel — this is the step that catches packaging regressions:

- The `video-edit-cli` executable works from a clean venv:
  `uv venv /tmp/vec-rel && uv pip install -p /tmp/vec-rel/bin/python dist/*.whl`
  then run `--help` and `skills list`.
- **Bundled skills are present**: `unzip -l dist/*.whl | grep video_editor/skills/`
  must show `SKILL.md` and references for every skill in
  `video_editor.skills.SHIPPED_SKILLS` (repo `skills/` dir is the source of truth;
  the force-include entries in `pyproject.toml` do the bundling).
- All JSON schemas are present: `unzip -l dist/*.whl | grep schemas/`.

## Step 6: Commit, tag, publish

Show the user a summary (version, changelog entry, files touched) and get
confirmation before pushing or publishing.

```bash
git add pyproject.toml src/video_editor/__init__.py CHANGELOG.md
git commit -m "release: vX.Y.Z"
git tag vX.Y.Z
git push origin main vX.Y.Z
uv publish
```

If `uv publish` fails mid-upload, it is safe to re-run; PyPI rejects
duplicate files idempotently.

## Step 7: GitHub Release

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --notes "<the X.Y.Z changelog section>"
```

## Step 8: Verify

```bash
uv pip install --no-cache -p /tmp/vec-verify/bin/python video-edit-cli==X.Y.Z --index-url https://pypi.org/simple
```

(Create the venv first; PyPI's simple index can lag ~1–2 minutes after upload —
retry rather than assuming failure.) Confirm `video-edit-cli skills install`
works from the fresh install, then share the links:

- PyPI: https://pypi.org/project/video-edit-cli/X.Y.Z/
- GitHub Release: `gh release view vX.Y.Z --json url`

## If something goes wrong after tagging

PyPI versions are immutable — a broken published version cannot be replaced.
Fix forward with a new patch release. If the tag was pushed but nothing was
published, you may delete and re-create it (`git tag -d vX.Y.Z && git push
origin :refs/tags/vX.Y.Z`) — confirm with the user first.
