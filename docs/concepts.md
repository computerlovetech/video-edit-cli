---
title: "Concepts: edit plans, provenance, workspaces"
description: >-
  The five ideas behind video-edit-cli — JSON result envelopes, immutable
  sources with provenance sidecars, workspaces, reviewable edit plans, and
  project profiles.
---

# Concepts

The tool uses five ideas: the result envelope, immutable sources with
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

See the formal definition in
[`result.schema.json`](https://github.com/computerlovetech/video-edit-cli/blob/main/src/video_editor/schemas/result.schema.json);
the other JSON documents (edit plans, transcripts, workspaces, profiles) have
schemas in the same directory.

## Immutable sources and provenance

Commands never modify their inputs. Every derived file is a new file, and every
derived file gets a `*.provenance.json` sidecar recording:

- the input paths and their SHA-256 hashes,
- the tool versions (`video-edit-cli`, ffmpeg),
- the parameters the command received,
- the exact commands the underlying tools ran.

The sidecar shows where a file came from and how to create it again.

## Workspaces

`workspace init` creates an organized directory for one editing job:

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

Workspaces organize files; they do not hold hidden state. Commands still take
explicit input and output paths. Passing `--workspace <root>` also records the
derived artifact in `workspace.json`. Plans and notes refer to sources by
manifest id (`src-1`, `src-2`, …). Sources can also have a `--role` label
(`camera-a`, `screen`, `mic-guest`).

By default, the companion agent skill puts new jobs in
`<project-root>/video-edit-projects/YYYY-MM-DD-<source-id-or-slug>/`, with the CLI
workspace in its `edit/` directory. This is an agent convention. The CLI still
requires explicit paths and accepts any location the user chooses.

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
  the validator rejects unknown fields.
- The validator checks clip ranges against the real media durations.
- Clips on the same source must be in increasing source order and must not
  overlap.
- Every clip has a `reason` that explains the edit to a reviewer.

Rendering a plan (`render preview` or `render master`) also writes
`<output>.manifest.json`, which maps every output-time cut boundary back to
source times. That manifest drives the review commands (`cuts list`,
`cut inspect`) and subtitle derivation (`subtitles create`).

Create a new file for each revision. Set `parent_plan` to the previous plan's
id instead of editing a rendered plan in place.

## Project profiles

An external YAML profile defines the project's canvases, codecs, loudness
targets, intro and outro assets, music, fonts, camera aliases, and subtitle
style. Pass its path explicitly. The CLI never finds profiles through the
environment.

Top-level keys: `schema_version`, `profiles` (named render profiles), `music`,
`assets`, `fonts`, `camera_aliases`, `subtitle_style`. Relative asset paths
resolve against the profile file's directory, and every referenced file must
exist. The schema is
[`project-profile.schema.json`](https://github.com/computerlovetech/video-edit-cli/blob/main/src/video_editor/schemas/project-profile.schema.json).

`render master` uses a named profile. `output validate` checks a finished file
against the profile's canvas, codec, and loudness settings.

## Transcripts

`transcript create` writes a word-level JSON transcript — the authoritative
artifact. `transcript pack` derives a compact text view for reading, and
`transcript search` finds time-aligned matches for a spoken phrase. Plans quote
times from the JSON, never from the packed view.
