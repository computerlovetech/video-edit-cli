# Video Edit CLI

[![PyPI](https://img.shields.io/pypi/v/video-edit-cli)](https://pypi.org/project/video-edit-cli/)
[![Python](https://img.shields.io/pypi/pyversions/video-edit-cli)](https://pypi.org/project/video-edit-cli/)
[![Tests](https://github.com/computerlovetech/video-edit-cli/actions/workflows/test.yml/badge.svg)](https://github.com/computerlovetech/video-edit-cli/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A video-editing tool for AI agents. Your agent gets a headless editing
workbench — inspect, transcribe, cut, master, and package video — plus a
bundled skill that teaches it how to edit well.

Works with any coding agent that supports skills:
**Claude Code** · **Codex** · **Cursor** · **GitHub Copilot** · **Pi** · and others.

## Get started

Install the skill into your project with [skills.sh](https://skills.sh):

```sh
npx skills add computerlovetech/video-edit-cli --skill video-edit-cli
```

Then ask your agent to edit a recording:

> Make clips for YouTube Shorts from this video, with burned-in subtitles:
> https://youtu.be/r1Kh5WssSPg

That's it. The skill guides the agent through the whole workflow, including
installing the CLI itself. Only `ffmpeg`/`ffprobe` must be present.

More prompts that work well: [example prompts](docs/examples.md). Have a good
one? Add it.

## How it works

The CLI exposes atomic, deterministic subcommands; the agent plans the edit
and composes the primitives. Every command prints one JSON result on stdout,
source media is immutable, and every derived file gets a `*.provenance.json`
sidecar recording exactly how it was made.

```sh
video-edit-cli workspace init --root /tmp/ep1 --source recording.mp4
video-edit-cli probe --input recording.mp4
video-edit-cli filmstrip create --input recording.mp4 \
  --start 60 --end 90 --output /tmp/ep1/analysis/strip.png --workspace /tmp/ep1
```

Direct install: `uv tool install video-edit-cli` (Apple Silicon transcription:
`uv tool install 'video-edit-cli[mlx]'`). Discover the full command surface
with `--help` on any subcommand, and check dependencies with
`video-edit-cli doctor`.

Runs on macOS and Linux. Windows is untested; use WSL.

## Docs

Full documentation: https://computerlovetech.github.io/video-edit-cli/
