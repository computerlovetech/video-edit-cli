# Workspace conventions

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
