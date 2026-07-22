"""Dependency-free Standard MIDI File type-1 artifacts for accepted candidates."""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from bandforge_domain.arrangements import validate_arrangement_document


@dataclass(frozen=True)
class MidiArtifact:
    data: bytes
    manifest: dict[str, Any]


_DRUM_KEYS = {
    "KICK": 36,
    "SNARE": 38,
    "CLOSED_HAT": 42,
    "OPEN_HAT": 46,
    "RIDE": 51,
    "CRASH": 49,
    "LOW_TOM": 45,
    "MID_TOM": 47,
    "HIGH_TOM": 50,
    "PERCUSSION": 39,
}


def export_candidate_midi(candidate: Mapping[str, Any]) -> MidiArtifact:
    """Render an accepted canonical candidate into a deterministic type-1 MIDI file."""
    _require_accepted_candidate(candidate)
    data = _render_type1(candidate)
    source_refs = list(candidate["sourceRefs"])
    manifest = {
        "artifactType": "STANDARD_MIDI_FILE",
        "format": 1,
        "ticksPerQuarter": candidate["global"]["ticksPerQuarter"],
        "trackCount": len(candidate["tracks"]) + 1,
        "parentVersionId": candidate["versionId"],
        "sourceRevisionIds": [reference["sourceRevisionId"] for reference in source_refs],
        "rightsAttested": all(reference["rightsAttested"] is True for reference in source_refs),
        "provenance": candidate.get("extensions", {}).get(
            "bandforge.generation-lineage", candidate["provenance"]
        ),
        "contentHash": "sha256:" + hashlib.sha256(data).hexdigest(),
    }
    return MidiArtifact(data=data, manifest=manifest)


def validate_midi_type1(data: bytes) -> dict[str, int]:
    """Validate the structural header, chunks, and events of a type-1 MIDI file."""
    if len(data) < 14 or data[:4] != b"MThd":
        raise ValueError("MIDI header is missing or truncated")
    header_length = struct.unpack_from(">I", data, 4)[0]
    if header_length != 6 or len(data) < 14 + header_length:
        raise ValueError("MIDI header length is invalid")
    format_type, track_count, division = struct.unpack_from(">HHH", data, 8)
    if format_type != 1:
        raise ValueError("MIDI format must be type 1")
    if track_count < 2:
        raise ValueError("type-1 MIDI requires a conductor and musical track")
    if division & 0x8000 or division == 0:
        raise ValueError("MIDI division must be positive ticks-per-quarter")

    offset = 14
    for _ in range(track_count):
        if offset + 8 > len(data) or data[offset : offset + 4] != b"MTrk":
            raise ValueError("MIDI track chunk is missing or truncated")
        length = struct.unpack_from(">I", data, offset + 4)[0]
        start = offset + 8
        end = start + length
        if end > len(data):
            raise ValueError("MIDI track chunk is truncated")
        _validate_track_events(data[start:end])
        offset = end
    if offset != len(data):
        raise ValueError("MIDI contains trailing bytes")
    return {"format": format_type, "trackCount": track_count, "ticksPerQuarter": division}


def _require_accepted_candidate(candidate: Mapping[str, Any]) -> None:
    if candidate.get("status") not in {"CANDIDATE", "ACCEPTED"}:
        raise ValueError("MIDI export requires an accepted candidate")
    summary = candidate.get("validationSummary", {})
    if summary.get("status") != "VALID" or summary.get("errorCount") != 0:
        raise ValueError("MIDI export requires an accepted candidate")
    try:
        validate_arrangement_document(candidate)
    except ValueError as error:
        raise ValueError(f"candidate schema invalid: {error}") from error
    if not all(reference.get("rightsAttested") is True for reference in candidate["sourceRefs"]):
        raise ValueError("MIDI export requires rights-attested source references")


def _render_type1(document: Mapping[str, Any]) -> bytes:
    tracks = [
        _render_conductor_track(document),
        *(
            _render_musical_track(track, index)
            for index, track in enumerate(document["tracks"])
        ),
    ]
    header = b"MThd" + struct.pack(
        ">IHHH", 6, 1, len(tracks), document["global"]["ticksPerQuarter"]
    )
    return header + b"".join(_track_chunk(track) for track in tracks)


