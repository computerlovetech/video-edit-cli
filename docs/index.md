# video-edit-cli

A video-editing tool for AI agents. Your agent gets a headless editing
workbench — inspect, transcribe, cut, master, and package video — plus a
bundled [skill](skills.md) that teaches it how to edit well. It works with any
coding agent that supports skills: Claude Code, Codex, Pi, Cursor, Copilot,
Amp, and others.

## Get started

Install the `video-edit-cli` skill into your project with
[skills.sh](https://skills.sh) (it installs into every agent you use):

```sh
npx skills add computerlovetech/video-edit-cli --skill video-edit-cli
```

Then ask your agent to edit a recording. The skill guides the agent through the
whole workflow — including installing the `video-edit-cli` CLI itself
(`uv tool install video-edit-cli`) if it isn't on `PATH`. Only `ffmpeg` and
`ffprobe` must be installed separately.

## Example prompts

A growing collection of prompts that work well. Have a good one? Add it.

> Make clips for YouTube Shorts from this video, with burned-in subtitles:
> https://youtu.be/r1Kh5WssSPg

## Where next

- [Concepts](concepts.md) — workspaces, provenance, result envelopes, edit
  plans, project profiles.
- [Workflows](workflows.md) — recipes for a main edit, a vertical short, audio
  restoration, subtitles, and multi-camera sync.
- [CLI reference](reference.md) — every command and flag.
- [Agent skills](skills.md) — the bundled skills that teach agents the editing
  method.
