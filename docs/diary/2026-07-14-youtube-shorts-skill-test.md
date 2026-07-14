# Diary: YouTube Shorts skill and CLI test

Create three retention-oriented vertical clips from a YouTube podcast episode, package them with burned captions and publishing copy, then revise the framing after real-world visual review exposed a layout error.

## Step 1: Produce three captioned vertical clips

**Author:** main

### Prompt Context

**Verbatim prompt:** Make 3 youtube shorts clips from this video using video-editor skill to test the skill and the cli. it should be veritcal format and have subtitles printed into  the video in some font size and type that you notice on social media. the clips shuold be fast paced, engagning and max out rentention.
Youtube video: https://www.youtube.com/watch?v=H-umNSXMxlw 

make a working dir for it

**Interpretation:** Download the episode, create an immutable video-edit workspace, transcribe it, select three strong excerpts editorially, render 1080x1920 clips, burn social-style captions, validate them, and retain provenance and publishing metadata.

**Inferred intent:** Exercise the video-editor and create-clips instructions against a real recording, uncover workflow or CLI weaknesses, and leave usable Shorts rather than synthetic test fixtures.

### What I did

I downloaded the source into `/workspaces/H-umNSXMxlw/source/`, initialized `/workspaces/H-umNSXMxlw/edit/workspace.json`, extracted canonical audio, installed the declared MLX extra, and created a 6,730-word transcript. I read the full packed transcript, chose three excerpts, inspected filmstrips and reframe previews, created and validated short plans, rendered full-resolution previews, generated SRT/VTT captions, converted them to styled ASS, burned them into the videos, and validated duration and caption coverage. Packages live under `/workspaces/H-umNSXMxlw/clips/`.

### Why

The skill requires evidence before edits, immutable source media, transcript-derived boundaries, explicit crop decisions, provenance, and validation. The packaging work also tested whether the CLI primitives compose into a complete short-form workflow.

### What worked

The workspace and provenance contracts made the workflow auditable. MLX Whisper large-v3-turbo transcribed the 37.5-minute episode quickly and produced useful word timings. Transcript packing made editorial selection practical. `short create-plan`, `plan validate`, `render preview`, `subtitles create`, and `output validate` composed cleanly. CLI commands returned structured JSON, making failures and artifact paths easy to track. The three selected excerpts were semantically strong and the caption styling rendered cleanly once a libass-enabled FFmpeg was available.

### What didn't work

The first transcription attempt failed with `error [missing-dependency]: the mlx-whisper backend requires the optional 'mlx' extra; install with \`uv sync --extra mlx\` (Apple Silicon only)` from `uv run video-edit-cli transcript create ...`. This was recoverable by installing the documented extra.

The first caption burn failed with `error [tool-failure]: this ffmpeg build has no 'subtitles' filter (libass); use --mode mux or install a full ffmpeg build` from `uv run video-edit-cli subtitles render ... --mode burn`. Installing `ffmpeg-full` solved it, but Homebrew upgraded `x265` and temporarily broke the linked standard FFmpeg with `Library not loaded: /opt/homebrew/opt/x265/lib/libx265.215.dylib`. Reinstalling `ffmpeg` repaired the default binary.

Most importantly, the initial visual review was insufficient. Sparse filmstrips made the source look like alternating solo shots, so all plans used a center crop. In reality, the episode alternated between full-screen and persistent split-screen layouts. The center crop cut both faces in split screen. CLI validation passed because it checks technical properties, not subject framing.

### What I learned

For short-form reframing, identifying the source's layout state is a separate task from locating faces in a few frames. A crop can be locally correct and globally wrong. Split-screen podcasts need layout-aware, per-segment crops. Technical validation cannot substitute for watching or densely sampling the complete vertical result.

### What was tricky

The split-screen seam looked like a wipe transition in isolated frames, which led to the wrong diagnosis. The source switches among split screen, solo-left, and solo-right layouts. The CLI supports a crop per timeline segment, but the skill did not make layout segmentation explicit, so the capability was initially underused. Caption styling also required an ASS conversion because `subtitles render` exposes no style arguments.

### What warrants review

Review `/workspaces/H-umNSXMxlw/edit/plans/short-01.json` through `short-03.json` as examples of technically valid but editorially defective static crops. Compare their renders with the v2 plans and renders. Review whether dependency preflight should report MLX and libass availability before long workflows begin.

### Future work

Add a layout-analysis or dense visual-QC step to the vertical-video instructions. Consider CLI support for subtitle style profiles and a dependency preflight command. Add output validation hooks for sampled framing or a report that explicitly states visual framing is unverified.

## Step 2: Replace static crops with layout-aware crops

**Author:** main

### Prompt Context

