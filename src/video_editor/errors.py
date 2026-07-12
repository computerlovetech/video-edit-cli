"""Structured errors with stable codes for the CLI contract."""

from __future__ import annotations


class VideoEditorError(Exception):
    """Failure with a stable machine-readable code and actionable message."""

    def __init__(self, code: str, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code


class MissingBinaryError(VideoEditorError):
    def __init__(self, binary: str) -> None:
        super().__init__(
            "missing-binary",
            f"required external binary '{binary}' was not found on PATH; "
            f"install FFmpeg (e.g. `brew install ffmpeg`) and retry",
            exit_code=3,
        )


class InvalidInputError(VideoEditorError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid-input", message, exit_code=2)


class ToolFailureError(VideoEditorError):
    def __init__(self, message: str) -> None:
        super().__init__("tool-failure", message, exit_code=4)
