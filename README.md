# Video Edit CLI

[![PyPI](https://img.shields.io/pypi/v/video-edit-cli)](https://pypi.org/project/video-edit-cli/)
[![Python](https://img.shields.io/pypi/pyversions/video-edit-cli)](https://pypi.org/project/video-edit-cli/)
[![Tests](https://github.com/computerlovetech/video-edit-cli/actions/workflows/test.yml/badge.svg)](https://github.com/computerlovetech/video-edit-cli/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Turn raw recordings into publish-ready videos with your AI agent. Ask in plain
language to edit a podcast, make YouTube Shorts with burned-in subtitles,
remove silences and false starts, sync multi-camera shoots, or restore and
master audio. The tool is open source, runs locally, and has no watermarks or
per-clip credits.

![An AI coding agent turning a talk into three captioned YouTube Shorts with video-edit-cli](https://raw.githubusercontent.com/computerlovetech/video-edit-cli/main/docs/assets/demo.svg)

We use this tool at [computerlove.tech](https://computerlove.tech) to edit our
video podcasts. We made it open source so your agent can edit yours too.

It works with any coding agent that supports skills:
**Claude Code** · **Codex** · **Cursor** · **GitHub Copilot** · **Pi** · and others.

## Get started

Install the skill into your project with [skills.sh](https://skills.sh):

```sh
npx skills add computerlovetech/video-edit-cli --skill video-edit-cli
```

Then ask your agent to edit a recording:

> Make clips for YouTube Shorts from this video, with burned-in subtitles:
> https://youtu.be/r1Kh5WssSPg

The skill guides the agent through the workflow and installs the CLI when
needed. You need only `ffmpeg` and `ffprobe`.

More prompts that work well: [example prompts](docs/examples.md). Have a good
one? Add it.

## What your agent can do with it

- **Edit a podcast or talk into a publishable episode** — cut false starts,
  retakes, and dead air from the transcript, keeping the conversation intact.
- **Turn a long video into vertical Shorts/Reels** — pick moments from the
  transcript, reframe to 9:16, and burn in styled subtitles.
- **Transcribe and subtitle** — word-level Whisper transcripts, SRT/VTT
  export, muxed or burned-in subtitles.
- **Restore and master audio** — extract, denoise, A/B compare, and
  loudness-normalize for podcast or YouTube delivery.
- **Sync multi-camera and separate-audio shoots** — estimate and apply
  offsets, then cut between angles in one plan.
- **Inspect unknown media** — check streams, durations, frames, filmstrips,
  waveforms, and low-resolution previews before editing.

## How it works

The CLI provides small, fixed commands. The agent gathers evidence from
transcripts, frames, and waveforms. It then writes an **edit plan**: an ordered
keep-list that gives a `reason` for every cut. The CLI validates and renders
the plan:

```json
{
  "plan_id": "rough-cut-1",
  "timeline": [
    {"source": "src-1", "in": 0.5, "out": 42.1, "reason": "keep intro"},
    {"source": "src-1", "in": 55.0, "out": 120.4, "reason": "false start removed at 42.1-55.0"}
  ]
}
```

Every command prints one JSON result on stdout. Commands never change source
media. Each derived file gets a `*.provenance.json` sidecar that records how
the tool made it, so you can trace and reproduce every edit.

```sh
video-edit-cli workspace init --root /tmp/ep1 --source recording.mp4
video-edit-cli probe --input recording.mp4
video-edit-cli filmstrip create --input recording.mp4 \
  --start 60 --end 90 --output /tmp/ep1/analysis/strip.png --workspace /tmp/ep1
```

Install the CLI directly with `uv tool install video-edit-cli`. For Apple
Silicon transcription, run `uv tool install 'video-edit-cli[mlx]'`. Use
`--help` on any subcommand to list its options. Check dependencies with
`video-edit-cli doctor`.

Runs on macOS and Linux. Windows is untested; use WSL.

## Docs

Full documentation: https://computerlovetech.github.io/video-edit-cli/
