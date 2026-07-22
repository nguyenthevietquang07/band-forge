"""Parsing for the deliberately small structured-source chord vocabulary."""

from __future__ import annotations

import re
from dataclasses import dataclass

ROOT_PITCH_CLASSES = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}

_CHORD_PATTERN = re.compile(
    r"^(?P<root>[A-G](?:#|b)?)(?P<quality>m|sus2|sus4|5)?(?P<extension>6|maj7|7|9|add9)?(?:/(?P<bass>[A-G](?:#|b)?))?$"
)


@dataclass(frozen=True)
class ParseFinding:
    code: str
    message: str
    bar_ordinal: int | None = None


@dataclass(frozen=True)
class ParsedChord:
    display_symbol: str
    root_pitch_class: int
    quality: str
    extensions: list[str]
    bass_pitch_class: int | None


def _pitch_class(symbol: str) -> int:
    return ROOT_PITCH_CLASSES[symbol.upper()]


def parse_chord(symbol: str) -> ParsedChord | ParseFinding:
    """Parse one supported display symbol without silently changing its meaning."""
    normalized = symbol.strip()
    match = _CHORD_PATTERN.fullmatch(normalized)
    if match is None:
        return ParseFinding(
            code="UNSUPPORTED_CHORD_SYMBOL",
            message=f"Chord symbol '{symbol}' is not supported by this source editor.",
        )

    quality_token = match.group("quality")
    quality = {
        None: "MAJOR",
        "m": "MINOR",
        "sus2": "SUS2",
        "sus4": "SUS4",
        "5": "POWER",
    }[quality_token]
    extension_token = match.group("extension")
    extension = {"maj7": "MAJ7", "add9": "ADD9"}.get(extension_token, extension_token)
    bass = match.group("bass")

    return ParsedChord(
        display_symbol=normalized,
        root_pitch_class=_pitch_class(match.group("root")),
        quality=quality,
        extensions=[] if extension is None else [extension],
        bass_pitch_class=None if bass is None else _pitch_class(bass),
    )
