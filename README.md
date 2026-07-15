# Video Edit CLI

[![PyPI](https://img.shields.io/pypi/v/video-edit-cli)](https://pypi.org/project/video-edit-cli/)
[![Python](https://img.shields.io/pypi/pyversions/video-edit-cli)](https://pypi.org/project/video-edit-cli/)
[![Tests](https://github.com/computerlovetech/video-edit-cli/actions/workflows/test.yml/badge.svg)](https://github.com/computerlovetech/video-edit-cli/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Turn raw recordings into published videos with your AI agent. Edit a podcast
into an episode, cut YouTube Shorts with burned-in subtitles, remove silences
and false starts, sync multi-camera shoots, restore and master audio — by
asking your coding agent in plain language. Open source, runs locally, no
watermarks, no per-clip credits.

![An AI coding agent turning a talk into three captioned YouTube Shorts with video-edit-cli](https://raw.githubusercontent.com/computerlovetech/video-edit-cli/main/docs/assets/demo.svg)

This is the tool we use internally at [computerlove.tech](https://computerlove.tech)
to edit our video podcast content — we open-sourced it so your agent can edit
yours too.

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
- **Inspect unknown media** — streams, durations, frames, filmstrips,
  waveforms, and cheap previews before touching anything.

## How it works

The agent edits like an editor, not a filter. The CLI exposes atomic,
deterministic subcommands; the agent gathers evidence (transcript, frames,
waveforms), authors an **edit plan** — an ordered keep-list where every cut
carries a written `reason` — and the CLI validates and renders it:

```json
{
  "plan_id": "rough-cut-1",
  "timeline": [
    {"source": "src-1", "in": 0.5, "out": 42.1, "reason": "keep intro"},
    {"source": "src-1", "in": 55.0, "out": 120.4, "reason": "false start removed at 42.1-55.0"}
  ]
}
```

Every command prints one JSON result on stdout, source media is immutable, and
every derived file gets a `*.provenance.json` sidecar recording exactly how it
was made — so every edit is auditable and reproducible.

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

## How it compares

|  | video-edit-cli | Opus Clip / Klap / Vizard | Descript | auto-editor |
|---|---|---|---|---|
| Price | Free, open source | $15–29/mo + per-clip credits | $16–24/mo | Free |
| Watermarks | Never | On free tiers | On free tier | Never |
| Runs locally / footage stays private | ✅ | ❌ uploaded to their cloud | ❌ | ✅ |
| Explains every cut with a written reason | ✅ | ❌ black-box "virality score" | ❌ | ❌ |
| Transcript-driven editing | ✅ | ✅ | ✅ | ❌ threshold only |
| Shorts with reframing + burned-in captions | ✅ | ✅ | ✅ | ❌ |
| Audio mastering, multicam sync, QC | ✅ | ❌ | Partial | ❌ |
| Drives your existing AI coding agent | ✅ | ❌ | ❌ | ❌ |
| Auditable & reproducible (provenance sidecars) | ✅ | ❌ | ❌ | ❌ |

**vs. hosted clip apps (Opus Clip, Vizard, Klap, Descript)** — those are
subscription apps with per-clip credits and watermarked free tiers.
video-edit-cli is free and runs locally: your footage never leaves your
machine, and the agent explains every cut instead of a black-box score.

**vs. auto-editor / jumpcutter** — those remove silence with a threshold.
video-edit-cli covers the whole editorial job: transcript-driven cuts, shorts
with reframing and captions, audio mastering, multicam sync, subtitles, and
final QC — with a skill that teaches the agent when to use each.

**vs. FFmpeg wrappers and video MCP servers** — most give an agent raw
commands and hope. video-edit-cli adds the missing method: evidence before
edits, validated plans, cut-by-cut review, provenance on every artifact, and
stable JSON results an agent can actually parse.

## Docs

Full documentation: https://computerlovetech.github.io/video-edit-cli/
