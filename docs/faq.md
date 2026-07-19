---
title: FAQ — AI agent video editing
description: >-
  Answers to common questions: free Opus Clip alternatives without watermarks,
  editing video with Claude Code, removing silences from podcasts, making
  YouTube Shorts automatically, and keeping footage local.
---

# FAQ

## Can an AI coding agent like Claude Code really edit video?

Yes. video-edit-cli gives the agent fixed commands for transcription, cutting,
reframing, subtitles, and audio mastering. A bundled [skill](skills.md) teaches
the agent to gather evidence, write an edit plan that explains each cut, then
render and review. You ask in plain language; the agent edits on your machine.

## Is there a free Opus Clip alternative without watermarks or credits?

video-edit-cli is open source and free, with no watermarks, per-clip credits,
or clip expiry. Hosted clip apps charge $15–29 per month and set per-minute
limits. An hour-long video can use much of a starter plan. Here, you pay only
for your own compute.

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

The editing model is similar: you cut video through its transcript. But your AI
agent runs this free, local CLI instead of a paid desktop app. The agent reads
the transcript and writes the cuts. A reviewable edit plan records each cut and
its reason.

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

You can audit them. In each edit plan, every cut has a written `reason`. You or
the agent reviews each cut before rendering. Provenance sidecars let you trace
and reproduce any edit. There is no hidden "virality score."

## Does it run on Windows?

The CLI supports macOS and Linux. Use WSL on Windows, which remains untested.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {"@type": "Question", "name": "Can an AI coding agent like Claude Code really edit video?", "acceptedAnswer": {"@type": "Answer", "text": "Yes. video-edit-cli gives the agent fixed commands for transcription, cutting, reframing, subtitles, and audio mastering. A bundled skill teaches it to gather evidence, write an edit plan that explains each cut, then render and review locally."}},
    {"@type": "Question", "name": "Is there a free Opus Clip alternative without watermarks or credits?", "acceptedAnswer": {"@type": "Answer", "text": "Yes. video-edit-cli is open source and free, with no watermarks, per-clip credits, or clip expiry. Your AI coding agent runs it locally."}},
    {"@type": "Question", "name": "How do I make YouTube Shorts from a long video automatically?", "acceptedAnswer": {"@type": "Answer", "text": "Install the video-edit-cli skill and ask your coding agent to make Shorts from the video. It transcribes, picks the strongest moments, reframes to 9:16, burns in captions, and renders each clip locally."}},
    {"@type": "Question", "name": "How do I remove silences, filler words, and false starts from a podcast?", "acceptedAnswer": {"@type": "Answer", "text": "Ask your agent to edit the recording into a publishable episode. It cuts from a word-level transcript, so it distinguishes dramatic pauses from dead air and removes false starts without clipping the retake."}},
    {"@type": "Question", "name": "Does my footage get uploaded anywhere?", "acceptedAnswer": {"@type": "Answer", "text": "No. Everything runs locally, including transcription. Source files are immutable and every derived file gets a provenance sidecar."}},
    {"@type": "Question", "name": "Which coding agents does it work with?", "acceptedAnswer": {"@type": "Answer", "text": "Any agent that supports skills: Claude Code, Codex, Cursor, GitHub Copilot, Pi, Amp, and others. The CLI is plain shell + JSON, so any agent that can run commands can use it."}}
  ]
}
</script>
