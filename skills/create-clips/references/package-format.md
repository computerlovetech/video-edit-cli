# Clip package format

One directory per clip, numbered in publish order, slug from the clip's topic:

```text
clips/
  01-<topic-slug>/
    vertical.mp4        # 9:16 master, validated
    horizontal.mp4      # 16:9 master, validated
    subtitles.srt
    subtitles.vtt
    youtube-short.txt   # title on line 1, blank line, description
    youtube-video.txt   # title on line 1, blank line, description
    linkedin.txt        # complete post text
    manifest.json
```

`manifest.json` records provenance and the editorial decision:

```json
{
  "schema_version": "1",
  "slug": "01-<topic-slug>",
  "source": {"path": "…", "sha256": "…"},
  "range": {"start": 123.45, "end": 187.2},
  "reason": "why this moment was selected",
  "language": "da",
  "episode_url": "https://…",
  "renders": {
    "vertical": {"file": "vertical.mp4", "canvas": "1080x1920"},
    "horizontal": {"file": "horizontal.mp4", "canvas": "1920x1080"}
  },
  "validation": "passed"
}
```

Rules:

- Every render keeps its `*.provenance.json` sidecar next to it.
- Formats a clip intentionally omits are left out of `renders` (and the reason
  noted in the summary), never shipped unvalidated.
- If the episode URL is unknown, use `[LINK]` in all copy and `null` in the
  manifest, and flag it in the final summary.
