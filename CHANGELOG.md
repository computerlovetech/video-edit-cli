# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-07-14

### Added

- `doctor` command: checks local dependencies for an editing workflow.
- `audio replace` command: swap a video's audio stream while copying the video
  stream, with codec/bitrate options and a duration-mismatch guard.
- Subtitle improvements: short-form cue reflow options (`--max-words`,
  `--max-chars`, `--max-duration`) and burn-in styling controls (font, colors,
  outline, shadow, alignment).
- Cut review improvements: inspect a single cut by index or all cuts, plus
  technical-only checks (streams, canvas, duration, loudness, subtitles).

### Changed

- Improved audio restoration primitives: denoising, mastering, analysis, and
  diagnostics.
- Renamed the bundled agent skill from `video-editor` to `video-edit-cli` to
  match the package and the skills.sh install command.

### Docs

- New MkDocs documentation site deployed to GitHub Pages.
- Open-source prep: MIT license, README refresh with badges and example prompts.

## [0.1.1] - 2026-07-12

### Added

- `skills list` and `skills install` subcommands: the `video-editor` agent skill now
  ships inside the package and can be installed into a project with
  `video-edit-cli skills install` (defaults to `.claude/skills`).
- `create-clips` skill: derives publishable social clips (Shorts, YouTube,
  LinkedIn) from a long-form recording. Distributed via agr only; intentionally
  not bundled in the wheel.

### Changed

- Build backend switched from `uv_build` to `hatchling` so the repository-root
  `skills/` directory can be bundled into the wheel.

## [0.1.0] - 2026-07-12

### Added

- Initial release, extracted from the Ship the Diff repository: headless,
  project-agnostic video-editing CLI (`video-edit-cli`) with atomic subcommands
  for workspaces, inspection, transcription, edit plans, rendering, audio
  mastering, subtitles, multicam sync, reframing, and short-form derivation.
- Companion `video-editor` agent skill.
- Optional extras: `mlx` (local transcription) and `df` (DeepFilterNet denoising).
