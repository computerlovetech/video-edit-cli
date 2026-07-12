# Audio restoration and mastering

Audio enhancement is adaptive: characterize first, then choose the lightest
treatment that meets the request. Never apply neural restoration blindly, and
always keep a mastering-only baseline candidate.

1. **Characterize.** `video-edit-cli audio analyze --input <wav>` reports
   integrated loudness, true peak, loudness range, clipping indicators, silence
   spans, and a high-frequency-dropoff signal. Decide from these numbers whether
   the recording is clean, noisy, clipped, or band-limited.
2. **Baseline.** `video-edit-cli audio master --input <wav> --output <ws>/renders/mastered.wav`
   applies the deterministic chain (highpass, gentle compression, two-pass
   BS.1770 loudness normalization). Targets default to −16 LUFS / −1.5 dBTP;
   take project targets from the external profile when one is supplied.
3. **Denoise only when analysis or listening justifies it.**
   `video-edit-cli audio denoise --input <wav> --output <ws>/renders/denoised.wav
   --backend deepfilternet` (requires the `df` extra). Master the denoised
   result too, so candidates differ only in restoration.
4. **Compare at matched loudness.** `video-edit-cli audio compare --input <a>
   --input <b> --output-dir <ws>/reports/ab` writes loudness-matched excerpts
   plus metrics. Metrics rank candidates; they do not prove speech still sounds
   natural — review the excerpts before choosing, and say which candidate you
   chose and why.

Invariants: intermediates stay lossless WAV (the commands enforce this);
originals are never replaced; every processed file keeps its provenance
sidecar naming backend, model, and parameters. If the recording is damaged
beyond conservative treatment (heavy clipping, missing bandwidth), report the
limitation rather than reaching for reconstruction that alters the voice.

Completion: the delivered audio meets the requested loudness/true-peak targets
(verify with `audio analyze`), the mastering-only baseline still exists as an
artifact, and any denoising applied is justified in your summary.