def _render_conductor_track(document: Mapping[str, Any]) -> bytes:
    events: list[tuple[int, int, int, bytes]] = []
    tempo = document["global"]["tempoMap"][0]["bpm"]
    micros_per_quarter = round(60_000_000 / tempo)
    events.append((0, 0, 0, b"\xff\x51\x03" + micros_per_quarter.to_bytes(3, "big")))
    signature = document["global"]["defaultTimeSignature"]
    events.append((0, 1, 0, bytes([0xFF, 0x58, 4, signature["numerator"], 2, 24, 8])))
    events.append((0, 2, 0, _meta_text(0x03, document["global"]["title"])))
    for index, harmony in enumerate(document["harmony"]):
        events.append(
            (
                harmony["startTick"],
                3,
                index,
                _meta_text(0x01, f"CHORD {harmony['displaySymbol']}"),
            )
        )
    return _encode_events(events)


def _render_musical_track(track: Mapping[str, Any], index: int) -> bytes:
    channel = 9 if track["instrument"] == "DRUMS" else index % 9
    events: list[tuple[int, int, int, bytes]] = []
    if track.get("midiProgram") is not None:
        events.append((0, 0, 0, bytes([0xC0 | channel, track["midiProgram"]])))
    order = 1
    for event in track["events"]:
        pitches = _midi_pitches(event)
        if not pitches:
            continue
        if event["type"] == "DRUM_HIT":
            pitches = [_DRUM_KEYS[event["kitPiece"]]]
        velocity = event.get("velocity", 80)
        for pitch in pitches:
            events.append(
                (
                    event["startTick"] + event["durationTicks"],
                    1,
                    order,
                    bytes([0x80 | channel, pitch, 0]),
                )
            )
            order += 1
            events.append((event["startTick"], 2, order, bytes([0x90 | channel, pitch, velocity])))
            order += 1
    return _encode_events(events)


def _midi_pitches(event: Mapping[str, Any]) -> list[int]:
    if event["type"] == "NOTE":
        return [event["soundingPitch"]]
    if event["type"] == "CHORD":
        return list(event["soundingPitches"])
    if event["type"] == "DRUM_HIT":
        return [_DRUM_KEYS[event["kitPiece"]]]
    return []


def _meta_text(kind: int, value: str) -> bytes:
    encoded = value.encode("utf-8")
    return bytes([0xFF, kind]) + _vlq(len(encoded)) + encoded


def _track_chunk(payload: bytes) -> bytes:
    return b"MTrk" + struct.pack(">I", len(payload)) + payload


def _encode_events(events: list[tuple[int, int, int, bytes]]) -> bytes:
    events.sort(key=lambda item: (item[0], item[1], item[2]))
    output = bytearray()
    previous_tick = 0
    for tick, _priority, _order, payload in events:
        output.extend(_vlq(tick - previous_tick))
        output.extend(payload)
        previous_tick = tick
    output.extend(b"\x00\xff\x2f\x00")
    return bytes(output)


def _vlq(value: int) -> bytes:
    if value < 0:
        raise ValueError("MIDI delta time cannot be negative")
    buffer = [value & 0x7F]
    value >>= 7
    while value:
        buffer.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(buffer))


def _read_vlq(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for _ in range(4):
        if offset >= len(data):
            raise ValueError("MIDI event length is truncated")
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, offset
    raise ValueError("MIDI variable-length value is too long")


def _validate_track_events(data: bytes) -> None:
    offset = 0
    running_status: int | None = None
    saw_end = False
    while offset < len(data):
        _delta, offset = _read_vlq(data, offset)
        if offset >= len(data):
            raise ValueError("MIDI event status is truncated")
        status = data[offset]
        if status < 0x80:
            if running_status is None:
                raise ValueError("MIDI event has no running status")
            status = running_status
        else:
            offset += 1
            if status < 0xF0:
                running_status = status
        if status == 0xFF:
            if offset >= len(data):
                raise ValueError("MIDI meta-event is truncated")
            meta_type = data[offset]
            offset += 1
            length, offset = _read_vlq(data, offset)
            if offset + length > len(data):
                raise ValueError("MIDI meta-event payload is truncated")
            offset += length
            if meta_type == 0x2F:
                if length != 0:
                    raise ValueError("MIDI end-of-track event is invalid")
                saw_end = True
                if offset != len(data):
                    raise ValueError("MIDI has events after end-of-track")
                break
        elif status in {0xF0, 0xF7}:
            length, offset = _read_vlq(data, offset)
            if offset + length > len(data):
                raise ValueError("MIDI sysex payload is truncated")
            offset += length
        elif 0x80 <= status <= 0xEF:
            data_length = 1 if status & 0xE0 == 0xC0 else 2
            if offset + data_length > len(data):
                raise ValueError("MIDI channel event is truncated")
            offset += data_length
        else:
            raise ValueError("MIDI system event is unsupported")
    if not saw_end:
        raise ValueError("MIDI track has no end-of-track event")
