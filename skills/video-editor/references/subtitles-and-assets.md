# Packaging: profiles, subtitles, assets, master render

Project identity — canvases, codecs, loudness targets, music, brand assets,
fonts, subtitle style — lives in an external YAML project profile passed by
path, never in the skill or your defaults. Without a profile you can still
preview; a publishable master needs one.

Order of operations for a packaged episode:

1. **Validate the profile's assets.** `video-edit-cli asset inspect --input <file>`
   for each intro/outro/music/font/image the profile references; loading the
   profile also fails on missing files. Fix or report missing assets before
   rendering.
2. **Master render.** `video-edit-cli render master --plan <plan> --profile
   <profile.yaml> --profile-name <name> --output <ws>/renders/<name>.mp4`
   compiles the approved plan at the profile canvas/codec, mixes profile music
   with speech-keyed ducking when declared, and normalizes loudness to the
   profile targets. It writes the same boundary manifest as preview renders —
   review cuts on the master too if timing changed.
3. **Subtitles.** `video-edit-cli subtitles create --manifest <render manifest>
   --transcript <transcript.json> --output-srt … --output-vtt …` maps transcript
   words through the kept ranges into output time (removed ranges drop their
   words). Transcripts must carry the plan's source id — pass `--source-id` at
   `transcript create` time. Attach with `subtitles render` (`--mode mux`
   default; `burn` requires an ffmpeg build with libass and fails cleanly
   otherwise).
4. **Validate the deliverable.** `video-edit-cli output validate --input <file>
   --profile <profile.yaml> --profile-name <name> --expect-duration <s>
   [--expect-subtitles --subtitles <srt>]` checks streams, canvas, frame rate,
   duration, loudness/true peak, and subtitle timing. The command reports
   `passed` with an issues list — the deliverable is not done until `passed`
   is true or each issue is explicitly accepted by the user.
