"""Edit-plan loading and validation.

A plan is an ordered keep-list: each timeline clip keeps [in, out) of a source,
with an editorial reason. Validation is structural (schema) plus semantic
(references, ranges against real media, ordering/overlap per source).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from video_editor import media, schemas
from video_editor.errors import InvalidInputError


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InvalidInputError(f"plan file not found: {path}")
    try:
        plan: dict[str, Any] = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise InvalidInputError(f"plan {path} is not valid JSON: {exc}") from exc
    return plan


def validate(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate a plan; return summary data (durations, boundaries)."""
    schemas.validate(plan, "edit-plan.schema.json")

    errors: list[str] = []
    sources: dict[str, Path] = {}
    durations: dict[str, float] = {}
    for record in plan["sources"]:
        if record["id"] in sources:
            errors.append(f"duplicate source id '{record['id']}'")
            continue
        source_path = Path(record["path"])
        sources[record["id"]] = source_path
        if not source_path.is_file():
            errors.append(f"source '{record['id']}' file not found: {source_path}")

    if errors:
        raise InvalidInputError("invalid plan: " + "; ".join(errors))

    for source_id, source_path in sources.items():
        durations[source_id] = media.duration_of(source_path)

    last_out: dict[str, float] = {}
    output_time = 0.0
    boundaries: list[float] = []
    for index, clip in enumerate(plan["timeline"]):
        label = f"timeline[{index}]"
        source_id = clip["source"]
        if source_id not in sources:
            errors.append(f"{label}: unknown source '{source_id}'")
            continue
        video_source = clip.get("video_source")
        if video_source is not None and video_source not in sources:
            errors.append(f"{label}: unknown video_source '{video_source}'")
        clip_in, clip_out = clip["in"], clip["out"]
        if clip_in >= clip_out:
            errors.append(f"{label}: in ({clip_in}) must be < out ({clip_out})")
            continue
        duration = durations[source_id]
        if clip_out > duration + 0.05:
            errors.append(
                f"{label}: out ({clip_out}) exceeds source '{source_id}' "
                f"duration ({duration:.3f})"
            )
            continue
        if source_id in last_out and clip_in < last_out[source_id]:
            errors.append(
                f"{label}: overlaps or reorders earlier clip on source "
                f"'{source_id}' (in {clip_in} < previous out {last_out[source_id]})"
            )
        last_out[source_id] = max(last_out.get(source_id, 0.0), clip_out)
        output_time += clip_out - clip_in
        boundaries.append(round(output_time, 6))

    if errors:
        raise InvalidInputError("invalid plan: " + "; ".join(errors))

    return {
        "plan_id": plan["plan_id"],
        "clip_count": len(plan["timeline"]),
        "output_duration": round(output_time, 6),
        "boundaries": boundaries[:-1],
    }
