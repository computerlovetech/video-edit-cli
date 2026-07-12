# Research on the Editing Pipeline

## Purpose

Ship the Diff needs an automated pipeline that can turn arbitrary podcast recordings into polished long-form video, mastered audio, subtitles, and short social clips. The initial implementation will live in this repository. If the pipeline becomes mature and reusable, it can be extracted later.

The editing agent may use a hosted model such as Claude or Codex. Speech-to-text and audio enhancement should run locally on an Apple Silicon Mac. Original media must remain untouched.

## Central finding

An agent should not consume an entire long video as an undifferentiated stream. It should work from compact, time-aligned representations and request visual evidence only when it needs it.

For dialogue-heavy podcasts, the transcript is the primary editing surface, but it is not sufficient on its own. Visual inspection is needed for reactions, gestures, camera selection, reframing, demonstrations, continuity, and quality control.

The practical pattern is:

```text
ingest -> analyze -> transcribe -> reason -> edit plan -> timeline -> render -> inspect -> revise
```

The language model makes semantic editorial decisions. Deterministic local tools handle synchronization, frame-accurate cuts, media transforms, validation, and rendering.

## What current agentic video systems do

### Transcript-first, visuals on demand

The clearest practical reference is [Video Use](https://github.com/browser-use/video-use), an open-source system designed for coding agents such as Claude Code and Codex. It packs word-level transcripts into a compact text artifact and exposes a `timeline_view` that generates a visual composite containing a filmstrip, waveform, word labels, and candidate cut points for a requested time range.

The agent does not watch the complete video. It reads the transcript, requests visual context around ambiguous decisions, emits an edit decision list, renders, and then inspects the result around cut boundaries.

This resembles how a coding agent navigates a codebase: search broadly, inspect a relevant region, make a constrained change, and verify the outcome.

### Active perception beats indiscriminate frame sampling

[VideoAgent](https://arxiv.org/abs/2403.10517) treats long-video understanding as an iterative search problem. The language model decides what information is missing and uses visual-language and retrieval tools to find relevant frames. In its experiments, it used roughly eight or nine selected frames on average. More uniformly sampled frames did not necessarily improve results because irrelevant context could distract the model.

The implication for editing is that visual access should be query-driven. The agent should be able to ask questions such as:

- Show the speakers around this interruption.
- Compare these two takes.
- Is the guest visibly reacting here?
- Which camera is usable during this range?
- Inspect two seconds on either side of every proposed cut.

### Multimodal understanding matters

[HIVE](https://aclanthology.org/2025.emnlp-industry.185/) reports that transcript-only editing misses facial expressions, gestures, actions, and other visual context. It also found that decomposing editing into smaller tasks produced more coherent results than predicting the whole edit in one step. Its decomposition includes highlight detection, opening and ending selection, and irrelevant-content pruning.

Although its benchmark focuses on short drama rather than podcasts, the useful engineering principle transfers: editing should be a staged workflow with explicit intermediate decisions, not a single large prompt that returns a finished timeline.

### The field is not solved

There is no established general-purpose agent that reliably performs professional long-form editing across arbitrary footage. Research systems often focus on video understanding, retrieval, generative transformation, or short-form benchmarks rather than complete production workflows. Practical systems therefore combine language-model judgment with conventional media tooling and human review.

## Recommended agent mechanics

### Episode workspace

Each run should create a self-contained workspace:

```text
episode/
  sources/              immutable original media
  proxies/              lightweight inspection media
  analysis/
    media.json           streams, codecs, duration, resolution, frame rate
    transcript.json      words, timestamps, confidence, language
    speakers.json        speaker turns and identities when known
    audio-quality.json   noise, clipping, reverb, loudness, bandwidth
    shots.json           scene and camera boundaries
  timeline/
    strategy.md          approved editorial intent
    edit-plan.json       semantic edit operations and reasons
    draft.otio           frame-accurate timeline
  previews/
  renders/
```

### Agent-facing tools

The agent should receive semantic tools rather than raw FFmpeg access as its main interface:

- `probe_media(path)` inventories arbitrary input media.
- `transcribe(path)` produces word-level timestamps.
- `inspect_range(source, start, end)` returns a filmstrip, waveform, transcript, and audio preview.
- `search_transcript(query)` finds relevant moments.
- `compare_ranges(ranges)` compares alternate takes or candidate clips.
- `remove_range(start, end, reason)` records a non-destructive cut.
- `select_camera(start, end, source)` chooses a video source.
- `insert_asset(asset, position, duration)` adds intros, music, titles, or overlays.
- `make_short(start, end, aspect)` derives a vertical timeline.
- `render_preview(range)` makes a cheap local preview.
- `inspect_cut(cut_id)` checks visual and audio continuity.
- `render_master(profile)` produces the final deliverable.

The tools should return structured results, validate time ranges, preserve provenance, and keep every operation reversible.

### Editing stages

1. Inventory and synchronize all provided media.
2. Produce local transcription and objective media analysis.
3. Ask the user to approve a plain-language editing strategy.
4. Find false starts, repeated passages, long dead air, mistakes, and strong moments.
5. Produce a semantic edit plan with a reason for every destructive decision.
6. Compile the plan into a frame-accurate timeline, preferably using [OpenTimelineIO](https://opentimelineio.readthedocs.io/en/latest/).
7. Render low-resolution previews before full masters.
8. Inspect every cut boundary and revise failures.
9. Add branding, music, subtitles, graphics, and final audio.
10. Render long-form deliverables and separate vertical clips.

### Transcript dependency

For a conversational podcast, transcript-first editing is the strongest default because meaning and narrative live primarily in speech. Editing without a transcript is still possible using waveforms, silence detection, scene boundaries, face and activity detection, camera quality, and sampled visual summaries. It will be weaker at removing redundant ideas, preserving arguments, finding hooks, and selecting coherent clips.

The pipeline should degrade gracefully when transcription fails, but it should not pretend that visual and acoustic signals alone provide equivalent editorial understanding.

## Local audio-restoration research

### Relevant open-source models

#### DeepFilterNet

[DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) is a practical baseline for full-band speech denoising. It operates at 48 kHz, supports macOS, provides a compiled command-line path, and is designed to suppress noise while retaining speech quality. It is a strong candidate for conservative cleanup and should be included in the first bake-off.

#### ClearerVoice-Studio

[ClearerVoice-Studio](https://github.com/modelscope/ClearerVoice-Studio) provides pretrained models for 16 and 48 kHz speech enhancement, speech separation, super-resolution, and target-speaker extraction. Its MossFormer2 48 kHz enhancement model is particularly relevant. Its broader toolkit may help when recordings contain interfering talkers or limited bandwidth, although Apple Silicon performance and memory use need measurement.

#### Resemble Enhance

[Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) combines a denoiser with an enhancement stage that restores distortions and extends bandwidth. This may improve poor phone recordings more dramatically than conservative denoising. Because it reconstructs missing detail, it can also alter voice character or create artifacts. It should be optional and evaluated against the original rather than used by default.

#### VoiceFixer

[VoiceFixer](https://github.com/haoheliu/voicefixer) targets general speech restoration, including denoising, dereverberation, declipping, and bandwidth restoration. It is another candidate for comparative testing, but its older dependency stack and large environment may make it less suitable as a production default.

### Enhancement is not mastering

Noise suppression alone does not produce finished podcast audio. After restoration, a conventional deterministic chain is still needed. Depending on the source, that may include:

1. Channel selection, synchronization, and lossless conversion.
2. DC offset and low-frequency rumble removal.
3. Conservative denoising or dereverberation.
4. Repair of isolated clicks, dropouts, or clipping when feasible.
5. Corrective equalization.
6. De-essing where needed.
7. Gentle compression and level matching between speakers.
8. True-peak limiting.
9. Two-pass loudness normalization for the target publication profile.

[FFmpeg](https://ffmpeg.org/ffmpeg-filters.html) supplies deterministic filters for analysis, loudness normalization, silence detection, equalization, dynamics, and limiting. Loudness and true-peak measurements should follow [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I/en).

### Use an adaptive pipeline

A single fixed enhancement chain will over-process clean recordings and fail unpredictably on damaged ones. The pipeline should first characterize each input, then produce candidates:

- Original with mastering only.
- Conservative neural denoising plus mastering.
- Stronger restoration plus mastering.
- Optional generative enhancement plus mastering.

Candidate selection should combine objective measurements, transcription stability, artifact checks, and short listening samples. Useful non-reference metrics include [DNSMOS](https://arxiv.org/abs/2110.01763), which separately estimates speech, background, and overall quality, and [NISQA](https://github.com/gabrielmittag/NISQA), which estimates quality dimensions such as noisiness, coloration, discontinuity, and loudness. These metrics can rank candidates, but they must not be treated as proof that a familiar voice still sounds natural.

### Important risks

- Aggressive denoising can produce metallic or watery speech.
- Dereverberation can damage consonants and spatial character.
- Generative bandwidth restoration can invent plausible but inaccurate detail.
- A result that sounds cleaner can reduce transcription accuracy.
- Per-track enhancement can create mismatched room tone between speakers.
- Repeated encoding will compound artifacts; intermediate audio should remain lossless.
- Automatic quality metrics do not replace listening tests.

The pipeline must preserve originals, record model and parameter provenance, and allow instant A/B comparison at matched loudness.

## Proposed first experiments

Before designing a complete production architecture, assemble a small private evaluation set representing the real failure modes:

- Good dedicated microphone recording.
- iPhone recording in a quiet room.
- iPhone recording with room echo.
- Constant fan or ventilation noise.
- Street or café noise.
- Clipped or heavily compressed audio.
- Two people bleeding into one microphone.
- Remote-call audio with codec artifacts.

Run DeepFilterNet, ClearerVoice, Resemble Enhance, VoiceFixer, and mastering-only baselines against identical excerpts. Loudness-match every result. Record processing time, memory use, DNSMOS or NISQA changes, transcription changes, and blinded human preference.

The first production audio pipeline should be selected from these results, not from published benchmark rankings alone.

## Current design recommendation

Build a transcript-first, visually inspectable editing system with semantic agent tools and deterministic rendering. Start with a conservative local audio path and make stronger restoration opt-in until the evaluation set demonstrates when it is safe. Treat both video editing and audio enhancement as iterative propose-render-inspect workflows rather than one-shot transformations.

The earliest useful vertical slice is:

1. Point the system at an arbitrary folder of media.
2. Inventory it and extract lossless audio locally.
3. Transcribe locally with word-level timestamps.
4. Give Claude or Codex a packed transcript plus `inspect_range`.
5. Let the agent propose removals and highlights.
6. Compile the decisions into a timeline and render a preview.
7. Inspect every cut.
8. Produce one mastered episode and one captioned vertical clip.

This slice tests the core representation, tool contract, rendering loop, and audio path without requiring the complete future system.
