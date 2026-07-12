# Video Editing Skill Roadmap

## Goal

Build a headless, project-agnostic podcast video-editing skill for AI coding agents. The skill consists of concise instructions and a deterministic local CLI whose atomic commands agents can use as tools. It will be developed inside Ship the Diff and may be extracted after it becomes mature.

The skill should let an agent inspect unfamiliar media, make evidence-based editorial decisions, render edits, and verify its own work. Speech-to-text and audio processing run locally. The agent model itself may be hosted.

This roadmap is the source of truth for development order. Research and architectural rationale live in [RESEARCH-EDITING-PIPELINE.md](RESEARCH-EDITING-PIPELINE.md).

## Development principles

- Each iteration leaves the skill usable at a larger scope.
- `SKILL.md` contains the steps every editing run needs.
- Branch-specific guidance is disclosed through explicit references only when needed.
- Media mechanics live in tested scripts rather than prose or improvised shell commands.
- Each step has a checkable completion criterion.
- Original media is immutable and every edit is reversible.
- Project-specific assets, identity, output profiles, and editorial preferences remain outside the skill.
- Every iteration includes deterministic fixtures and evaluation on real footage.
- The skill is pruned after each iteration to prevent duplication, sediment, and sprawl.
- Later capabilities must not weaken previously reliable paths.

## Iteration 1: Inspect

### Outcome

The agent can point the skill at arbitrary media, determine what it contains, and inspect any relevant time range.

### Capabilities

- Inventory files and streams with `ffprobe`.
- Identify duration, codecs, frame rate, dimensions, channels, and sample rate.
- Extract canonical audio without altering originals.
- Generate lightweight proxy media.
- Generate filmstrips and waveforms for requested ranges.
- Return structured output suitable for agent reasoning.

### Completion criterion

Given unfamiliar fixture media and one real recording, the agent produces an accurate inventory and can inspect any requested range without manually constructing FFmpeg commands.

## Iteration 2: Transcribe

### Outcome

The transcript becomes the primary surface for understanding dialogue while visual inspection remains available on demand.

### Capabilities

- Run word-level speech-to-text locally on Apple Silicon.
- Preserve word timestamps, confidence, and language metadata.
- Produce a detailed machine-readable transcript.
- Produce a compact transcript optimized for agent context.
- Search spoken content and map results back to source time.
- Teach the skill when transcript evidence is insufficient and visual inspection is required.

### Completion criterion

The agent can find spoken passages precisely, inspect their visual context, and relate every transcript selection to valid source timestamps on fixture and real media.

## Iteration 3: Cut

### Outcome

The agent can create and render a non-destructive rough cut of one composed video.

### Capabilities

- Define a semantic edit-plan format.
- Support keeping and removing source ranges.
- Require an editorial reason for every removal.
- Validate timestamps, ordering, overlaps, and source references.
- Compile a valid plan into deterministic FFmpeg operations.
- Render inexpensive previews before full-quality output.
- Preserve the plan and render provenance.

### Completion criterion

The agent can propose, explain, validate, and render a coherent rough cut without changing the source file. Invalid plans fail with actionable structured errors.

## Iteration 4: Review

### Outcome

The agent can inspect its rendered edits and revise defects before presenting the result.

### Capabilities

- Enumerate every edit boundary.
- Generate before-and-after filmstrips for each cut.
- Generate detailed waveform and transcript context around each cut.
- Produce short audio/video previews around boundaries.
- Detect likely clipped words, audio discontinuities, black frames, and invalid transitions.
- Teach the skill a render, inspect, revise loop.

### Completion criterion

Every cut in the rendered fixture and real episode has recorded inspection evidence and passes explicit continuity checks, or is reported as an unresolved defect.

## Iteration 5: Master Audio

### Outcome

The agent can produce clean, consistently mastered podcast audio locally without applying destructive enhancement blindly.

### Capabilities

- Measure noise, clipping, loudness, true peaks, and other useful quality signals.
- Produce a mastering-only baseline.
- Add conservative local speech denoising.
- Apply deterministic equalization, dynamics, limiting, and loudness normalization.
- Generate loudness-matched A/B candidates.
- Record models, parameters, metrics, and processing provenance.
- Disclose stronger restoration guidance only for damaged recordings.

