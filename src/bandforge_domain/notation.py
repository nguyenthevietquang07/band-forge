"""Deterministic, dependency-free MusicXML 4.0 artifacts for accepted candidates."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from bandforge_domain.arrangements import validate_arrangement_document


@dataclass(frozen=True)
class MusicXmlArtifact:
    data: bytes
    manifest: dict[str, Any]


_PITCH_NAMES = (
    ("C", 0),
    ("C", 1),
    ("D", 0),
    ("D", 1),
    ("E", 0),
    ("F", 0),
    ("F", 1),
    ("G", 0),
    ("G", 1),
    ("A", 0),
    ("A", 1),
    ("B", 0),
)
_ROOT_STEPS = ("C", "C", "D", "D", "E", "F", "F", "G", "G", "A", "A", "B")
_ROOT_ALTERS = (0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0)
_KIND_NAMES = {
    "MAJOR": "major",
    "MINOR": "minor",
    "DIMINISHED": "diminished",
    "AUGMENTED": "augmented",
    "SUS2": "suspended-second",
    "SUS4": "suspended-fourth",
    "POWER": "power",
    "OTHER": "other",
}
_DRUM_DISPLAY = {
    "KICK": ("F", 3),
    "SNARE": ("C", 5),
    "CLOSED_HAT": ("G", 5),
    "OPEN_HAT": ("G", 5),
    "RIDE": ("F", 5),
    "CRASH": ("A", 5),
    "LOW_TOM": ("E", 5),
    "MID_TOM": ("G", 5),
    "HIGH_TOM": ("A", 5),
    "PERCUSSION": ("C", 5),
}
_DURATION_TYPES = {
    240: "16th",
    480: "eighth",
    960: "quarter",
    1920: "half",
    3840: "whole",
}


def validate_generation_lineage(value: Any) -> dict[str, Any]:
    """Validate and return the canonical typed generation-lineage object."""
    if not isinstance(value, Mapping):
        raise ValueError("MusicXML generation lineage must be an object")
    required_strings = (
        "engineVersion",
        "stylePackVersion",
        "validatorVersion",
        "provenance",
    )
    seed = value.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ValueError("MusicXML generation lineage seed is invalid")
    for field in required_strings:
        field_value = value.get(field)
        if not isinstance(field_value, str) or not field_value:
            raise ValueError(f"MusicXML generation lineage {field} is invalid")
    input_revision_set = value.get("inputRevisionSet")
    if not isinstance(input_revision_set, list) or not input_revision_set:
        raise ValueError("MusicXML generation lineage inputRevisionSet is invalid")
    if not all(
        isinstance(revision, str) and bool(revision)
        for revision in input_revision_set
    ):
        raise ValueError("MusicXML generation lineage inputRevisionSet is invalid")
    return dict(value)


def export_candidate_musicxml(candidate: Mapping[str, Any]) -> MusicXmlArtifact:
    """Render an accepted canonical candidate as deterministic MusicXML 4.0."""
    lineage = require_accepted_candidate(candidate)
    _require_measure_boundaries(candidate)
    data = _render_musicxml(candidate)
    validate_musicxml(data, candidate)
    source_refs = list(candidate["sourceRefs"])
    manifest = {
        "artifactType": "MUSICXML_SCORE_PARTWISE",
        "format": "MusicXML 4.0",
        "ticksPerQuarter": candidate["global"]["ticksPerQuarter"],
        "sourceRevisionIds": [reference["sourceRevisionId"] for reference in source_refs],
        "acceptedVersionId": candidate["versionId"],
        "rightsAttested": all(reference["rightsAttested"] is True for reference in source_refs),
        "lineage": lineage,
        "trackIds": [track["id"] for track in candidate["tracks"]],
        "contentHash": "sha256:" + hashlib.sha256(data).hexdigest(),
    }
    return MusicXmlArtifact(data=data, manifest=manifest)


def validate_musicxml(data: bytes, candidate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate MusicXML structure, divisions, part identity, and measure bounds."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise ValueError(f"MusicXML is malformed XML: {error}") from error
    if _local_name(root.tag) != "score-partwise" or root.get("version") != "4.0":
        raise ValueError("MusicXML root must be score-partwise version 4.0")

    part_list = _child(root, "part-list")
    score_parts = _children(part_list, "score-part") if part_list is not None else []
    parts = _children(root, "part")
    if not score_parts or len(score_parts) != len(parts):
        raise ValueError("MusicXML part-list and part counts do not match")
    if candidate is not None and len(parts) != len(candidate.get("tracks", [])):
        raise ValueError("MusicXML part count does not match candidate tracks")

    measures = candidate.get("measures", []) if candidate is not None else []
    if candidate is not None and len(measures) == 0:
        raise ValueError("candidate must contain measures")
    for index, (score_part, part) in enumerate(zip(score_parts, parts, strict=True)):
        expected_part_id = f"P{index + 1:03d}"
        if score_part.get("id") != expected_part_id or part.get("id") != expected_part_id:
            raise ValueError("MusicXML part identity is not deterministic")
        part_measures = _children(part, "measure")
        if candidate is not None and len(part_measures) != len(measures):
            raise ValueError("MusicXML measure count does not match candidate")
        if not part_measures:
            raise ValueError("MusicXML part must contain at least one measure")
        for measure_index, measure_element in enumerate(part_measures):
            if measure_element.get("number") != str(measure_index + 1):
                raise ValueError("MusicXML measure identity is not ordered")
            if (
                candidate is not None
                and measure_element.get("id") != measures[measure_index]["id"]
            ):
                raise ValueError("MusicXML measure identity does not match candidate")
            attributes = _child(measure_element, "attributes")
            divisions = _child(attributes, "divisions") if attributes is not None else None
            if divisions is None or divisions.text != "960":
                raise ValueError("MusicXML divisions must be 960")
            notes = _children(measure_element, "note")
            directions = _children(measure_element, "direction")
            if not notes and not directions:
                raise ValueError("MusicXML measure content is empty")
            duration_total = 0
            for note in notes:
                duration = _child(note, "duration")
                if duration is None or not duration.text or int(duration.text) <= 0:
                    raise ValueError("MusicXML note duration is invalid")
                if _child(note, "chord") is None:
                    duration_total += int(duration.text)
            if candidate is not None and duration_total > measures[measure_index]["durationTicks"]:
                raise ValueError("MusicXML note exceeds measure boundary")

    return {
        "format": "MusicXML 4.0",
        "root": "score-partwise",
        "divisions": 960,
        "partCount": len(parts),
        "measureCount": len(_children(parts[0], "measure")),
    }


def require_accepted_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the common acceptance, schema, rights, and lineage gates."""
    if candidate.get("status") not in {"CANDIDATE", "ACCEPTED"}:
        raise ValueError("MusicXML export requires an accepted candidate")
    summary = candidate.get("validationSummary", {})
    if summary.get("status") != "VALID" or summary.get("errorCount") != 0:
        raise ValueError("MusicXML export requires an accepted candidate")
    try:
        validate_arrangement_document(candidate)
    except ValueError as error:
        raise ValueError(f"candidate schema invalid: {error}") from error
    source_refs = candidate.get("sourceRefs", [])
    if not source_refs or not all(
        reference.get("rightsAttested") is True for reference in source_refs
    ):
        raise ValueError("MusicXML export requires rights-attested source references")
    lineage = candidate.get("extensions", {}).get("bandforge.generation-lineage")
    try:
        return validate_generation_lineage(lineage)
    except ValueError as error:
        raise ValueError(f"MusicXML export requires generation lineage: {error}") from error


