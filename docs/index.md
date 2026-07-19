---
title: Video editing for AI agents
description: >-
  Open-source CLI that lets AI coding agents edit video — podcasts, YouTube
  Shorts with burned-in subtitles, multicam sync, audio mastering. Runs
  locally with Claude Code, Codex, Cursor, and more.
---

# video-edit-cli

Turn raw recordings into publish-ready videos with your AI agent. video-edit-cli
lets your agent inspect, transcribe, cut, master, and package video. Its bundled
[skill](skills.md) teaches the agent how to edit podcasts, make YouTube Shorts
with burned-in subtitles, sync multi-camera shoots, and restore audio. It is
open source, runs locally, and has no watermarks or per-clip credits.

It works with any coding agent that supports skills: Claude Code, Codex, Pi,
Cursor, Copilot, Amp, and others.

## Get started

Install the `video-edit-cli` skill into your project with
[skills.sh](https://skills.sh) (it installs into every agent you use):

```sh
npx skills add computerlovetech/video-edit-cli --skill video-edit-cli
```

Then ask your agent to edit a recording. The skill guides the agent through the
workflow, including installing the `video-edit-cli` CLI
(`uv tool install video-edit-cli`) if it isn't on `PATH`. Only `ffmpeg` and
`ffprobe` must be installed separately.

## Where next

- [Example prompts](examples.md) — prompts that work well.
- [Concepts](concepts.md) — workspaces, provenance, result envelopes, edit
  plans, project profiles.
- [Workflows](workflows.md) — recipes for a main edit, a vertical short, audio
  restoration, subtitles, and multi-camera sync.
- [CLI reference](reference.md) — every command and flag.
- [Agent skills](skills.md) — the bundled skills that teach agents the editing
  method.
