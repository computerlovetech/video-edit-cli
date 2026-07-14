# Cut review

A render is unreviewed until every boundary has evidence. The loop is
render → inspect → revise → re-render, repeated until each cut passes or its
defect is explicitly reported.

1. `video-edit-cli cuts list --manifest <render>.manifest.json` enumerates every
   boundary with a `boundary_type`: `temporal-cut`, `source-switch`, `transform`,
   or `continuous`. Transform boundaries preserve source time while changing a
   crop, video source, or gain.
2. Inspect all cuts with `video-edit-cli cut inspect --manifest <manifest> --all
   --output-dir <workspace>/reports --transcript <transcript.json>` produces a
   filmstrip, waveform, short preview, before/after frames, and a report with
   deterministic checks:
   - `black_frames_near_cut` / `silence_near_cut` — timestamps flagged by
     blackdetect/silencedetect in the review window.
   - `clipped_word_before` / `clipped_word_after` — a transcript word whose span
     straddles a discontinuous cut. This check is skipped for same-source
     continuous and transform boundaries because no transcript time was removed.
3. Judge the evidence yourself: look at the filmstrip and frames for visual
   jumps, posture/continuity mismatches, or mid-gesture cuts, and play or
   inspect the preview's waveform for audible bumps. `passed: true` means the
   deterministic checks found nothing — it does not certify the cut feels right.
   For transform boundaries, confirm that framing changes on the source layout
   change and that the active subject remains visible on both sides.
4. Fix a defective cut by writing a revised plan (`parent_plan` set, adjusted
   in/out times), re-rendering, and re-inspecting that boundary.

Completion: every cut in the final render has a report in
`<workspace>/reports/`, and each is either clean or explicitly listed as an
unresolved defect when you present the result.
