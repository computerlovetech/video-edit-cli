# video-edit-cli

A video-editing tool for AI agents. Your agent gets a headless editing
workbench — inspect, transcribe, cut, master, and package video — plus a
bundled skill that teaches it how to edit well. It works with any coding
agent that supports skills: Claude Code, Codex, Pi, Cursor, Copilot, Amp,
and others.

## Get started

Install the `video-edit-cli` skill into your project with
[skills.sh](https://skills.sh) (it installs into every agent you use):

```sh
npx skills add computerlovetech/video-edit-cli --skill video-edit-cli
```

Then ask your agent to edit a recording. The skill guides the agent through the
whole workflow — including installing the `video-edit-cli` CLI itself
(`uv tool install video-edit-cli`) if it isn't on `PATH`. Only `ffmpeg`/`ffprobe`
must be present separately.

## Examples

Things you can ask your agent once the skill is installed:

> Make highlight clips from this recording in vertical shorts format, with
> matching post captions I can use on LinkedIn and YouTube Shorts. Burn the
> subtitles into the video so it's clearly watchable without sound:
> ./recordings/talk.mp4

> Edit this podcast recording into a publishable episode: cut the false starts
> and long pauses, clean up and master the audio, and give me an MP4 with
> muxed subtitles.

> Here are two camera angles and a separate mic track from the same session —
> sync them and build a rough cut that follows whoever is speaking.

> Inspect this file and tell me what's in it: duration, streams, loudness,
> and whether the audio needs restoration before I publish it.

## How it works

The CLI exposes atomic, non-interactive, project-agnostic subcommands that
inspect and transform media deterministically; the agent plans the edit and
composes the primitives.

Contract:

- Machine-readable JSON on stdout (one result envelope per command), diagnostics on
  stderr, meaningful non-zero exit codes on failure.
- Source media is immutable. Every derived file is new and gets a
  `*.provenance.json` sidecar recording inputs, hashes, tool versions, parameters,
  and the exact tool commands.
- Requires `ffmpeg` and `ffprobe` on PATH; commands fail with the stable error code
  `missing-binary` when absent.

The CLI can also be installed directly: `uv tool install video-edit-cli`. For local
Apple Silicon transcription, install `uv tool install 'video-edit-cli[mlx]'`. FFmpeg
and FFprobe must be installed separately and available on `PATH`.

DeepFilterNet restoration uses the optional `df` extra on Python 3.11–3.12. Run
`video-edit-cli doctor --workflow audio-restoration` before denoising to verify the
complete local Torch, Torchaudio, decoding-backend, and DeepFilterNet import chain.

Usage discovery: `video-edit-cli --help` and `--help` on every subcommand. Inside this
repository, prefix commands with `uv run`.

Example:

```sh
uv run video-edit-cli workspace init --root /tmp/ep1 --source recording.mp4
uv run video-edit-cli probe --input recording.mp4
uv run video-edit-cli filmstrip create --input recording.mp4 \
  --start 60 --end 90 --output /tmp/ep1/analysis/strip.png --workspace /tmp/ep1
```

The companion skill in `skills/video-edit-cli/` teaches agents the editing method;
this package owns the mechanics. Besides skills.sh (see Get started), the skill
also ships inside the package — `video-edit-cli skills install` copies it into
`.claude/skills/` (or `--target <dir>`) — and can be managed with agr:
`agr add computerlovetech/video-edit-cli/video-edit-cli`.
Skills in `skills/` that are not listed in `video_editor.skills.SHIPPED_SKILLS`
(and the matching force-include entries in `pyproject.toml`) are agr-only and do
not ship in the wheel. Tests generate small deterministic fixtures at
runtime (`tests/generate_fixtures.py`); no media is committed.

Quality gates (run from this directory):

```sh
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```
