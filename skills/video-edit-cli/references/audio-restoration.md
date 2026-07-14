# Audio restoration and mastering

Audio enhancement is adaptive: characterize first, then choose the lightest
treatment that meets the request. Never apply neural restoration blindly, and
always keep a mastering-only baseline candidate.

1. **Preflight.** Run `video-edit-cli doctor --workflow audio-restoration`
   before choosing DeepFilterNet. A failed import check identifies the exact
   runtime layer that is absent or incompatible; do not interpret every backend
   failure as meaning the `df` package itself is missing.
2. **Characterize.** `video-edit-cli audio analyze --input <wav>` reports
   integrated loudness, true peak, loudness range, clipping indicators, silence
   spans, and a high-frequency-dropoff signal. Decide from these numbers whether
   the recording is clean, noisy, clipped, or band-limited.
3. **Baseline.** `video-edit-cli audio master --input <wav> --output <ws>/renders/mastered.wav`
   applies the deterministic chain (highpass, gentle compression, two-pass
   BS.1770 loudness normalization). Targets default to −16 LUFS / −1.5 dBTP;
   take project targets from the external profile when one is supplied.
4. **Denoise only when analysis or listening justifies it.**
   `video-edit-cli audio denoise --input <wav> --output <ws>/renders/denoised.wav
   --backend deepfilternet` (requires the `df` extra). Master the denoised
   result too, so candidates differ only in restoration.
5. **Compare at matched loudness.** `video-edit-cli audio compare --input <a>
   --input <b> --output-dir <ws>/reports/ab` writes loudness-matched excerpts
   plus metrics. Metrics rank candidates; they do not prove speech still sounds
   natural — review the excerpts before choosing, and say which candidate you
   chose and why.
6. **Put approved audio back into video when needed.** `video-edit-cli audio
   replace --video <render> --audio <mastered.wav> --output <new-render>
   --workspace <ws>` copies the existing video stream and encodes the replacement
   audio. It rejects material duration mismatches instead of silently drifting
   or truncating. This is an atomic mux operation, not an editorial decision:
   the agent must choose the approved candidate first.
7. **Measure the delivered container.** Run `audio analyze` on the final video,
   not only its WAV input, because lossy delivery encoding can move peak and
   loudness measurements slightly. Re-run the relevant `output validate` check
   for canvas, streams, and duration after replacement.

Invariants: intermediates stay lossless WAV (the commands enforce this);
originals are never replaced; every processed file keeps its provenance
sidecar naming backend, model, and parameters. If the recording is damaged
beyond conservative treatment (heavy clipping, missing bandwidth), report the
limitation rather than reaching for reconstruction that alters the voice.

Completion: the final delivered container meets the requested loudness/true-peak
targets (verify with `audio analyze`), the mastering-only baseline still exists
as an artifact, any denoising applied is justified in your summary, and an A/B
listening review explicitly checks pauses/noise floor, sibilants, plosives, and
low-energy speech for unnatural suppression or pumping.
