# Concepts

Five ideas carry the whole tool: the result envelope, immutable sources with
provenance, workspaces, edit plans, and project profiles.

## Result envelope

Every command prints exactly one JSON object on stdout. Success:

```json
{
  "ok": true,
  "command": "probe",
  "schema_version": "1",
  "artifacts": [{"path": "/tmp/ep1/analysis/strip.png", "kind": "filmstrip"}],
  "data": { "…command-specific payload…": "…" }
}
```

Failure:

```json
{
  "ok": false,
  "command": "render.preview",
  "schema_version": "1",
  "error": {"code": "invalid-input", "message": "plan references missing source"}
}
```

Diagnostics and progress go to stderr, so stdout is always parseable. Error
codes and exit codes are stable:

| Error code | Exit code | Meaning |
|---|---|---|
| `invalid-input` | 2 | Bad arguments, malformed plan/profile, missing file |
| `missing-binary` | 3 | `ffmpeg`/`ffprobe` (or an optional backend) not on `PATH` |
| `tool-failure` | 4 | An underlying tool ran and failed |

The envelope is described formally in
[`result.schema.json`](https://github.com/computerlovetech/video-edit-cli/blob/main/src/video_editor/schemas/result.schema.json);
the other JSON documents (edit plans, transcripts, workspaces, profiles) have
schemas in the same directory.

## Immutable sources and provenance

Commands never modify their inputs. Every derived file is a new file, and every
derived file gets a `*.provenance.json` sidecar recording:

- the input paths and their SHA-256 hashes,
- the tool versions (`video-edit-cli`, ffmpeg),
- the parameters the command received,
- the exact underlying tool commands that were executed.

This makes any artifact auditable and reproducible: given the sidecar, you can
see exactly where a file came from and re-derive it.

## Workspaces

A workspace is an organized directory for one editing job, created with
`workspace init`:

```text
<workspace>/
  workspace.json    manifest: workspace id, sources (paths, sha256, roles), artifacts
  sources/          symlinks to the immutable originals; never write here
  analysis/         probe, transcript, audio, sync, and shot artifacts
  proxies/          low-cost inspection media
  plans/            agent-authored edit plans
  previews/         range, cut, and draft previews
  renders/          final or candidate renders
  reports/          validation, comparison, and QC reports
```

Workspaces are organization, not hidden state. Commands still take explicit
input and output paths; passing `--workspace <root>` additionally records the
derived artifact in `workspace.json`. Sources are referred to by manifest id
(`src-1`, `src-2`, …) in plans and notes, and can carry a `--role` label
(`camera-a`, `screen`, `mic-guest`).

## Edit plans

A plan is an ordered keep-list, compiled deterministically to FFmpeg. Each
timeline clip keeps `[in, out)` seconds of a source, in output order. The CLI
never authors plans — the agent does; the CLI validates and renders them.

```json
{
  "schema_version": "1",
  "plan_id": "rough-cut-1",
  "created_by": "agent",
  "sources": [{"id": "src-1", "path": "/abs/path/recording.mp4"}],
  "timeline": [
    {"source": "src-1", "in": 0.5, "out": 42.1, "reason": "keep intro"},
    {"source": "src-1", "in": 55.0, "out": 120.4, "reason": "false start removed at 42.1-55.0"}
  ]
}
```

Rules enforced by `plan validate`:

- The plan must match
  [`edit-plan.schema.json`](https://github.com/computerlovetech/video-edit-cli/blob/main/src/video_editor/schemas/edit-plan.schema.json);
  unknown fields are rejected.
- Clip ranges are checked against the real media durations.
- Clips on the same source must be in increasing source order and must not
  overlap.
- Every clip carries a `reason` — the editorial justification a reviewer can
  audit.

Rendering a plan (`render preview` or `render master`) also writes
`<output>.manifest.json`, which maps every output-time cut boundary back to
source times. That manifest drives the review commands (`cuts list`,
`cut inspect`) and subtitle derivation (`subtitles create`).

Revisions are new files: set `parent_plan` to the previous plan's id rather
than editing a rendered plan in place.

## Project profiles

Project identity — canvases, codecs, loudness targets, intro/outro assets,
music, fonts, camera aliases, subtitle styling — lives in an external YAML
profile, passed explicitly by path. Profiles are never discovered from the
environment.

Top-level keys: `schema_version`, `profiles` (named render profiles), `music`,
`assets`, `fonts`, `camera_aliases`, `subtitle_style`. Relative asset paths
resolve against the profile file's directory, and every referenced file must
exist. The schema is
[`project-profile.schema.json`](https://github.com/computerlovetech/video-edit-cli/blob/main/src/video_editor/schemas/project-profile.schema.json).

Profiles are consumed by `render master` (pick a named profile to render with)
and `output validate` (check a finished file against the profile's canvas,
codec, and loudness expectations).

## Transcripts

`transcript create` writes a word-level JSON transcript — the authoritative
artifact. `transcript pack` derives a compact text view for reading, and
`transcript search` finds time-aligned matches for a spoken phrase. Plans quote
times from the JSON, never from the packed view.
