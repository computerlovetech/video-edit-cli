# Agent skills

The CLI owns the mechanics; the bundled **agent skills** teach an AI agent the
editing method — when to gather evidence, how to author plans, how to review
cuts. They are Markdown skill definitions (`SKILL.md` plus reference documents)
that ship inside the wheel.

## Installing

```sh
video-edit-cli skills list                 # what ships in this build
video-edit-cli skills install              # copies into .claude/skills/
video-edit-cli skills install --target <dir>
```

Alternatively, manage them with [agr](https://agr.run):

```sh
agr add computerlovetech/video-edit-cli/video-editor
```

## What the skills cover

**video-editor** is the core method skill. Its invariants apply to every task:

- Source media is immutable; every derived file keeps its provenance sidecar.
- Evidence before edits: never act on a range that hasn't been inspected via
  metadata, transcript, frames, waveform, or preview.
- Validate before rendering; preview before mastering when edits are material.
- Prefer the cheapest sufficient evidence.

It walks the agent through the workflow described in
[Workflows](workflows.md) — preflight, workspace, inspection, plan, render,
cut review, and final validation — with branch references for audio
restoration, packaged deliverables, multi-camera work, and vertical video.

**create-clips** builds on video-editor: it derives several publishable social
clips (YouTube Shorts, standard YouTube videos, LinkedIn) from a long-form
recording after a main edit exists. It is distributed via agr rather than in
the wheel.

## For repository contributors

The skill sources live in `skills/` at the repository root. Only skills listed
in `video_editor.skills.SHIPPED_SKILLS` (with matching force-include entries in
`pyproject.toml`) ship in the wheel; the rest are agr-only.