def _render_musicxml(document: Mapping[str, Any]) -> bytes:
    root = ET.Element("score-partwise", {"version": "4.0"})
    work = ET.SubElement(root, "work")
    ET.SubElement(work, "work-title").text = document["global"]["title"]
    identification = ET.SubElement(root, "identification")
    encoding = ET.SubElement(identification, "encoding")
    ET.SubElement(encoding, "software").text = "BandForge deterministic rules baseline"

    part_list = ET.SubElement(root, "part-list")
    for index, track in enumerate(document["tracks"], start=1):
        part_id = f"P{index:03d}"
        score_part = ET.SubElement(part_list, "score-part", {"id": part_id})
        ET.SubElement(score_part, "part-name").text = track["name"]

    for index, track in enumerate(document["tracks"], start=1):
        part = ET.SubElement(root, "part", {"id": f"P{index:03d}"})
        for measure in document["measures"]:
            measure_element = ET.SubElement(
                part,
                "measure",
                {"number": str(measure["ordinal"]), "id": measure["id"]},
            )
            _append_attributes(measure_element, document, track)
            if index == 1:
                _append_harmony(measure_element, document, measure)
            events = _events_for_measure(track, measure)
            if events:
                for event in events:
                    _append_event_notes(measure_element, event, measure)
            else:
                _append_rest(measure_element, measure["durationTicks"])
    ET.indent(root, space="  ")
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        root, encoding="utf-8", short_empty_elements=True
    ) + b"\n"


def _append_attributes(
    parent: ET.Element, document: Mapping[str, Any], track: Mapping[str, Any]
) -> None:
    attributes = ET.SubElement(parent, "attributes")
    ET.SubElement(attributes, "divisions").text = "960"
    key = document["global"]["key"]
    key_element = ET.SubElement(attributes, "key")
    ET.SubElement(key_element, "fifths").text = str(
        _key_fifths(key["tonicPitchClass"], key["mode"])
    )
    ET.SubElement(key_element, "mode").text = key["mode"].lower()
    signature = document["global"]["defaultTimeSignature"]
    time = ET.SubElement(attributes, "time")
    ET.SubElement(time, "beats").text = str(signature["numerator"])
    ET.SubElement(time, "beat-type").text = str(signature["denominator"])
    clef = ET.SubElement(attributes, "clef")
    if track["instrument"] == "DRUMS":
        ET.SubElement(clef, "sign").text = "percussion"
    else:
        ET.SubElement(clef, "sign").text = "F" if track["instrument"] == "BASS" else "G"
        ET.SubElement(clef, "line").text = "4" if track["instrument"] == "BASS" else "2"


