# Transcription

For dialogue media the transcript is the primary editing surface — but not the
only one: reactions, gestures, camera usability, and continuity still need
targeted visual inspection (frames, filmstrips, previews).

Workflow:

1. `video-edit-cli transcript create --input <audio-or-video> --output <ws>/analysis/transcript.json`
   runs the local backend (default `mlx-whisper`; requires the `mlx` extra) and
   writes the authoritative word-level JSON. Pass `--source-id` so the transcript
   records which workspace source it describes. Transcribing the extracted
   canonical WAV is faster than the full video.
2. `transcript pack` derives a compact `[start-end] text` view sized for your
   context. Read the packed view; treat the JSON as the source of truth for
   times.
3. `transcript search --query "<phrase>"` returns word-aligned start/end times
   plus segment context. Use it to locate passages precisely instead of scanning.

Rules:

- Every editorial time you use must come from transcript JSON times or direct
  media inspection — never estimate timestamps from memory of the packed view's
  prose.
- Transcript evidence is insufficient when the decision depends on what is
  visible (reactions, demonstrations, camera choice) or on sound that is not
  speech (music, noise, overlaps). Inspect the range visually/aurally before
  deciding.
- If transcription fails or the backend is unavailable, fall back to waveform +
  filmstrip inspection and say so; do not pretend acoustic evidence equals
  semantic understanding.
