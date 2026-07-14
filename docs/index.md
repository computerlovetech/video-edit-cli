# video-edit-cli

A video-editing tool for AI agents. Your agent gets a headless editing
workbench — inspect, transcribe, cut, master, and package video — plus a
bundled [skill](skills.md) that teaches it how to edit well.

## Get started

Install the `video-editor` skill into your project with
[skills.sh](https://skills.sh):

```sh
npx skills add computerlovetech/video-edit-cli --skill video-editor
```

Then ask your agent to edit a recording. The skill guides the agent through the
whole workflow — including installing the `video-edit-cli` CLI itself
(`uv tool install video-edit-cli`) if it isn't on `PATH`. Only `ffmpeg` and
`ffprobe` must be installed separately.

The rest of this page covers the CLI directly: its contract, manual
installation, and a quickstart for driving it yourself.

## The contract

One `video-edit-cli` binary exposes atomic, non-interactive, project-agnostic
subcommands that inspect and transform media deterministically. The agent (or
you) plans the edit; the CLI supplies the mechanics.

Every command follows the same rules:

- **One JSON result envelope on stdout** per invocation; diagnostics go to
  stderr; failures exit non-zero with a stable error code. See
  [Concepts → Result envelope](concepts.md#result-envelope).
- **Source media is immutable.** Commands never modify inputs. Every derived
  file is new and gets a `*.provenance.json` sidecar recording inputs, hashes,
  tool versions, parameters, and the exact ffmpeg commands that produced it.
- **Nothing is implicit.** No command picks highlights, chooses a denoiser, or
  discovers configuration. Editorial judgement and project identity come from
  the caller — via edit plans and explicit
  [project profiles](concepts.md#project-profiles).

## Installation

Install the base CLI as a tool:

```sh
uv tool install video-edit-cli
```

Optional extras:

```sh
# Local transcription on Apple Silicon (mlx-whisper)
uv tool install 'video-edit-cli[mlx]'

# DeepFilterNet speech denoising (Python 3.11–3.12 only)
uv tool install 'video-edit-cli[df]'
```

`ffmpeg` and `ffprobe` must be installed separately and available on `PATH`;
commands fail with the stable error code `missing-binary` when they are absent.

Verify your environment before starting work:

```sh
video-edit-cli doctor                              # base checks: ffmpeg, ffprobe
video-edit-cli doctor --workflow transcription     # + transcription backend
video-edit-cli doctor --workflow audio-restoration # + Torch/DeepFilterNet chain
video-edit-cli doctor --workflow vertical-captioned
```

## Quickstart

```sh
# 1. Create a workspace and register the immutable source
video-edit-cli workspace init --root /tmp/ep1 --source recording.mp4

# 2. Inspect the media
video-edit-cli probe --input recording.mp4

# 3. Gather visual evidence for a range
video-edit-cli filmstrip create --input recording.mp4 \
  --start 60 --end 90 --output /tmp/ep1/analysis/strip.png --workspace /tmp/ep1

# 4. Transcribe (Apple Silicon, requires the mlx extra)
video-edit-cli transcript create --input recording.mp4 \
  --output /tmp/ep1/transcripts/recording.json --workspace /tmp/ep1

# 5. Author an edit-plan JSON yourself, then validate and render it
video-edit-cli plan validate --plan /tmp/ep1/plans/main.json
video-edit-cli render preview --plan /tmp/ep1/plans/main.json \
  --output /tmp/ep1/renders/preview.mp4 --workspace /tmp/ep1
```

Every command prints a JSON envelope, so results compose in scripts:

```sh
video-edit-cli probe --input recording.mp4 | jq '.data.format.duration'
```

Usage discovery is built in: `video-edit-cli --help` and `--help` on every
subcommand are the authoritative surface. The
[CLI reference](reference.md) mirrors them with context and examples.

## Where next

- [Concepts](concepts.md) — workspaces, provenance, result envelopes, edit
  plans, project profiles.
- [Workflows](workflows.md) — recipes for a main edit, a vertical short, audio
  restoration, subtitles, and multi-camera sync.
- [CLI reference](reference.md) — every command and flag.
- [Agent skills](skills.md) — the bundled skills that teach agents the editing
  method.
