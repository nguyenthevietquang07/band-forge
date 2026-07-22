"""Construction and schema validation of canonical ArrangementDocument snapshots."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from bandforge_domain.chart import NormalizedChart


class SourceNotReadyError(ValueError):
    """Raised when a source revision cannot safely become an arrangement seed."""


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts" / "arrangement-document.schema.json"


def _key_components(key: str) -> tuple[int, str, str]:
    root, separator, mode = key.rpartition("_")
    pitch_classes = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    if not separator or root not in pitch_classes or mode not in {"MAJOR", "MINOR"}:
        raise ValueError("key must use a supported form such as A_MINOR or G_MAJOR")
    return pitch_classes[root], mode, f"{root} {mode.lower()}"


def _stable_id(prefix: str, ordinal: int | None = None) -> str:
    suffix = "seed" if ordinal is None else f"{ordinal:03d}"
    return f"{prefix}_{suffix}"


def _source_guide_track(section_id: str) -> dict[str, Any]:
    return {
        "id": "track_source_guide",
        "name": "Source Guide",
        "instrument": "KEYS",
        "playerLevel": "BEGINNER",
        "writtenRange": {"minimum": 36, "maximum": 96},
        "soundingRange": {"minimum": 36, "maximum": 96},
        "transpositionSemitones": 0,
        "maxPolyphony": 1,
        "midiProgram": None,
        "roles": [{"sectionInstanceId": section_id, "role": "REST"}],
        "events": [],
    }


def build_arrangement_seed(
    chart: NormalizedChart,
    source_revision_id: str,
    source_hash: str,
    now: datetime,
    arrangement_id: str = "arrangement_seed",
    version_id: str = "version_seed_001",
) -> dict[str, Any]:
    """Build an immutable, source-locked draft from an approved normalized chart."""
    if chart.findings or any(event is None for event in chart.harmony):
        raise SourceNotReadyError("Resolve every source finding before approval.")

    tonic, mode, key_display = _key_components(chart.source.key)
    measures = [
        {
            "id": _stable_id("measure", measure.ordinal),
            "ordinal": measure.ordinal,
            "startTick": measure.start_tick,
            "durationTicks": measure.duration_ticks,
            "timeSignature": {"numerator": 4, "denominator": 4},
            "rehearsalMark": "A" if measure.ordinal == 1 else None,
            "isPickup": False,
        }
        for measure in chart.measures
    ]
    section_id = "section_source_001"
    harmony = [
        {
            "id": _stable_id("harmony", event.ordinal),
            "startTick": event.start_tick,
            "durationTicks": event.duration_ticks,
            "rootPitchClass": event.root_pitch_class,
            "bassPitchClass": event.bass_pitch_class,
            "quality": event.quality,
            "extensions": event.extensions,
            "displaySymbol": event.display_symbol,
            "romanNumeral": None,
            "isLocked": True,
            "provenance": "USER",
            "sourceHarmonyEventId": None,
        }
        for event in chart.harmony
        if event is not None
    ]
    created_at = now.isoformat().replace("+00:00", "Z")
    document: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "arrangementId": arrangement_id,
        "versionId": version_id,
        "parentVersionId": None,
        "status": "DRAFT",
        "global": {
            "title": chart.source.title,
            "composer": None,
            "ticksPerQuarter": 960,
            "key": {"tonicPitchClass": tonic, "mode": mode, "display": key_display},
            "tempoMap": [{"startTick": 0, "bpm": 100}],
            "defaultTimeSignature": {"numerator": 4, "denominator": 4},
        },
        "sourceRefs": [
            {
                "sourceRevisionId": source_revision_id,
                "contentHash": source_hash,
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
            }
        ],
        "measures": measures,
        "sectionInstances": [
            {
                "id": section_id,
                "type": "OTHER",
                "label": "Source Chart",
                "startMeasureId": measures[0]["id"],
                "endMeasureId": measures[-1]["id"],
                "energy": 1,
                "density": 1,
            }
        ],
        "harmony": harmony,
        "tracks": [_source_guide_track(section_id)],
        "controls": {
            "stylePackId": "acoustic-pop@1.0.0",
            "feel": "STRAIGHT",
            "swingRatio": None,
            "density": 1,
            "harmonicAdventurousness": 0,
            "variationMode": "SAFE",
        },
        "locks": [{"id": "lock_source_harmony", "type": "HARMONY"}],
        "provenance": {
            "createdBy": "IMPORTER",
            "createdAt": created_at,
            "engineVersion": "source-workflow-0.1.0",
            "validatorVersion": "schema-1.0.0",
            "seed": None,
            "modelId": None,
            "promptVersion": None,
            "retrievalItemIds": [],
            "fallbackUsed": False,
        },
        "validationSummary": {
            "runId": "validation_seed_001",
            "status": "VALID",
            "errorCount": 0,
            "warningCount": 0,
        },
        "extensions": {},
    }
    validate_arrangement_document(document)
    return document


def validate_arrangement_document(document: Mapping[str, Any]) -> None:
    """Raise the first actionable JSON Schema violation for a canonical document."""
    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "document"
        raise ValueError(f"ArrangementDocument schema violation at {location}: {first.message}")
