---
title: Agent skills for video editing
description: >-
  Install the bundled video-edit-cli agent skills that teach Claude Code,
  Codex, Cursor, and other coding agents an evidence-based video editing
  method.
---

# Agent skills

The CLI performs the operations. The bundled **agent skills** teach an AI agent
when to gather evidence, how to write plans, and how to review cuts. These
Markdown files (`SKILL.md` and its references) ship inside the wheel.

## Installing

The recommended path is [skills.sh](https://skills.sh) — no prior CLI install
needed; the skill has the agent install the CLI when it's missing:

```sh
npx skills add computerlovetech/video-edit-cli --skill video-edit-cli
```

If you already installed the CLI, install its bundled copy directly:

```sh
video-edit-cli skills list                 # what ships in this build
video-edit-cli skills install              # copies into .claude/skills/
video-edit-cli skills install --target <dir>
```

You can also manage them with [agr](https://agr.run):

```sh
agr add computerlovetech/video-edit-cli/video-edit-cli
```

## What the skills cover

**video-edit-cli** is the core method skill. Its invariants apply to every task:

- Source media is immutable; every derived file keeps its provenance sidecar.
- Evidence before edits: inspect a range through metadata, a transcript,
  frames, a waveform, or a preview before acting on it.
- Validate before rendering; preview before mastering when edits are material.
- Prefer the cheapest sufficient evidence.

It guides the agent through the workflow in
[Workflows](workflows.md) — preflight, workspace, inspection, plan, render,
cut review, and final validation — with branch references for audio
restoration, packaged deliverables, multi-camera work, and vertical video.

## For repository contributors

The skill sources live in `skills/` at the repository root. Only skills listed
in `video_editor.skills.SHIPPED_SKILLS` (with matching force-include entries in
`pyproject.toml`) ship in the wheel; the rest are agr-only.
