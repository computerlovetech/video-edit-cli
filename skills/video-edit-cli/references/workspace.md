# Workspace conventions

## Default project location

Unless the user specifies another destination, keep each editing job under the
current project root:

```text
<project-root>/video-edit-projects/YYYY-MM-DD-<source-id-or-slug>/
  source/        downloaded or copied immutable source media
  edit/          video-edit-cli workspace root
  deliverables/  optional handoff copies and accompanying text
```

Prefix the job directory with its local creation date in ISO format, then append
a stable, filesystem-safe external identifier when one exists (for example,
`2026-07-14-r1Kh5WssSPg` for a YouTube video); otherwise append a concise
source-derived slug. Before initializing, tell the user which path you will use.
Search existing `video-edit-projects/*/edit/workspace.json` manifests first and
reuse a project whose registered source path or SHA-256 matches, even on a later
date, instead of creating a duplicate. Never silently combine unrelated sources
into an existing project.

This location is an agent convention, not hidden CLI state: continue to pass the
explicit `--root`, `--workspace`, input, and output paths to every command. A
user-provided location always overrides the convention.

## CLI workspace layout

`video-edit-cli workspace init --root <path> --source <file>...` creates:

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

Rules:

- Write each derived artifact into the matching directory, and pass
  `--workspace <root>` on derived-file commands so the artifact is recorded in
  `workspace.json`.
- Refer to sources by their manifest id (`src-1`, `src-2`, …) in plans and notes;
  the manifest maps ids to immutable paths and hashes.
- Give each source a `--role` label at init when you know it
  (e.g. `camera-a`, `screen`, `mic-guest`).
- A workspace is organization, not hidden state: commands still take explicit
  input/output paths, so you can always operate on files directly.
