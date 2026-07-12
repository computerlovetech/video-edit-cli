# Multi-camera editing

Applies when multiple synchronized (or synchronizable) recordings cover the
same session — extra cameras, separate audio recorders, screen captures.

1. **Synchronize first.** `video-edit-cli sync analyze --reference <a> --other <b>`
   estimates the offset by audio correlation and reports candidates and a
   confidence ratio; it never rewrites sources. Verify a low-confidence result
   by inspecting waveforms around the claimed alignment before trusting it.
2. **Apply explicitly.** `video-edit-cli sync apply --input <b> --offset <s>
   --output <ws>/renders/b-aligned.mp4` (or a `.json` output for mapping
   metadata only). All plan times then refer to the aligned timeline.
3. **Relate sources to roles.** Record which source is which camera/mic in the
   workspace `--role` labels; project camera aliases live in the external
   profile, not here.
4. **Choose cameras with evidence.** A clip's `video_source` selects the camera
   while audio stays on the clip's `source`. Decide switches from transcript
   context plus filmstrips of each candidate camera — check the speaker is
   usable (framing, focus, reactions) on the camera you pick.
5. **Review switches like cuts.** Every camera switch is a boundary in the
   render manifest; inspect each with `cut inspect` for continuity (posture,
   gaze, gesture) across the switch.

Completion: sources verified aligned, every switch justified by inspected
evidence, and the single-source path still used when only one camera is usable.