def _append_harmony(
    parent: ET.Element, document: Mapping[str, Any], measure: Mapping[str, Any]
) -> None:
    measure_start = measure["startTick"]
    measure_end = measure_start + measure["durationTicks"]
    for harmony in document["harmony"]:
        if measure_start <= harmony["startTick"] < measure_end:
            element = ET.SubElement(parent, "harmony")
            root = ET.SubElement(element, "root")
            ET.SubElement(root, "root-step").text = _ROOT_STEPS[harmony["rootPitchClass"]]
            if _ROOT_ALTERS[harmony["rootPitchClass"]]:
                ET.SubElement(root, "root-alter").text = "1"
            kind = ET.SubElement(element, "kind", {"text": harmony["displaySymbol"]})
            kind.text = _KIND_NAMES[harmony["quality"]]


def _append_event_notes(
    parent: ET.Element, event: Mapping[str, Any], measure: Mapping[str, Any]
) -> None:
    duration = str(event["durationTicks"])
    event_type = event["type"]
    if event_type == "NOTE":
        _append_pitch_note(parent, event["writtenPitch"], duration, event)
    elif event_type == "CHORD":
        for pitch_index, pitch in enumerate(event["writtenPitches"]):
            _append_pitch_note(parent, pitch, duration, event, chord=pitch_index > 0)
    elif event_type == "DRUM_HIT":
        note = ET.SubElement(parent, "note")
        unpitched = ET.SubElement(note, "unpitched")
        step, octave = _DRUM_DISPLAY[event["kitPiece"]]
        ET.SubElement(unpitched, "display-step").text = step
        ET.SubElement(unpitched, "display-octave").text = str(octave)
        ET.SubElement(note, "duration").text = duration
        ET.SubElement(note, "voice").text = "1"
        ET.SubElement(note, "type").text = _DURATION_TYPES.get(event["durationTicks"], "quarter")
    elif event_type == "REST":
        _append_rest(parent, event["durationTicks"])
    elif event_type == "DIRECTION":
        direction = ET.SubElement(parent, "direction")
        direction_type = ET.SubElement(direction, "direction-type")
        ET.SubElement(direction_type, "words").text = event["value"]
    else:
        raise ValueError(f"MusicXML does not support event type {event_type}")


def _append_pitch_note(
    parent: ET.Element,
    pitch: int,
    duration: str,
    event: Mapping[str, Any],
    *,
    chord: bool = False,
) -> None:
    note = ET.SubElement(parent, "note")
    if chord:
        ET.SubElement(note, "chord")
    pitch_element = ET.SubElement(note, "pitch")
    step, alter = _PITCH_NAMES[pitch % 12]
    ET.SubElement(pitch_element, "step").text = step
    if alter:
        ET.SubElement(pitch_element, "alter").text = str(alter)
    ET.SubElement(pitch_element, "octave").text = str(pitch // 12 - 1)
    ET.SubElement(note, "duration").text = duration
    ET.SubElement(note, "voice").text = "1"
    ET.SubElement(note, "type").text = _DURATION_TYPES.get(int(duration), "quarter")


def _append_rest(parent: ET.Element, duration: int) -> None:
    note = ET.SubElement(parent, "note")
    ET.SubElement(note, "rest")
    ET.SubElement(note, "duration").text = str(duration)
    ET.SubElement(note, "voice").text = "1"
    ET.SubElement(note, "type").text = _DURATION_TYPES.get(duration, "quarter")


def _events_for_measure(
    track: Mapping[str, Any], measure: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    start = measure["startTick"]
    end = start + measure["durationTicks"]
    return sorted(
        (event for event in track.get("events", []) if start <= event["startTick"] < end),
        key=lambda event: (event["startTick"], event["id"]),
    )


def _require_measure_boundaries(document: Mapping[str, Any]) -> None:
    measures = document["measures"]
    collections = (
        document.get("harmony", []),
        *(track.get("events", []) for track in document["tracks"]),
    )
    for collection in collections:
        for event in collection:
            measure = next(
                (
                    item
                    for item in measures
                    if item["startTick"] <= event["startTick"] < (
                        item["startTick"] + item["durationTicks"]
                    )
                ),
                None,
            )
            if measure is None or event["startTick"] + event["durationTicks"] > (
                measure["startTick"] + measure["durationTicks"]
            ):
                raise ValueError("MusicXML export rejects measure boundary overflow")


def _key_fifths(tonic_pitch_class: int, mode: str) -> int:
    major_fifths = {0: 0, 1: 7, 2: 2, 3: -3, 4: 4, 5: -1, 6: 6, 7: 1, 8: -4, 9: 3, 10: -2, 11: 5}
    if mode == "MINOR":
        return major_fifths[(tonic_pitch_class + 3) % 12]
    return major_fifths.get(tonic_pitch_class, 0)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(parent: ET.Element | None, name: str) -> list[ET.Element]:
    if parent is None:
        return []
    return [child for child in list(parent) if _local_name(child.tag) == name]


def _child(parent: ET.Element | None, name: str) -> ET.Element | None:
    children = _children(parent, name)
    return children[0] if children else None
