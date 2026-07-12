"""Derived transcript views: packed text for agent context, time-aligned search.

Transcript JSON is authoritative; these views are conveniences derived from it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from video_editor import schemas
from video_editor.errors import InvalidInputError


def load_transcript(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InvalidInputError(f"transcript file not found: {path}")
    document: dict[str, Any] = json.loads(path.read_text())
    schemas.validate(document, "transcript.schema.json")
    return document


def pack(document: dict[str, Any]) -> str:
    """Render a compact `[start-end] (speaker) text` line per segment."""
    lines = [
        f"# transcript of {document['source']['path']}",
        f"# language={document['language']} backend={document['backend']} "
        f"model={document['model']}",
    ]
    for segment in document["segments"]:
        speaker = f" ({segment['speaker']})" if segment.get("speaker") else ""
        lines.append(
            f"[{segment['start']:.2f}-{segment['end']:.2f}]{speaker} {segment['text'].strip()}"
        )
    return "\n".join(lines) + "\n"


def _normalize(text: str) -> str:
    return re.sub(r"[^\w]+", " ", text.lower()).strip()


def search(
    document: dict[str, Any], query: str, max_results: int = 20
) -> list[dict[str, Any]]:
    """Find query occurrences in the word stream; return time-aligned matches."""
    query_tokens = _normalize(query).split()
    if not query_tokens:
        raise InvalidInputError("search query is empty after normalization")

    words: list[dict[str, Any]] = []
    for segment_index, segment in enumerate(document["segments"]):
        for word in segment["words"]:
            token = _normalize(word["text"])
            if token:
                words.append(
                    {
                        "token": token,
                        "start": word["start"],
                        "end": word["end"],
                        "segment_index": segment_index,
                    }
                )

    matches: list[dict[str, Any]] = []
    span = len(query_tokens)
    for i in range(len(words) - span + 1):
        window = words[i : i + span]
        if [w["token"] for w in window] == query_tokens:
            segment = document["segments"][window[0]["segment_index"]]
            matches.append(
                {
                    "start": window[0]["start"],
                    "end": window[-1]["end"],
                    "text": " ".join(w["token"] for w in window),
                    "segment_index": window[0]["segment_index"],
                    "segment_start": segment["start"],
                    "segment_end": segment["end"],
                    "segment_text": segment["text"].strip(),
                }
            )
            if len(matches) >= max_results:
                break
    return matches
