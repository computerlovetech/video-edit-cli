---
title: "Workflows: podcast edits, Shorts, multicam, mastering"
description: >-
  Step-by-step command-line recipes — edit a podcast into an episode, cut
  vertical Shorts with subtitles, sync multi-camera shoots, restore and
  master audio.
---

# Workflows

These recipes combine commands into common deliverables. Each recipe runs
`doctor`, sets up a workspace, gathers evidence, acts, and validates. The paths
below assume a workspace at `$WS`.

## Main edit (dialogue-driven rough cut)

To edit a talk or podcast recording from the command line, transcribe it,
author an edit plan from the transcript, then validate, render, and review the
cut:

```sh
video-edit-cli doctor --workflow transcription
video-edit-cli workspace init --root $WS --source recording.mp4

# Evidence
video-edit-cli probe --input recording.mp4
video-edit-cli transcript create --input recording.mp4 \
  --output $WS/analysis/recording.transcript.json --workspace $WS
video-edit-cli transcript pack --transcript $WS/analysis/recording.transcript.json \
  --output $WS/analysis/recording.transcript.txt --workspace $WS

# Author $WS/plans/rough-cut-1.json yourself (see Concepts → Edit plans), then:
video-edit-cli plan validate --plan $WS/plans/rough-cut-1.json
video-edit-cli render preview --plan $WS/plans/rough-cut-1.json \
  --output $WS/previews/rough-cut-1.mp4 --workspace $WS
```

Review every boundary before sharing the result:

```sh
video-edit-cli cuts list --manifest $WS/previews/rough-cut-1.mp4.manifest.json
video-edit-cli cut inspect --manifest $WS/previews/rough-cut-1.mp4.manifest.json \
  --all --output-dir $WS/reports/cut-review \
  --transcript $WS/analysis/recording.transcript.json
```

`cut inspect` gathers frames, a waveform, a mini-preview, transcript context,
and clipped-word checks around each boundary. Fix defects by writing a revised
plan (`parent_plan` set), re-validating, and re-rendering.

## Packaged master (profile, subtitles, final checks)

To produce a final deliverable with subtitles, render against a project
profile, derive SRT/VTT from the render manifest, and validate the output:

```sh
video-edit-cli render master --plan $WS/plans/final.json \
  --profile ./project.yaml --profile-name youtube-1080p \
  --output $WS/renders/episode.mp4 --workspace $WS

video-edit-cli subtitles create \
  --manifest $WS/renders/episode.mp4.manifest.json \
  --transcript $WS/analysis/recording.transcript.json \
  --output-srt $WS/renders/episode.srt --output-vtt $WS/renders/episode.vtt \
  --workspace $WS

# Mux (soft subs) or burn (hard subs)
video-edit-cli subtitles render --input $WS/renders/episode.mp4 \
  --subtitles $WS/renders/episode.srt --mode mux \
  --output $WS/renders/episode.subbed.mp4 --workspace $WS

video-edit-cli output validate --input $WS/renders/episode.subbed.mp4 \
  --profile ./project.yaml --profile-name youtube-1080p --expect-subtitles
```

`output validate` checks streams, canvas, duration, loudness, and subtitles. It
does not check framing or editorial quality. Extract and review frames or
previews for those checks.

Check external assets (intro, outro, music, fonts, images, subtitle files)
before use with `asset inspect --input <path>`.

## Vertical short from a long-form source

To turn a long recording into a vertical 9:16 short from the command line,
choose a range, preview the reframe, derive a vertical plan, and render it.
`short create-plan` never picks highlights — you choose the range (from the
transcript or inspection) and state the editorial reason.

```sh
video-edit-cli doctor --workflow vertical-captioned

# Preview candidate framings for the chosen range
video-edit-cli reframe preview --input recording.mp4 \
  --start 312.4 --end 358.9 --crop 656:0:608:1080 --canvas 1080x1920 \
  --output $WS/previews/short-frame.mp4 --workspace $WS

# Derive an editable vertical plan, then validate/render like any plan
video-edit-cli short create-plan --input recording.mp4 \
  --start 312.4 --end 358.9 --crop 656:0:608:1080 --canvas 1080x1920 \
  --reason "self-contained story about X with a strong hook" \
  --output $WS/plans/short-1.json --workspace $WS

video-edit-cli plan validate --plan $WS/plans/short-1.json
video-edit-cli render preview --plan $WS/plans/short-1.json \
  --output $WS/previews/short-1.mp4 --workspace $WS
```

For captioned shorts, derive subtitles from the short's render manifest with
tight cues (`--max-words` / `--max-chars`) and burn them with
`subtitles render --mode burn`.

## Audio restoration and mastering

To denoise and loudness-normalize audio, extract and analyze it. Then denoise
it with an explicit backend, compare candidates, master the best one, and
attach it to the video:

```sh
video-edit-cli doctor --workflow audio-restoration   # verifies the DF/Torch chain

video-edit-cli audio extract --input recording.mp4 \
  --output $WS/analysis/recording.wav --workspace $WS
video-edit-cli audio analyze --input $WS/analysis/recording.wav

# Denoising is always an explicit choice of backend
video-edit-cli audio denoise --input $WS/analysis/recording.wav \
  --backend deepfilternet --output $WS/analysis/recording.dn.wav --workspace $WS

# Compare candidates loudness-matched before committing
video-edit-cli audio compare --input $WS/analysis/recording.wav \
  --input $WS/analysis/recording.dn.wav --output-dir $WS/reports/ab

# Master the best candidate, then attach it to the video
video-edit-cli audio master --input $WS/analysis/recording.dn.wav \
  --output $WS/analysis/recording.mastered.wav --workspace $WS
video-edit-cli audio replace --video recording.mp4 \
  --audio $WS/analysis/recording.mastered.wav \
  --output $WS/renders/recording.restored.mp4 --workspace $WS
```

`audio master` runs deterministic two-pass loudness normalization (defaults
target speech delivery; override with `--target-lufs`, `--true-peak`, `--lra`).

## Multi-camera / separate-audio sync

To sync two cameras or a separate audio recorder from the command line,
estimate the offset from the audio, review it, and apply it:

```sh
video-edit-cli sync analyze --reference camera-a.mp4 --other mic.wav
```

`sync analyze` only produces evidence — an estimated offset with confidence.
Review it, then apply the approved offset:

```sh
video-edit-cli sync apply --input mic.wav --offset 12.42 \
  --output $WS/analysis/mic.aligned.wav --workspace $WS
```

Give `--output` a `.json` path to write an offset mapping instead of aligned
media. Aligned sources can then appear side by side in one plan's `sources`.

## Cheap inspection at every step

| Need | Command |
|---|---|
| Streams, duration, container metadata | `probe` |
| Small editable copy for fast seeking | `proxy create` |
| One frame at a timestamp | `frame extract` |
| Timestamped contact sheet for a range | `filmstrip create` |
| Audio shape of a range | `waveform create` |
| Watchable low-cost preview of a range | `preview create` |

Use the least costly evidence that answers the question. For dialogue, start
with `probe` and transcripts. Use targeted frames, waveforms, and previews only
when needed.
