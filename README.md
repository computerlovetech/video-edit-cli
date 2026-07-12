# video-edit-cli

Headless, project-agnostic video-editing workbench for AI agents. One `video-edit-cli`
CLI exposes atomic, non-interactive subcommands that inspect and transform media
deterministically; the agent plans the edit and composes the primitives.

Contract:

- Machine-readable JSON on stdout (one result envelope per command), diagnostics on
  stderr, meaningful non-zero exit codes on failure.
- Source media is immutable. Every derived file is new and gets a
  `*.provenance.json` sidecar recording inputs, hashes, tool versions, parameters,
  and the exact tool commands.
- Requires `ffmpeg` and `ffprobe` on PATH; commands fail with the stable error code
  `missing-binary` when absent.

Install the base CLI with `uv tool install video-edit-cli`. For local Apple Silicon
transcription, install `uv tool install 'video-edit-cli[mlx]'`. FFmpeg and FFprobe must
be installed separately and available on `PATH`.

Usage discovery: `video-edit-cli --help` and `--help` on every subcommand. Inside this
repository, prefix commands with `uv run`.

Example:

```sh
uv run video-edit-cli workspace init --root /tmp/ep1 --source recording.mp4
uv run video-edit-cli probe --input recording.mp4
uv run video-edit-cli filmstrip create --input recording.mp4 \
  --start 60 --end 90 --output /tmp/ep1/analysis/strip.png --workspace /tmp/ep1
```

The companion skill in `skills/video-editor/` teaches agents the editing method;
this package owns the mechanics. Tests generate small deterministic fixtures at
runtime (`tests/generate_fixtures.py`); no media is committed.

Quality gates (run from this directory):

```sh
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```
