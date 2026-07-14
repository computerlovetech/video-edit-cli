---
name: video-editor
description: Edit, inspect, transcribe, cut, master, or package video and audio media with the headless `video-edit-cli` CLI. Use when the user asks to edit a recording, cut a video, inspect unfamiliar media, extract audio, preview a range, synchronize cameras, make a vertical clip, or produce podcast/episode deliverables.
---

You are the editor; the `video-edit-cli` CLI is your workbench. It exposes atomic,
deterministic primitives that print one JSON result on stdout. You form the
editorial plan yourself — no command decides what to keep, remove, or highlight.

Run `video-edit-cli --help` (and `--help` on any subcommand) for the authoritative
command surface; inside this repository run it as `uv run video-edit-cli …`.

## Invariants (hold for every task)

- Source media is immutable. Never overwrite, re-encode in place, or delete an
  original. Every derived file is new and keeps its `*.provenance.json` sidecar.
- Evidence before edits: never act on a range you have not inspected through
  metadata, transcript, frames, waveform, or preview.
- Validate before rendering; preview before mastering when edits are material.
- Prefer the cheapest sufficient evidence: `probe` and transcript first for
  dialogue; targeted visual/audio inspection only where a decision needs it.

## Method

1. **Establish the outcome.** Restate what deliverable is requested and what
   media exists. Done when you can name the requested outputs and every source
   file involved.
2. **Preflight the workflow.** Run `video-edit-cli doctor --workflow base`, or
   use `transcription` / `vertical-captioned` when those capabilities apply.
   Resolve failed dependency checks before expensive work.
3. **Set up a workspace.** Read [references/workspace.md](references/workspace.md),
   then `video-edit-cli workspace init`. Done when `workspace.json` lists every
   source with its hash.
4. **Inspect the media.** `probe` every source; gather audio, proxies, frames,
   filmstrips, waveforms, or range previews as decisions require. For dialogue
   media read [references/transcription.md](references/transcription.md) and
   transcribe first. Done when you know each source's duration, streams, and
   content well enough to justify the plan you are about to form.
5. **Plan and render.** Read [references/edit-plan.md](references/edit-plan.md)
   before creating or modifying a plan; author the plan yourself, validate it,
   and render a preview. Done when the validated plan renders and its manifest
   exists.
6. **Review and revise.** Read [references/cut-review.md](references/cut-review.md);
   inspect every boundary of any render you produced. Done when each cut passes
   or its defect is fixed or explicitly reported.
7. **Finish the deliverable.** Done when every requested output passes technical
   validation and the required visual/editorial review. `output validate` does
   not inspect framing or editorial quality; report those reviews separately.

## Branch references (read when the condition applies)

- Audio cleanup/mastering requested, or analysis finds degraded speech →
  [references/audio-restoration.md](references/audio-restoration.md)
- Packaged deliverable (project profile, subtitles, assets, music, master
  render) → [references/subtitles-and-assets.md](references/subtitles-and-assets.md)
- Multiple synchronized visual/audio sources →
  [references/multicamera.md](references/multicamera.md)
- Vertical or short-form deliverable →
  [references/vertical-video.md](references/vertical-video.md)