**Verbatim prompt:** okay it looks like this in 1 and 3 [Image #1] not good. 2 is mostly good, but the camera occasionally gets into the middle of the screen.

**Interpretation:** Diagnose the framing defect from the supplied screenshot and revise all three clips, including the less obvious intermittent problem in clip 2.

**Inferred intent:** Produce genuinely usable final clips and determine why the first supposedly validated outputs were visually wrong.

### What I did

I inspected full-resolution source frames across all three ranges and ran scene-change detection to map layout transitions. I created revision plans `/workspaces/H-umNSXMxlw/edit/plans/short-01-v2.json` through `short-03-v2.json`, each with a `parent_plan` and per-segment crops: right-pane crops for split screen and centered crops for solo shots. I rendered dense filmstrips, regenerated captions against the revised manifests, burned them into `vertical-v2.mp4`, validated all outputs, and produced cut-inspection reports.

### Why

The defect was not solvable with one crop per excerpt. The plans needed to encode layout changes explicitly while retaining continuous source timing and provenance.

### What worked

Per-timeline-segment crop support was exactly the right primitive. Once the layout states were known, the fix was deterministic and compact. Dense 15-frame filmstrips immediately demonstrated that all faces stayed centered. The v2 outputs passed duration and subtitle validation, and user review confirmed the result was excellent.

### What didn't work

The first cut-inspection command mistakenly used `--cut 1` when `cuts list` reported the only cut as `cut_index: 0`, producing `error [invalid-input]: cut index 1 out of range (render has 1 cuts)`. Retrying with `--cut 0` worked.

Cut inspection marked clip 1 and clip 2 boundaries as failed because the crop changes occur during continuous words (`you're` and `Mm`). No source time is removed—the adjacent segments meet at the same timestamp—but the checker treats the reframe boundary like a discontinuous editorial cut. This is a false-positive or at least a poorly classified warning for continuous same-source crop changes.

### What I learned

The edit-plan schema already has the expressive power needed for dynamic reframing. The main gap is planning guidance and review tooling, not necessarily rendering capability. Reframe boundaries should be distinguished from temporal cuts because their audio-continuity risks differ.

### What was tricky

Layout transition times did not always coincide with word boundaries. Visually correct crop switches can occur mid-word while audio remains continuous. The current manifest and cut-review model cannot represent “continuous media, changed visual transform,” so it reports clipped words even when nothing was clipped.

### What warrants review

Inspect `/workspaces/H-umNSXMxlw/edit/reports/v2-01.jpg` through `v2-03.jpg` and compare them with `/workspaces/H-umNSXMxlw/edit/reports/final-01.jpg` through `final-03.jpg`. Review `/workspaces/H-umNSXMxlw/edit/reports/cut-01-v2/cut-0-report.json` and `cut-02-v2/cut-0-report.json` as concrete false-positive cases.

### Future work

Teach manifests and cut review to classify transform-only boundaries separately from source-time discontinuities. Add an ergonomic way to author dynamic crop segments, and require full-range or dense-sample framing review before a vertical deliverable is declared complete.

## Step 3: Encode the lessons in the CLI and skills

**Author:** main

### Prompt Context

**Verbatim prompt:** please update the cli and skill what these improvements until you're satisfied.

**Interpretation:** Turn the concrete workflow failures into backward-compatible CLI capabilities, tests, and stronger agent instructions, then exercise the changes against the real clip rather than stopping at fixture coverage.

**Inferred intent:** Make future vertical-caption workflows fail earlier, classify edits more accurately, expose missing styling/reflow controls, and prevent a technical pass from being mistaken for visual approval.

### What I did

I added a workflow-aware `doctor` command, transform-aware render manifests and cut reports, batch `cut inspect --all`, short-form subtitle reflow controls, direct burn-style controls, explicit canvas expectations, and validation-scope reporting. I updated both copies of the video-editor skill plus the create-clips instructions to require layout-state classification, dense full-range review, technical/visual separation, and representative caption-frame inspection. Tests now cover preflight, transform boundaries, batch inspection, reflow, style-mode rejection, canvas expectations, and validation scope.

### Why

Every addition maps to a failure observed in the real session: dependencies were discovered late, dynamic crops were misclassified as destructive cuts, captions required an undocumented ASS conversion, and a technically valid render still had broken framing.

### What worked

The existing command structure and JSON envelopes accepted the new behavior without schema breakage. A real forward test classified the clip's crop switch as `boundary_type: transform`, marked it source-continuous, skipped the irrelevant clipped-word test, and passed `cut inspect --all`. Reflow produced 27 concise cues over 42.08 seconds. `output validate --expect-canvas 1080x1920` passed and now states that visual framing and editorial quality remain unperformed.

### What didn't work

The first implementation pass produced `error[unresolved-reference]: Name subtitle_filter used when not defined` because the burn-filter variable was placed in the mux branch. Type checking caught it before the full test run. The first real styled burn used pixel-like values (`--font-size 60 --margin-v 280`); libass interpreted them in its approximately 384x288 script coordinate system and pushed oversized captions off the top of the frame. Technical validation still passed, proving again that media metadata cannot validate composition. The first forward-test command also passed the project root to `--workspace`, but the actual manifest was at `edit/workspace.json`, producing `error [invalid-input]: no workspace manifest at workspaces/H-umNSXMxlw/workspace.json`.

### What I learned

Tool contracts need to name their coordinate system. A style parameter called “font size” or “margin” invites pixel assumptions unless the CLI help and skill explicitly say ASS script units. Real-media forward tests reveal semantic bugs that unit tests and stream validation cannot. Structured boundary types are more useful than treating every segment join as an editorial cut.

### What was tricky

Continuous source time and changed visual transforms had to be inferred from adjacent manifest segments while retaining compatibility with old manifests. Subtitle cue splitting needed deterministic approximate timings without inventing word-level data. Keeping the canonical and mirrored skill trees identical required deliberate verification.

### What warrants review

Review `src/video_editor/diagnostics.py`, the transform classification in `src/video_editor/review.py`, the subtitle styling/reflow contract, and the revised vertical-video guidance. The corrected real-media proof is `workspaces/H-umNSXMxlw/edit/reports/short-01-styled-corrected-frame-2.png`; compare it with the intentionally failed pixel-assumption render at `short-01-styled-frame-2.png`.

### Future work

Consider a first-class subtitle style profile or a pixel-based abstraction that generates ASS with an explicit PlayRes, automatic workspace discovery from child paths, and optional computer-vision framing checks. These are larger design changes; the current CLI now documents the boundary honestly and requires visual evidence.
