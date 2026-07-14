# Edit plans

A plan is an ordered keep-list compiled deterministically to FFmpeg: each
timeline clip keeps `[in, out)` seconds of a source, in output order. Times come
from transcript JSON or direct inspection — never estimated. The authoritative
field reference is `video-edit-cli/src/video_editor/schemas/edit-plan.schema.json`;
unknown fields fail validation.

Minimal plan:

```json
{
  "schema_version": "1",
  "plan_id": "rough-cut-1",
  "created_by": "<agent>",
  "sources": [{"id": "src-1", "path": "/abs/path/recording.mp4"}],
  "timeline": [
    {"source": "src-1", "in": 0.5, "out": 42.1, "reason": "keep intro"},
    {"source": "src-1", "in": 55.0, "out": 120.4, "reason": "false start removed at 42.1-55.0"}
  ]
}
```

Rules:

- Every clip carries a `reason` — the editorial justification for what this keep
  implies was removed. Write reasons a reviewer could audit.
- Clips on the same source must be in increasing source order and must not
  overlap; a plan that reorders or repeats source material is rejected.
- Store plans in `<workspace>/plans/`, one file per revision; set `parent_plan`
  when revising instead of editing a rendered plan in place.
- `video-edit-cli plan validate --plan <file>` checks schema, references, ranges
  against real media, and ordering; it also reports output duration and the cut
  boundaries you must later inspect.
- `video-edit-cli render preview --plan <file> --output <workspace>/previews/<name>.mp4`
  renders the validated rough cut (360p default) and writes
  `<output>.manifest.json` mapping every output-time boundary back to source
  times — the input for cut review. Never present a render whose boundaries you
  have not inspected.
