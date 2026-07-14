# Vertical / short-form deliverables

Applies when a vertical or short-form clip is requested. You choose the moment
— from the transcript and targeted inspection — and the tools execute it; no
command picks highlights.

1. **Choose the range yourself.** Find candidate moments in the transcript
   (hooks, self-contained arguments), confirm visually with filmstrips, and pick
   exact word-aligned in/out times.
2. **Classify every layout state.** Inspect a dense filmstrip across the complete
   range and frames around each scene/layout change. Record whether each span is
   solo speaker, split screen, screen share, picture-in-picture, or transition.
   Never infer that one crop works from a single representative frame.
3. **Frame explicitly.** Inspect frames to decide each crop, then check it with
   `video-edit-cli reframe preview --input <src> --start … --end …
   --crop x:y:w:h --canvas 1080x1920`. Iterate until the speaker sits correctly
   in the vertical frame. Mixed layouts require separate timeline segments with
   per-segment `crop` values; preserve source continuity at transform boundaries.
4. **Derive the plan.** `video-edit-cli short create-plan --input <src>
   --start … --end … --canvas 1080x1920 --crop … --reason "…"
   --output <ws>/plans/short-1.json` writes a normal, editable edit plan with
   `output_canvas` set; refine it like any plan (split clips, adjust times).
5. **Render and caption.** `render preview` honors the plan's canvas. Create
   captions with `subtitles create` against the short's render manifest and
   use `--max-words`, `--max-chars`, and `--max-duration` to reflow long transcript
   segments for short-form reading. Burn a project-provided style with the font,
   size, color, outline, alignment, and margin options on `subtitles render`.
   Numeric styles are ASS script units, not output pixels; for SRT/VTT, start
   near `--font-size 9.5 --outline-width 1 --shadow 0.5 --alignment 2 --margin-v
   42`, burn a representative frame, and adjust from visual evidence.
6. **Validate technically and visually.** Run `output validate --expect-canvas
   1080x1920 --expect-duration …`, then create a
   dense full-range filmstrip (at least 15 samples for a one-minute short) and
   inspect frames immediately before and after every layout boundary. Confirm
   that the active speaker remains visible, captions stay in the safe area, and
   no split-screen seam or inactive camera occupies the vertical frame.

Completion: the short matches the requested canvas and duration, captions map
correctly, every layout state has an approved crop, and dense full-range visual
review confirms framing. A technically passing `output validate` is insufficient.
