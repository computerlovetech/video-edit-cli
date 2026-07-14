---
title: CLI reference
description: >-
  Every video-edit-cli command with flags and JSON output — probe, transcribe,
  plan, render, subtitles, audio mastering, multicam sync, workspace, and
  skills management.
---

# CLI reference

Every command prints one JSON [result envelope](concepts.md#result-envelope) on
stdout and exits non-zero with a stable error code on failure.
`video-edit-cli --help` (and `--help` on every subcommand) is the authoritative
surface; this page mirrors it with context.

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
Verify your environment with [`doctor`](#doctor) before starting work.

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

## Conventions

Conventions used by many commands:

- `--workspace WORKSPACE` — optional workspace root; records the derived
  artifact in `workspace.json`. Never required.
- Commands that create files take an explicit `--output` (or `--output-dir`)
  and never overwrite source media.
- Times and durations are seconds (fractions allowed); ranges are
  `--start`/`--end` in source time.

---

## Environment

### `doctor`

Check local dependencies for an editing workflow.

```sh
video-edit-cli doctor [--workflow {base,transcription,vertical-captioned,audio-restoration}]
```

| Option | Description |
|---|---|
| `--workflow` | Which dependency chain to verify (default `base`: ffmpeg + ffprobe). `transcription` adds the local Whisper backend; `audio-restoration` verifies the full Torch/Torchaudio/DeepFilterNet import chain; `vertical-captioned` covers the short-form pipeline. |

Run the matching workflow check before expensive work; resolve failures first.

---

## Workspace

### `workspace init`

Create a [workspace](concepts.md#workspaces) and register immutable sources.

```sh
video-edit-cli workspace init --root ROOT --source SOURCE [--source SOURCE ...] [--role ROLE ...]
```

| Option | Description |
|---|---|
| `--root` | Directory to create the workspace in |
| `--source` | Source media path (repeatable) |
| `--role` | Role label per source, in `--source` order (e.g. `camera-a`, `mic-guest`) |

Writes `workspace.json` with each source's path, SHA-256 hash, and id
(`src-1`, `src-2`, …), and creates the standard subdirectories.

---

## Inspection

### `probe`

Inspect streams and container metadata.

```sh
video-edit-cli probe --input INPUT
```

| Option | Description |
|---|---|
| `--input` | Path to the media file |

### `proxy create`

Create a low-resolution proxy for cheap seeking and review.

```sh
video-edit-cli proxy create --input INPUT --output OUTPUT [--height HEIGHT] [--workspace WS]
```

| Option | Description |
|---|---|
| `--input` | Path to the source media file |
| `--output` | Path for the new derived file |
| `--height` | Proxy height in pixels |

### `frame extract`

Extract one frame at a source time.

```sh
video-edit-cli frame extract --input INPUT --output OUTPUT --time TIME [--workspace WS]
```

| Option | Description |
|---|---|
| `--time` | Source time in seconds |

### `filmstrip create`

Create a timestamped contact sheet for a range.

```sh
video-edit-cli filmstrip create --input INPUT --output OUTPUT \
  --start START --end END [--columns COLUMNS] [--frames FRAMES] [--workspace WS]
```

| Option | Description |
|---|---|
| `--start` / `--end` | Range in seconds |
| `--columns` | Tiles per row |
| `--frames` | Frames to sample |

### `waveform create`

Render a waveform image for a range.

```sh
video-edit-cli waveform create --input INPUT --output OUTPUT --start START --end END [--workspace WS]
```

### `preview create`

Render a short low-cost preview of a range.

```sh
video-edit-cli preview create --input INPUT --output OUTPUT --start START --end END [--workspace WS]
```

---

## Audio

### `audio extract`

Extract lossless canonical WAV audio.

```sh
video-edit-cli audio extract --input INPUT --output OUTPUT [--workspace WS]
```

### `audio analyze`

Measure loudness, peaks, clipping, silence, and bandwidth.

```sh
video-edit-cli audio analyze --input INPUT
```

### `audio master`

Deterministic mastering with two-pass loudness normalization.

```sh
video-edit-cli audio master --input INPUT --output OUTPUT \
  [--target-lufs TARGET] [--true-peak DBTP] [--lra LRA] \
  [--highpass HZ] [--no-compressor] [--workspace WS]
```

| Option | Description |
|---|---|
| `--target-lufs` | Integrated loudness target |
| `--true-peak` | True-peak ceiling in dBTP |
| `--lra` | Loudness range target |
| `--highpass` | Rumble highpass frequency in Hz |
| `--no-compressor` | Skip the gentle speech compressor |

### `audio denoise`

Run one explicitly selected local denoising backend. Denoising is never applied
implicitly.

```sh
video-edit-cli audio denoise --input INPUT --output OUTPUT --backend deepfilternet [--workspace WS]
```

| Option | Description |
|---|---|
| `--backend` | Denoising backend; currently `deepfilternet` (requires the `df` extra, Python 3.11–3.12) |

Run `doctor --workflow audio-restoration` first.

### `audio compare`

Produce loudness-matched A/B artifacts and metrics for candidate audio files.

```sh
video-edit-cli audio compare --input A.wav --input B.wav --output-dir DIR \
  [--match-lufs LUFS] [--start START] [--duration SECONDS]
```

| Option | Description |
|---|---|
| `--input` | Candidate audio (repeat 2+ times) |
| `--output-dir` | Directory for samples and the report |
| `--match-lufs` | Loudness to match excerpts to |
| `--start` / `--duration` | Excerpt to compare |

### `audio replace`

Replace a video's audio stream while stream-copying its video.

```sh
video-edit-cli audio replace --video VIDEO --audio AUDIO --output OUTPUT \
  [--audio-codec CODEC] [--audio-bitrate BITRATE] \
  [--duration-tolerance SECONDS] [--workspace WS]
```

| Option | Description |
|---|---|
| `--video` | Video whose video stream is kept |
| `--audio` | Replacement audio input |
| `--duration-tolerance` | Maximum allowed audio/video duration difference in seconds |

---

## Transcription

### `transcript create`

Transcribe with a local backend and write detailed word-level JSON (the
authoritative transcript).

```sh
video-edit-cli transcript create --input INPUT --output OUTPUT \
  [--backend {mlx-whisper,fixture}] [--model MODEL] [--language LANG] \
  [--fixture FIXTURE] [--source-id ID] [--workspace WS]
```

| Option | Description |
|---|---|
| `--backend` | Transcription backend; `fixture` replays a prepared raw JSON (tests/dev) |
| `--model` | Backend model name |
| `--language` | Spoken language hint (e.g. `en`, `da`) |
| `--fixture` | Raw transcription JSON for `--backend fixture` |
| `--source-id` | Workspace source id to record in the transcript |

`mlx-whisper` requires the `mlx` extra (Apple Silicon).

### `transcript pack`

Derive the compact agent-readable text view from an authoritative transcript.

```sh
video-edit-cli transcript pack --transcript TRANSCRIPT --output OUTPUT [--workspace WS]
```

### `transcript search`

Find time-aligned matches for a spoken phrase.

```sh
video-edit-cli transcript search --transcript TRANSCRIPT --query QUERY [--max-results N]
```

---

## Plans and rendering

### `plan validate`

Validate a plan's schema, references, and ranges against the real media. See
[Concepts → Edit plans](concepts.md#edit-plans).

```sh
video-edit-cli plan validate --plan PLAN
```

### `render preview`

Render a plan with the low-cost preview profile (360p default). Also writes
`<output>.manifest.json` mapping output boundaries to source times.

```sh
video-edit-cli render preview --plan PLAN --output OUTPUT [--height HEIGHT] [--workspace WS]
```

### `render master`

Render a plan using a named profile from an external
[project profile](concepts.md#project-profiles) YAML.

```sh
video-edit-cli render master --plan PLAN --profile PROFILE.yaml \
  --profile-name NAME --output OUTPUT [--workspace WS]
```

---

## Cut review

### `cuts list`

Enumerate cut boundaries from a render manifest.

```sh
video-edit-cli cuts list --manifest MANIFEST
```

### `cut inspect`

Gather frames, waveform, preview, transcript context, and checks around one cut
(or every cut).

```sh
video-edit-cli cut inspect --manifest MANIFEST (--cut INDEX | --all) \
  --output-dir DIR [--window SECONDS] [--transcript TRANSCRIPT]
```

| Option | Description |
|---|---|
| `--cut` | Zero-based cut index from `cuts list` |
| `--all` | Inspect every cut in the manifest |
| `--window` | Seconds of context on each side |
| `--transcript` | Source transcript JSON for clipped-word checks |

---

## Subtitles

### `subtitles create`

Derive SRT + WebVTT from source transcripts mapped through a render manifest.

```sh
video-edit-cli subtitles create --manifest MANIFEST --transcript TRANSCRIPT \
  --output-srt OUT.srt --output-vtt OUT.vtt \
  [--max-words N] [--max-chars N] [--max-duration SECONDS] [--workspace WS]
```

| Option | Description |
|---|---|
| `--transcript` | Source transcript JSON (repeatable, one per source) |
| `--max-words` / `--max-chars` | Cue limits for short-form reflow |
| `--max-duration` | Maximum approximate cue duration in seconds |

### `subtitles render`

Mux (soft) or burn (hard) subtitles into a video.

```sh
video-edit-cli subtitles render --input VIDEO --subtitles SUBS --output OUTPUT \
  [--mode {mux,burn}] [--font NAME] [--font-size UNITS] \
  [--primary-color ASS] [--outline-color ASS] [--outline-width UNITS] \
  [--shadow UNITS] [--alignment 1-9] [--margin-v UNITS] [--workspace WS]
```

| Option | Description |
|---|---|
| `--subtitles` | SRT, VTT, or ASS path |
| `--mode` | `mux` (subtitle stream) or `burn` (pixels) |
| `--font-size` | Burn mode, in libass script units — not output pixels (SRT/VTT commonly use a 288-unit-high script canvas) |
| `--primary-color` / `--outline-color` | Burn mode ASS colors, e.g. `&H00FFFFFF` |
| `--alignment` | ASS alignment 1–9 (2 = bottom center) |
| `--margin-v` | Burn mode vertical margin in ASS script units; 35–50 suits lower-third captions |

---

## Assets and output

### `asset inspect`

Validate an intro, outro, music, font, image, or subtitle asset before use.

```sh
video-edit-cli asset inspect --input INPUT
```

### `output validate`

Technical checks only — streams, canvas, duration, loudness, subtitles. Framing
and editorial quality need human/agent review.

```sh
video-edit-cli output validate --input INPUT \
  [--profile PROFILE.yaml] [--profile-name NAME] \
  [--expect-duration SECONDS] [--expect-canvas WIDTHxHEIGHT] \
  [--duration-tolerance SECONDS] [--loudness-tolerance LU] \
  [--expect-subtitles] [--subtitles SUBS]
```

| Option | Description |
|---|---|
| `--expect-canvas` | Expected `WIDTHxHEIGHT` without requiring a profile |
| `--expect-subtitles` | Require a subtitle stream |
| `--subtitles` | Subtitle file to check against the output duration |

---

## Synchronization

### `sync analyze`

Estimate the audio offset between two sources. Produces evidence only — it
changes nothing.

```sh
video-edit-cli sync analyze --reference REFERENCE --other OTHER [--max-offset SECONDS]
```

### `sync apply`

Create an aligned derivative (or a `.json` offset mapping) from an approved
offset.

```sh
video-edit-cli sync apply --input INPUT --offset SECONDS --output OUTPUT [--workspace WS]
```

| Option | Description |
|---|---|
| `--output` | Aligned media path, or a `.json` path for mapping metadata only |

---

## Short-form

### `reframe preview`

Preview an explicit crop scaled onto a canvas.

```sh
video-edit-cli reframe preview --input INPUT --output OUTPUT \
  --start START --end END --crop X:Y:WIDTH:HEIGHT --canvas WIDTHxHEIGHT [--workspace WS]
```

| Option | Description |
|---|---|
| `--crop` | `x:y:width:height` in source pixels |
| `--canvas` | Output canvas `WIDTHxHEIGHT` |

### `short create-plan`

Derive an editable vertical plan from an explicit source range. You choose the
range — this command never picks highlights.

```sh
video-edit-cli short create-plan --input INPUT --start START --end END \
  --reason REASON --output PLAN.json \
  [--source-id ID] [--canvas WIDTHxHEIGHT] [--crop X:Y:W:H] \
  [--parent-plan ID] [--created-by NAME] [--workspace WS]
```

| Option | Description |
|---|---|
| `--reason` | Editorial reason for choosing this range (required) |
| `--parent-plan` | Plan id this short derives from |
| `--created-by` | Authoring agent identifier |

---

## Agent skills

### `skills list`

List the [skills bundled](skills.md) with the CLI.

```sh
video-edit-cli skills list
```

### `skills install`

Copy the bundled skills into an agent skills directory.

```sh
video-edit-cli skills install [--target DIR]
```

| Option | Description |
|---|---|
| `--target` | Skills directory to install into (default `.claude/skills`) |
