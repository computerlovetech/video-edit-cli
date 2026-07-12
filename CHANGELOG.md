# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
