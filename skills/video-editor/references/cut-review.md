# Cut review

A render is unreviewed until every boundary has evidence. The loop is
render → inspect → revise → re-render, repeated until each cut passes or its
defect is explicitly reported.

1. `video-edit-cli cuts list --manifest <render>.manifest.json` enumerates every
   boundary with its output time and the source out/in times it joins.
2. For each cut, `video-edit-cli cut inspect --manifest <manifest> --cut <i>
   --output-dir <workspace>/reports --transcript <transcript.json>` produces a
   filmstrip, waveform, short preview, before/after frames, and a report with
   deterministic checks:
   - `black_frames_near_cut` / `silence_near_cut` — timestamps flagged by
     blackdetect/silencedetect in the review window.
   - `clipped_word_before` / `clipped_word_after` — a transcript word whose span
     straddles the cut point (pass `--transcript` whenever one exists).
3. Judge the evidence yourself: look at the filmstrip and frames for visual
   jumps, posture/continuity mismatches, or mid-gesture cuts, and play or
   inspect the preview's waveform for audible bumps. `passed: true` means the
   deterministic checks found nothing — it does not certify the cut feels right.
4. Fix a defective cut by writing a revised plan (`parent_plan` set, adjusted
   in/out times), re-rendering, and re-inspecting that boundary.

Completion: every cut in the final render has a report in
`<workspace>/reports/`, and each is either clean or explicitly listed as an
unresolved defect when you present the result.