### Completion criterion

The output meets defined loudness and true-peak requirements, retains reviewable alternatives, and passes evaluation on representative clean and degraded recordings without replacing the original.

## Iteration 6: Package the Episode

### Outcome

The agent can turn an approved edit into a publishable long-form episode using an external project profile and assets.

### Capabilities

- Generate and render subtitles from the edited timeline.
- Insert intro, outro, titles, and reusable brand assets.
- Add music with deterministic timing, fades, and speech ducking.
- Define standard preview and master output profiles.
- Validate streams, duration, subtitle timing, loudness, and expected assets in the final render.

### Completion criterion

The agent produces a complete long-form episode that passes all media validation checks without requiring interaction with a graphical editor.

## Iteration 7: Direct Cameras and Make Clips

### Outcome

The skill handles multi-source podcast editing and derives polished vertical clips without weakening the single-video path.

### Capabilities

- Synchronize separate audio and video sources.
- Relate speakers to available camera tracks.
- Select cameras using dialogue and visual evidence.
- Inspect reactions and continuity around switches.
- Find candidate highlights using transcript and visual context.
- Create derived vertical timelines.
- Reframe speakers, apply captions, and render short-form profiles.

### Completion criterion

The agent can produce a coherent multi-camera long-form edit and at least one captioned vertical clip from representative real footage while the single-source regression suite remains green.

## Iteration 8: Package Multi-Format Clip Releases

### Outcome

One approved source range becomes a validated, platform-ready release bundle in both
vertical and horizontal formats. The generic editor produces media and neutral metadata
inputs; project skills supply brand voice and publishing copy.

### Capabilities

- Derive a 9:16 short-form render and a 16:9 standard-video render from the same
  word-aligned editorial selection.
- Support independent crop/reframe decisions per aspect ratio without changing the
  selected argument or clipping its opening and payoff.
- Burn styled subtitles into both renders and also emit matching SRT/VTT files.
- Normalize and validate loudness, true peak, canvas, frame rate, duration, codecs,
  subtitle safe areas, and text timing for every variant.
- Create a deterministic release manifest that groups all derivatives of one clip:
  source range, editorial reason, vertical video, horizontal video, subtitles,
  provenance, validation reports, and project-supplied metadata files.
- Accept project-supplied title, description, episode URL, and social-copy files without
  embedding Ship the Diff or Verbos identity in the `video-edit-cli` package.
- Provide an optional publish handoff manifest suitable for a separate YouTube uploader;
  uploading and external account mutation remain outside the media CLI.

### Completion criterion

Given one approved podcast moment and an external project profile, the agent produces a
release directory containing validated 9:16 and 16:9 videos, burned and sidecar
subtitles, and a manifest that pairs each artifact with project-provided title,
description, and social copy. The workflow is demonstrated on one Ship the Diff episode
and one Verbos episode without introducing either brand into the project-agnostic CLI.

## Cross-session working method

At the start of a session:

1. Read this roadmap and the current iteration's handoff or specification.
2. Inspect the skill, scripts, fixtures, tests, and recent diary entries.
3. Work only within the active iteration unless the roadmap is explicitly revised.

At the end of a session:

1. Record what changed and why.
2. Record exact validation performed and unresolved failures.
3. Update the active iteration's progress artifact.
4. Leave the next session one concrete, bounded starting point.

An iteration advances only when its completion criterion has been demonstrated on deterministic fixtures and representative real footage. Passing unit tests alone is not sufficient.

## Deferred decisions

- Whether some later branches eventually earn separate skills.
- Extraction into a standalone repository or shared skill package.
- Whether experience with real footage justifies replacing the initial transcription or denoising backend.
- Whether the custom edit-plan format eventually needs OpenTimelineIO interchange.
- Whether clip release packaging remains a branch of the video-edit-cli skill or becomes
  a separate orchestration skill once both Ship the Diff and Verbos have used it.
- Whether YouTube upload belongs in a generic publishing plugin, a project-specific
  skill, or a human-approved external automation layer.
