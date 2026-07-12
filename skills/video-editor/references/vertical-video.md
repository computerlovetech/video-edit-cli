# Vertical / short-form deliverables

Applies when a vertical or short-form clip is requested. You choose the moment
— from the transcript and targeted inspection — and the tools execute it; no
command picks highlights.

1. **Choose the range yourself.** Find candidate moments in the transcript
   (hooks, self-contained arguments), confirm visually with filmstrips, and pick
   exact word-aligned in/out times.
2. **Frame explicitly.** Inspect a frame to decide the crop, then check it with
   `video-edit-cli reframe preview --input <src> --start … --end …
   --crop x:y:w:h --canvas 1080x1920`. Iterate until the speaker sits correctly
   in the vertical frame.
3. **Derive the plan.** `video-edit-cli short create-plan --input <src>
   --start … --end … --canvas 1080x1920 --crop … --reason "…"
   --output <ws>/plans/short-1.json` writes a normal, editable edit plan with
   `output_canvas` set; refine it like any plan (split clips, adjust times).
4. **Render and caption.** `render preview` honors the plan's canvas. Create
   captions with `subtitles create` against the short's render manifest and
   attach with `subtitles render`. Vertical viewers rely on captions — include
   them unless told otherwise.
5. **Validate.** `output validate --expect-duration … --expect-subtitles`
   plus a filmstrip of the result to confirm framing survived.

Completion: the short matches the requested canvas and duration, captions map
correctly to the excerpt, and your summary states why this range was chosen.
