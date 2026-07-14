---
name: create-clips
description: Derive several publishable social clips (YouTube Shorts, standard YouTube videos, LinkedIn) from a long-form recording — podcast episode, interview, vlog, talk, or livestream. Use when the user asks to make clips, shorts, highlights, or teasers from a video, especially after a main edit already exists. Builds on the video-edit-cli skill and the video-edit-cli CLI.
---

You turn one long recording into a small set of clips worth publishing, each
packaged with everything needed to post it. The `video-edit-cli` skill and the
`video-edit-cli` CLI are your workbench for all media mechanics; this skill owns
the clip-release workflow. Read the `video-edit-cli` skill first if it is not
already loaded — its invariants (immutable sources, evidence before edits,
validate before rendering) all apply here.

## Inputs

Establish these before cutting anything; ask only for what you cannot infer.

- **Source**: an existing video-edit-cli workspace (preferred — reuse its
  transcript, plans, and hashes) or standalone media (then `workspace init` first).
- **Clip count**: default 3–5 if unspecified.
- **Full-episode URL**: needed for descriptions; use a `[LINK]` placeholder and
  say so if unknown.
- **Language**: of the recording; copy is written in the same language unless
  asked otherwise.
- **Formats**: default is both 9:16 vertical and 16:9 horizontal per clip.
- **Brand/voice**: any project profile, tone guidance, or naming conventions the
  hosting repo provides (e.g. a project-specific publishing skill or profile YAML).

## Method

1. **Know the material.** Reuse the workspace transcript if present; otherwise
   transcribe (see the video-edit-cli transcription reference). Skim the full
   transcript before selecting anything.
2. **Select moments editorially.** Choose self-contained segments with a hook in
   the first seconds, one clear idea, and a natural ending — a claim, a result, a
   story, a provocation. You choose; no command picks highlights for you. Target
   20–90 s for Shorts. Prefer moments that stand alone without episode context.
3. **Tighten boundaries and classify layouts.** Use word-level transcript timing
   to start on the first word of a sentence and end on a completed thought.
   Inspect a dense filmstrip over every complete candidate and frames around all
   scene changes. Record solo, split-screen, screen-share, and transition spans;
   mixed layouts require per-segment crops in the short plan.
4. **Render both formats per clip.** Vertical via `short create-plan` (mind the
   vertical-video reference — check for burned-in captions before cropping faces);
   horizontal as a straight excerpt at source aspect. Master audio to the
   platform loudness target and run `output validate` on every deliverable.
5. **Subtitles.** Burn styled subtitles into both renders when the source has
   none; always keep `subtitles.srt` and `subtitles.vtt` sidecars. If the source
   already has burned-in captions, do not double-caption — mux instead.
6. **Write the copy.** For each clip, in the recording's language:
   - `youtube-short.txt` — clickable title (line 1) + short description with the
     episode link and relevant hashtags.
   - `youtube-video.txt` — title + fuller description linking the episode.
   - `linkedin.txt` — a self-contained post (hook, substance, link); no
     clickbait that the clip doesn't cash.
7. **Package and review.** Assemble the layout in
   [references/package-format.md](references/package-format.md), review every
   render's cut boundaries and framing, and report any residual defects honestly.
   For each vertical render, inspect a dense full-range filmstrip (at least 15
   samples per minute) plus both sides of every transform boundary. Technical
   output validation never substitutes for this visual review.

## Boundaries

- Never modify the main edit or the source media; clips are derived artifacts.
- Do not publish anywhere — the deliverable is the reviewed package. Publishing
  is owned by project-specific skills (e.g. a podcast's release skill).
- Project-specific tone, branding, output location, and naming conventions come
  from the hosting repo; when absent, use the defaults above and say so.
