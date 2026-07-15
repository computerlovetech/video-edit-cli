---
title: FAQ — AI agent video editing
description: >-
  Answers to common questions: free Opus Clip alternatives without watermarks,
  editing video with Claude Code, removing silences from podcasts, making
  YouTube Shorts automatically, and keeping footage local.
---

# FAQ

## Can an AI coding agent like Claude Code really edit video?

Yes. video-edit-cli gives the agent deterministic commands for transcription,
cutting, reframing, subtitles, and audio mastering, plus a bundled
[skill](skills.md) that teaches it an editor's method: gather evidence first
(transcript, frames, waveforms), author an edit plan where every cut has a
written reason, then render and review. You ask in plain language; the agent
does the editing on your machine.

## Is there a free Opus Clip alternative without watermarks or credits?

video-edit-cli is one: open source, free, no watermarks, no per-clip credits,
and no clip expiry. Hosted clip apps charge $15–29/month and meter you with
per-minute credits — a single hour-long video can burn much of a starter plan.
Here, the only costs are your own compute. See the
[comparison table](https://github.com/computerlovetech/video-edit-cli#how-it-compares).

## How do I make YouTube Shorts from a long video automatically?

Install the skill (`npx skills add computerlovetech/video-edit-cli --skill
video-edit-cli`) and ask your agent, for example: *"Make clips for YouTube
Shorts from this video, with burned-in subtitles."* The agent transcribes the
video, picks the strongest moments from the transcript, reframes to 9:16,
burns in styled captions, and renders each clip. See
[example prompts](examples.md).

## How do I remove silences, filler words, and false starts from a podcast?

Ask your agent to *"edit this recording into a publishable episode: cut the
false starts, retakes, and long silences."* Unlike threshold-based silence
cutters, the agent works from a word-level transcript, so it can distinguish a
dramatic pause from dead air and remove a false start without clipping the
retake. The [main edit workflow](workflows.md) shows the full recipe.

## Is this like Descript's text-based editing?

The editing model is similar — cut video by working with its transcript — but
video-edit-cli is a free, local CLI driven by your AI agent rather than a
subscription desktop app. The agent reads the transcript and authors the cuts
for you, and every cut is recorded in a reviewable edit plan with a reason.

## Does my footage get uploaded anywhere?

No. Everything — transcription included — runs locally. Source files are never
modified, and every derived file gets a provenance sidecar recording exactly
how it was made. Nothing leaves your machine unless you publish it.

## What do I need installed?

Only `ffmpeg` and `ffprobe`. The skill has the agent install the CLI itself
(`uv tool install video-edit-cli`) when it's missing, and
`video-edit-cli doctor` verifies the rest per workflow.

## Which coding agents does it work with?

Any agent that supports skills: Claude Code, Codex, Cursor, GitHub Copilot,
Pi, Amp, and others. The CLI itself is plain shell + JSON, so any agent that
can run commands can use it directly.

## Can I trust the cuts the agent makes?

You can audit them. Every edit plan is an ordered keep-list where each cut
carries a written `reason`; you (or the agent) review it cut by cut before
rendering, and rendered artifacts carry provenance sidecars, so any edit can
be reproduced or challenged. No black-box "virality score".

## Does it run on Windows?

macOS and Linux are supported. Windows is untested — use WSL.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {"@type": "Question", "name": "Can an AI coding agent like Claude Code really edit video?", "acceptedAnswer": {"@type": "Answer", "text": "Yes. video-edit-cli gives the agent deterministic commands for transcription, cutting, reframing, subtitles, and audio mastering, plus a bundled skill that teaches it an editor's method: gather evidence, author an edit plan where every cut has a written reason, then render and review — all locally."}},
    {"@type": "Question", "name": "Is there a free Opus Clip alternative without watermarks or credits?", "acceptedAnswer": {"@type": "Answer", "text": "video-edit-cli is one: open source, free, no watermarks, no per-clip credits, no clip expiry. It runs locally, driven by your AI coding agent."}},
    {"@type": "Question", "name": "How do I make YouTube Shorts from a long video automatically?", "acceptedAnswer": {"@type": "Answer", "text": "Install the video-edit-cli skill and ask your coding agent to make Shorts from the video. It transcribes, picks the strongest moments, reframes to 9:16, burns in captions, and renders each clip locally."}},
    {"@type": "Question", "name": "How do I remove silences, filler words, and false starts from a podcast?", "acceptedAnswer": {"@type": "Answer", "text": "Ask your agent to edit the recording into a publishable episode. It cuts from a word-level transcript, so it distinguishes dramatic pauses from dead air and removes false starts without clipping the retake."}},
    {"@type": "Question", "name": "Does my footage get uploaded anywhere?", "acceptedAnswer": {"@type": "Answer", "text": "No. Everything runs locally, including transcription. Source files are immutable and every derived file gets a provenance sidecar."}},
    {"@type": "Question", "name": "Which coding agents does it work with?", "acceptedAnswer": {"@type": "Answer", "text": "Any agent that supports skills: Claude Code, Codex, Cursor, GitHub Copilot, Pi, Amp, and others. The CLI is plain shell + JSON, so any agent that can run commands can use it."}}
  ]
}
</script>
