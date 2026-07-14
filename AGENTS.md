# video-edit-cli

This repository contains two independently useful but coordinated artifacts:

- The `video-edit-cli` Python package and executable provide deterministic,
  project-agnostic media operations.
- `skills/video-edit-cli/` teaches AI agents how to compose those operations into an
  evidence-based editing workflow.

Keep project identity, brand defaults, editorial voice, and publishing credentials out
of this repository. Projects provide explicit profiles and assets by path.

Source media is immutable. Derived artifacts must retain provenance sidecars and the
workspace, transcript, edit-plan, profile, result, and render-manifest contracts must
remain backward compatible unless their schema version changes.

Before committing package changes, run:

```sh
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

Before publishing, also build distributions and install the wheel in a clean environment.
