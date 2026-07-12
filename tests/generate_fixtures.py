"""Generate small deterministic media fixtures with ffmpeg.

Fixtures are generated on demand (never committed):

- main.mp4: 8 s, 640x360 30 fps testsrc (its pattern includes a visual counter); audio is
  speech-like tone bursts separated by silence, with a repeated "false start"
  shaped burst pattern at the beginning.
- offset.mp4: the same content delayed by a known offset (for sync tests later).
- audio_only.wav: the fixture audio without video.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

MAIN_DURATION = 8.0
KNOWN_OFFSET = 1.5

# Tone bursts (start, end, freq Hz): two identical bursts up front emulate a
# false start, then distinct "sentences" separated by silence.
BURSTS = [
    (0.5, 1.2, 440),
    (1.6, 2.3, 440),
    (3.0, 4.4, 660),
    (5.2, 6.8, 550),
]


def _audio_expr() -> str:
    parts = []
    for start, end, freq in BURSTS:
        parts.append(f"if(between(t,{start},{end}),0.6*sin(2*PI*{freq}*t),0)")
    return "'" + "+".join(parts) + "'"


def _run(args: list[str]) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to generate fixtures")
    subprocess.run(
        [ffmpeg, "-hide_banner", "-nostdin", "-y", *args],
        check=True,
        capture_output=True,
    )


def generate_main(path: Path, duration: float = MAIN_DURATION) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size=640x360:rate=30:duration={duration}",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc={_audio_expr()}:s=48000:d={duration}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(path),
        ]
    )
    return path


def generate_offset(path: Path, offset: float = KNOWN_OFFSET) -> Path:
    """Same audio content delayed by `offset` seconds, video included."""
    path.parent.mkdir(parents=True, exist_ok=True)
    duration = MAIN_DURATION + offset
    delayed = (
        "'"
        + "+".join(
            f"if(between(t,{start + offset},{end + offset}),0.6*sin(2*PI*{freq}*(t-{offset})),0)"
            for start, end, freq in BURSTS
        )
        + "'"
    )
    _run(
        [
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size=320x240:rate=25:duration={duration}",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc={delayed}:s=44100:d={duration}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            str(path),
        ]
    )
    return path


def generate_audio_only(path: Path, duration: float = MAIN_DURATION) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc={_audio_expr()}:s=48000:d={duration}",
            "-c:a",
            "pcm_s16le",
            str(path),
        ]
    )
    return path


def generate_music(path: Path, duration: float = 3.0) -> Path:
    """Quiet looping music bed for packaging tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc='0.2*sin(2*PI*220*t)+0.1*sin(2*PI*330*t)':s=48000:d={duration}",
            "-c:a",
            "pcm_s16le",
            str(path),
        ]
    )
    return path


def generate_image(path: Path) -> Path:
    """One-frame test image asset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=320x180:rate=1:duration=1",
            "-frames:v",
            "1",
            str(path),
        ]
    )
    return path


if __name__ == "__main__":
    root = Path(__file__).parent / "fixtures"
    print(generate_main(root / "main.mp4"))
    print(generate_offset(root / "offset.mp4"))
    print(generate_audio_only(root / "audio_only.wav"))
