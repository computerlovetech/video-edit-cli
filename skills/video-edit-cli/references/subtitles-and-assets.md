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
   `transcript create` time. For short-form delivery, reflow with `--max-words`,
   `--max-chars`, and `--max-duration`. Attach with `subtitles render` (`--mode
   mux` default); burn mode accepts ASS styling options such as `--font`,
   `--font-size`, `--outline-width`, `--alignment`, and `--margin-v`. Burn mode
   requires libass; check it first with `doctor --workflow vertical-captioned`.
   These numeric style values use libass/ASS script units, **not output pixels**.
   Plain SRT/VTT commonly render on a 384x288 script canvas, so a practical
   bold social-caption starting point is `--font-size 9.5 --outline-width 1
   --shadow 0.5 --alignment 2 --margin-v 42`; inspect a burned frame before
   rendering the full deliverable. Values such as `--font-size 60 --margin-v
   280` are pixel-like assumptions and can push captions off-canvas.
4. **Validate the deliverable.** `video-edit-cli output validate --input <file>
   --profile <profile.yaml> --profile-name <name> --expect-duration <s>
   [--expect-subtitles --subtitles <srt>]` checks streams, canvas, frame rate,
   duration, loudness/true peak, and subtitle timing. The command reports
   `passed` with an issues list and explicitly marks visual/editorial validation
   as not performed. The deliverable is not done until technical validation and
   the relevant human/agent visual review both pass.
