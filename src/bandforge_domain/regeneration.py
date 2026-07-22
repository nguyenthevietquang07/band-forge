"""Immutable, deterministic SAFE regeneration of a bounded event scope."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from bandforge_domain.arrangements import validate_arrangement_document

RegenerationMode = Literal["SAFE"]


@dataclass(frozen=True)
class RegenerationResult:
    document: dict[str, Any]
    manifest: dict[str, Any]


def regenerate_scoped(
    candidate: Mapping[str, Any],
    track_ids: Sequence[str],
    measure_ids: Sequence[str],
    seed: int,
    mode: RegenerationMode = "SAFE",
) -> RegenerationResult:
    """Create an immutable candidate revision changing only scoped event velocities."""
    _require_accepted_candidate(candidate)
    if mode != "SAFE":
        raise ValueError("Only SAFE regeneration is supported")
    if seed < 0:
        raise ValueError("regeneration seed must be non-negative")
    selected_tracks = tuple(dict.fromkeys(track_ids))
    selected_measures = tuple(dict.fromkeys(measure_ids))
    if not selected_tracks:
        raise ValueError("regeneration requires at least one track")
    if not selected_measures:
        raise ValueError("regeneration requires at least one measure")

    known_tracks = {track["id"] for track in candidate["tracks"]}
    known_measures = {measure["id"] for measure in candidate["measures"]}
    if not set(selected_tracks) <= known_tracks:
        raise ValueError("regeneration track scope contains an unknown track")
    if not set(selected_measures) <= known_measures:
        raise ValueError("regeneration measure scope contains an unknown measure")

    parent_version_id = candidate["versionId"]
    identity = {
        "parentVersionId": parent_version_id,
        "trackIds": selected_tracks,
        "measureIds": selected_measures,
        "seed": seed,
        "mode": mode,
    }
    new_version_id = "regen_" + _digest(identity)[:24]
    document = deepcopy(candidate)
    changed_event_ids: list[str] = []
    in_scope_event_ids: set[str] = set()
    for track in document["tracks"]:
        if track["id"] not in selected_tracks:
            continue
        for event in track["events"]:
            if _event_measure_id(event, document["measures"]) not in selected_measures:
                continue
            in_scope_event_ids.add(event["id"])
            if "velocity" not in event:
                continue
            event["velocity"] = _safe_velocity(event["velocity"], seed, event["id"])
            changed_event_ids.append(event["id"])
    if not changed_event_ids:
        raise ValueError("regeneration scope contains no mutable events")

    outside_before = _event_content_hash(candidate, in_scope_event_ids)
    outside_after = _event_content_hash(document, in_scope_event_ids)
    source_refs = list(candidate["sourceRefs"])
    manifest = {
        "parentVersionId": parent_version_id,
        "newVersionId": new_version_id,
        "trackIds": list(selected_tracks),
        "measureIds": list(selected_measures),
        "seed": seed,
        "mode": mode,
        "sourceRevisionIds": [reference["sourceRevisionId"] for reference in source_refs],
        "rightsAttested": all(reference["rightsAttested"] is True for reference in source_refs),
        "provenance": deepcopy(
            candidate.get("extensions", {}).get(
                "bandforge.generation-lineage", candidate["provenance"]
            )
        ),
        "changedEventIds": changed_event_ids,
        "outsideScopeContentHashBefore": outside_before,
        "outsideScopeContentHashAfter": outside_after,
        "preservedOutsideScope": outside_before == outside_after,
    }
    document["versionId"] = new_version_id
    document["parentVersionId"] = parent_version_id
    document["status"] = "CANDIDATE"
    document["provenance"] = {
        **document["provenance"],
        "createdBy": "REPAIRER",
        "engineVersion": "safe-regeneration-0.1.0",
        "seed": seed,
        "validatorVersion": candidate["provenance"]["validatorVersion"],
    }
    document["extensions"]["bandforge.regeneration"] = deepcopy(manifest)
    document["validationSummary"] = {
        **document["validationSummary"],
        "runId": "validation_" + new_version_id,
        "status": "VALID",
        "errorCount": 0,
        "warningCount": 0,
    }
    validate_arrangement_document(document)
    return RegenerationResult(document=document, manifest=manifest)


def _require_accepted_candidate(candidate: Mapping[str, Any]) -> None:
    if candidate.get("status") not in {"CANDIDATE", "ACCEPTED"}:
        raise ValueError("regeneration requires an accepted candidate")
    summary = candidate.get("validationSummary", {})
    if summary.get("status") != "VALID" or summary.get("errorCount") != 0:
        raise ValueError("regeneration requires an accepted candidate")
    try:
        validate_arrangement_document(candidate)
    except ValueError as error:
        raise ValueError(f"candidate schema invalid: {error}") from error
    if not all(reference.get("rightsAttested") is True for reference in candidate["sourceRefs"]):
        raise ValueError("regeneration requires rights-attested source references")


def _event_measure_id(
    event: Mapping[str, Any], measures: Sequence[Mapping[str, Any]]
) -> str | None:
    for measure in measures:
        measure_end = measure["startTick"] + measure["durationTicks"]
        if measure["startTick"] <= event["startTick"] < measure_end:
            return measure["id"]
    return None


def _safe_velocity(velocity: int, seed: int, event_id: str) -> int:
    digest = hashlib.sha256(f"{seed}:{event_id}".encode()).digest()
    delta = 1 if digest[0] % 2 else -1
    next_velocity = velocity + delta
    if next_velocity < 1 or next_velocity > 127:
        next_velocity = velocity - delta
    return next_velocity


def _event_content_hash(document: Mapping[str, Any], excluded_event_ids: set[str]) -> str:
    events = [
        {"trackId": track["id"], "event": event}
        for track in document["tracks"]
        for event in track["events"]
        if event["id"] not in excluded_event_ids
    ]
    encoded = json.dumps(events, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
