"""Deterministic, validator-gated four-piece candidate generation."""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any, Literal

from bandforge_domain.arrangements import validate_arrangement_document

ENGINE_VERSION = "rules-baseline-0.1.0"
STYLE_PACK_VERSION = "acoustic-pop@1.0.0"
VALIDATOR_VERSION = "rules-0.1.0"

Instrument = Literal["DRUMS", "BASS", "GUITAR", "KEYS"]
Difficulty = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]


@dataclass(frozen=True)
class ArrangementControls:
    style: str = "acoustic-pop"
    tempo_bpm: int = 100
    difficulty: Difficulty = "BEGINNER"
    seed: int = 0

    def __post_init__(self) -> None:
        if self.style != "acoustic-pop":
            raise ValueError("The baseline supports only the acoustic-pop style.")
        if not 40 <= self.tempo_bpm <= 240:
            raise ValueError("tempo_bpm must be between 40 and 240.")
        if self.difficulty not in {"BEGINNER", "INTERMEDIATE", "ADVANCED"}:
            raise ValueError("difficulty must be BEGINNER, INTERMEDIATE, or ADVANCED.")
        if self.difficulty != "BEGINNER":
            raise ValueError("Only BEGINNER difficulty is supported by the baseline.")
        if self.seed < 0:
            raise ValueError("seed must be non-negative.")


@dataclass(frozen=True)
class GenerationLineage:
    seed: int
    engine_version: str
    style_pack_version: str
    validator_version: str
    input_revision: str
    input_revision_set: tuple[str, ...]
    provenance: str


@dataclass(frozen=True)
class ValidationFinding:
    rule_id: str
    category: str
    message: str
    track_id: str | None = None
    measure_id: str | None = None

    @property
    def severity(self) -> str:
        return "ERROR"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ruleId": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "trackId": self.track_id,
            "measureId": self.measure_id,
        }


@dataclass(frozen=True)
class CandidateResult:
    document: dict[str, Any]
    lineage: GenerationLineage
    findings: tuple[ValidationFinding, ...]
    accepted: bool


@dataclass(frozen=True)
class CandidateSummary:
    """Stable, non-musical comparison data for one generated candidate."""

    candidate_id: str
    seed: int
    accepted: bool
    input_revision_set: tuple[str, ...]
    engine_version: str
    style_pack_version: str
    validator_version: str
    provenance: str
    findings: tuple[ValidationFinding, ...]
    source_harmony_unchanged: bool

    @property
    def hard_finding_count(self) -> int:
        return len(self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidateId": self.candidate_id,
            "seed": self.seed,
            "accepted": self.accepted,
            "hardFindingCount": self.hard_finding_count,
            "sourceHarmonyUnchanged": self.source_harmony_unchanged,
            "lineage": {
                "seed": self.seed,
                "engineVersion": self.engine_version,
                "stylePackVersion": self.style_pack_version,
                "validatorVersion": self.validator_version,
                "inputRevisionSet": list(self.input_revision_set),
                "provenance": self.provenance,
            },
            "findings": [finding.to_dict() for finding in self.findings],
        }


def compare_candidates(
    source: Mapping[str, Any],
    seeds: Iterable[int],
    controls: ArrangementControls | None = None,
) -> tuple[CandidateSummary, ...]:
    """Generate and summarize at most eight reproducible BEGINNER candidates."""
    seed_values = tuple(seeds)
    if not 1 <= len(seed_values) <= 8:
        raise ValueError("candidate comparison requires between 1 and 8 seeds")
    if len(set(seed_values)) != len(seed_values):
        raise ValueError("candidate comparison seeds must be distinct")

    base_controls = controls or ArrangementControls()
    summaries: list[CandidateSummary] = []
    for seed in sorted(seed_values):
        result = generate_candidate(source, replace(base_controls, seed=seed))
        summaries.append(
            CandidateSummary(
                candidate_id=result.document["versionId"],
                seed=seed,
                accepted=result.accepted,
                input_revision_set=result.lineage.input_revision_set,
                engine_version=result.lineage.engine_version,
                style_pack_version=result.lineage.style_pack_version,
                validator_version=result.lineage.validator_version,
                provenance=result.lineage.provenance,
                findings=result.findings,
                source_harmony_unchanged=result.document.get("harmony") == source.get("harmony"),
            )
        )
    return tuple(summaries)


_VALIDATOR_RULES: tuple[dict[str, str], ...] = (
    {
        "ruleId": "BF-LOCK-001",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "description": "Candidate harmony must equal the locked source harmony.",
    },
    {
        "ruleId": "BF-LOCK-002",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "description": "Only DRAFT or ACCEPTED source documents can generate candidates.",
    },
    {
        "ruleId": "BF-LOCK-003",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "description": "The source document must declare a HARMONY lock.",
    },
    {
        "ruleId": "BF-LOCK-004",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "description": "Every source harmony event must remain locked.",
    },
    {
        "ruleId": "BF-RIGHTS-001",
        "category": "RIGHTS",
        "severity": "ERROR",
        "description": "Every source reference must carry a rights attestation.",
    },
    {
        "ruleId": "BF-SCHEMA-001",
        "category": "SCHEMA",
        "severity": "ERROR",
        "description": "Source and candidate documents must satisfy the canonical schema.",
    },
    {
        "ruleId": "BF-STRUCT-001",
        "category": "BAR_ALIGNMENT",
        "severity": "ERROR",
        "description": "Events must fit inside their canonical measure boundaries.",
    },
    {
        "ruleId": "BF-TIMING-001",
        "category": "TIMING",
        "severity": "ERROR",
        "description": "Event durations must be positive.",
    },
    {
        "ruleId": "BF-RANGE-001",
        "category": "RANGE",
        "severity": "ERROR",
        "description": "Sounding pitches must fit the track sounding range.",
    },
    {
        "ruleId": "BF-RANGE-002",
        "category": "RANGE",
        "severity": "ERROR",
        "description": "Written pitches must fit the track written range.",
    },
    {
        "ruleId": "BF-POLY-001",
        "category": "POLYPHONY",
        "severity": "ERROR",
        "description": "Event voice count must fit the track polyphony limit.",
    },
)


def build_validator_catalog(source: Mapping[str, Any]) -> dict[str, Any]:
    """Return machine-readable hard-rule definitions and failure evidence."""
    baseline = generate_candidate(source, ArrangementControls(seed=0))
    baseline_document = baseline.document

    def evidence(
        rule_id: str, findings: tuple[ValidationFinding, ...], accepted: bool
    ) -> dict[str, Any]:
        finding = next(item for item in findings if item.rule_id == rule_id)
        return {"accepted": accepted, **finding.to_dict()}

    failures: list[dict[str, Any]] = []

    changed_harmony = deepcopy(baseline_document)
    changed_harmony["harmony"][0]["displaySymbol"] = "INVALID_SOURCE_LOCK"
    failures.append(evidence("BF-LOCK-001", validate_candidate(changed_harmony, source), False))

    unusable_source = deepcopy(source)
    unusable_source["status"] = "ARCHIVED"
    unusable_result = generate_candidate(unusable_source, ArrangementControls(seed=0))
    failures.append(evidence("BF-LOCK-002", unusable_result.findings, unusable_result.accepted))

    missing_lock = deepcopy(source)
    missing_lock["locks"] = []
    missing_lock_result = generate_candidate(missing_lock, ArrangementControls(seed=0))
    failures.append(
        evidence("BF-LOCK-003", missing_lock_result.findings, missing_lock_result.accepted)
    )

    unlocked_source = deepcopy(source)
    unlocked_source["harmony"][0]["isLocked"] = False
    unlocked_result = generate_candidate(unlocked_source, ArrangementControls(seed=0))
    failures.append(evidence("BF-LOCK-004", unlocked_result.findings, unlocked_result.accepted))

    unattested_source = deepcopy(source)
    unattested_source["sourceRefs"][0]["rightsAttested"] = False
    unattested_result = generate_candidate(unattested_source, ArrangementControls(seed=0))
    failures.append(
        evidence("BF-RIGHTS-001", unattested_result.findings, unattested_result.accepted)
    )

    schema_invalid_source = deepcopy(source)
    del schema_invalid_source["tracks"]
    schema_invalid_result = generate_candidate(schema_invalid_source, ArrangementControls(seed=0))
    failures.append(
        evidence("BF-SCHEMA-001", schema_invalid_result.findings, schema_invalid_result.accepted)
    )

    structurally_invalid = deepcopy(baseline_document)
    structurally_invalid["tracks"][1]["events"][0]["startTick"] = 999999
    failures.append(
        evidence("BF-STRUCT-001", validate_candidate(structurally_invalid, source), False)
    )

    invalid_timing = deepcopy(baseline_document)
    invalid_timing["tracks"][1]["events"][0]["durationTicks"] = 0
    failures.append(evidence("BF-TIMING-001", validate_candidate(invalid_timing, source), False))

    invalid_sounding_range = deepcopy(baseline_document)
    invalid_sounding_range["tracks"][3]["events"][0]["soundingPitches"][0] = 100
    failures.append(
        evidence("BF-RANGE-001", validate_candidate(invalid_sounding_range, source), False)
    )

    invalid_written_range = deepcopy(baseline_document)
    invalid_written_range["tracks"][3]["events"][0]["writtenPitches"][0] = 100
    failures.append(
        evidence("BF-RANGE-002", validate_candidate(invalid_written_range, source), False)
    )

    invalid_polyphony = deepcopy(baseline_document)
    invalid_polyphony["tracks"][3]["events"][0]["soundingPitches"] = [60, 62, 64, 65, 67]
    failures.append(evidence("BF-POLY-001", validate_candidate(invalid_polyphony, source), False))

    return {
        "validatorVersion": VALIDATOR_VERSION,
        "scope": "hard deterministic structural validators",
        "rules": [dict(rule) for rule in _VALIDATOR_RULES],
        "representativeFailures": failures,
    }


def generate_candidate(
    source: Mapping[str, Any],
    controls: ArrangementControls,
) -> CandidateResult:
    """Generate one deterministic candidate without modifying source harmony."""
    source_document, input_revision = _source_document(source)
    input_revision_set = _source_revision_set(source_document)
    source_schema_error: ValueError | None = None
    try:
        validate_arrangement_document(source_document)
    except ValueError as error:
        source_schema_error = error
    candidate = deepcopy(source_document)
    lineage = GenerationLineage(
        seed=controls.seed,
        engine_version=ENGINE_VERSION,
        style_pack_version=STYLE_PACK_VERSION,
        validator_version=VALIDATOR_VERSION,
        input_revision=input_revision,
        input_revision_set=input_revision_set,
        provenance="approved-source-locked-rules-baseline",
    )
    findings = list(_source_lock_findings(source_document, candidate))
    if source_schema_error is not None and not any(
        finding.rule_id == "BF-RIGHTS-001" for finding in findings
    ):
        findings.append(ValidationFinding("BF-SCHEMA-001", "SCHEMA", str(source_schema_error)))
    if not findings and source_schema_error is None:
        candidate = _add_generated_tracks(candidate, controls)
        candidate["status"] = "CANDIDATE"
        candidate["parentVersionId"] = source_document["versionId"]
        candidate["versionId"] = _candidate_version_id(
            source_document, controls, input_revision_set
        )
        candidate["global"]["tempoMap"] = [{"startTick": 0, "bpm": controls.tempo_bpm}]

    candidate["provenance"] = {
        **candidate["provenance"],
        "createdBy": "GENERATOR",
        "engineVersion": lineage.engine_version,
        "validatorVersion": lineage.validator_version,
        "seed": lineage.seed,
        "modelId": None,
        "promptVersion": None,
        "fallbackUsed": False,
    }
    if isinstance(candidate.get("extensions"), dict):
        candidate["extensions"]["bandforge.generation-lineage"] = {
            "seed": lineage.seed,
            "engineVersion": lineage.engine_version,
            "stylePackVersion": lineage.style_pack_version,
            "validatorVersion": lineage.validator_version,
            "inputRevisionSet": list(lineage.input_revision_set),
            "provenance": lineage.provenance,
        }
    findings.extend(validate_candidate(candidate, source_document))
    try:
        validate_arrangement_document(candidate)
    except ValueError as error:
        findings.append(ValidationFinding("BF-SCHEMA-001", "SCHEMA", str(error)))
    candidate["validationSummary"] = {
        **candidate["validationSummary"],
        "status": "VALID" if not findings else "INVALID",
        "errorCount": len(findings),
        "warningCount": 0,
    }
    if findings:
        candidate["status"] = "CANDIDATE"
    return CandidateResult(candidate, lineage, tuple(findings), not findings)


def validate_candidate(
    candidate: Mapping[str, Any], source: Mapping[str, Any]
) -> tuple[ValidationFinding, ...]:
    """Return hard findings for source-lock, timing, range, and polyphony rules."""
    findings: list[ValidationFinding] = []
    source_harmony = source.get("harmony", [])
    if candidate.get("harmony") != source_harmony:
        findings.append(
            ValidationFinding(
                "BF-LOCK-001", "SOURCE_LOCK", "Candidate changed locked source harmony."
            )
        )

    measures = candidate.get("measures", [])
    for track in candidate.get("tracks", []):
        for event in track.get("events", []):
            measure = _measure_for_event(event, measures)
            duration = event.get("durationTicks")
            if isinstance(duration, (int, float)) and duration <= 0:
                findings.append(
                    ValidationFinding(
                        "BF-TIMING-001",
                        "TIMING",
                        "Event duration must be positive.",
                        track["id"],
                        None if measure is None else measure["id"],
                    )
                )
            if measure is None or event["startTick"] + event["durationTicks"] > (
                measure["startTick"] + measure["durationTicks"]
            ):
                findings.append(
                    ValidationFinding(
                        "BF-STRUCT-001",
                        "BAR_ALIGNMENT",
                        "Event exceeds the canonical measure boundary.",
                        track["id"],
                        None if measure is None else measure["id"],
                    )
                )
            pitches = _event_pitches(event)
            low = track["soundingRange"]["minimum"]
            high = track["soundingRange"]["maximum"]
            if any(pitch < low or pitch > high for pitch in pitches):
                findings.append(
                    ValidationFinding(
                        "BF-RANGE-001",
                        "RANGE",
                        "Event pitch is outside the track sounding range.",
                        track["id"],
                        None if measure is None else measure["id"],
                    )
                )
            written_pitches = _written_event_pitches(event)
            written_low = track["writtenRange"]["minimum"]
            written_high = track["writtenRange"]["maximum"]
            if any(pitch < written_low or pitch > written_high for pitch in written_pitches):
                findings.append(
                    ValidationFinding(
                        "BF-RANGE-002",
                        "RANGE",
                        "Event pitch is outside the track written range.",
                        track["id"],
                        None if measure is None else measure["id"],
                    )
                )
            if len(pitches) > track["maxPolyphony"]:
                findings.append(
                    ValidationFinding(
                        "BF-POLY-001",
                        "POLYPHONY",
                        "Event voice count exceeds the track polyphony limit.",
                        track["id"],
                        None if measure is None else measure["id"],
                    )
                )
    return tuple(findings)


def _source_document(source: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    source_refs = source.get("sourceRefs", [])
    if not source_refs:
        raise ValueError("source document must include sourceRefs")
    return deepcopy(source), source_refs[0]["sourceRevisionId"]


def _source_revision_set(document: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(reference["sourceRevisionId"] for reference in document["sourceRefs"])


def _candidate_version_id(
    source: Mapping[str, Any],
    controls: ArrangementControls,
    input_revision_set: tuple[str, ...],
) -> str:
    identity = {
        "arrangementId": source["arrangementId"],
        "inputRevisionSet": input_revision_set,
        "style": controls.style,
        "tempoBpm": controls.tempo_bpm,
        "difficulty": controls.difficulty,
        "seed": controls.seed,
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"candidate_{digest}"


def _source_lock_findings(
    source: Mapping[str, Any], candidate: Mapping[str, Any]
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    if source.get("status") not in {"DRAFT", "ACCEPTED"}:
        findings.append(
            ValidationFinding("BF-LOCK-002", "SOURCE_LOCK", "Source document is not usable.")
        )
    if not any(lock.get("type") == "HARMONY" for lock in source.get("locks", [])):
        findings.append(
            ValidationFinding("BF-LOCK-003", "SOURCE_LOCK", "Source harmony lock is missing.")
        )
    if not all(event.get("isLocked") is True for event in source.get("harmony", [])):
        findings.append(
            ValidationFinding("BF-LOCK-004", "SOURCE_LOCK", "Source harmony is not fully locked.")
        )
    if not source.get("sourceRefs") or not all(
        reference.get("rightsAttested") is True for reference in source["sourceRefs"]
    ):
        findings.append(
            ValidationFinding(
                "BF-RIGHTS-001",
                "RIGHTS",
                "Every source reference must carry a rights attestation.",
            )
        )
    if candidate.get("harmony") != source.get("harmony"):
        findings.append(
            ValidationFinding(
                "BF-LOCK-001", "SOURCE_LOCK", "Candidate changed locked source harmony."
            )
        )
    return tuple(findings)


def _add_generated_tracks(
    document: dict[str, Any], controls: ArrangementControls
) -> dict[str, Any]:
    rng = random.Random(controls.seed)
    section_id = document["sectionInstances"][0]["id"]
    tracks = [
        _track("generated_drums", "Drums", "DRUMS", "PULSE", {"minimum": 0, "maximum": 127}, 1),
        _track("generated_bass", "Bass", "BASS", "FOUNDATION", {"minimum": 28, "maximum": 60}, 1),
        _track("generated_guitar", "Guitar", "GUITAR", "COMP", {"minimum": 48, "maximum": 84}, 4),
        _track("generated_keys", "Keys", "KEYS", "PAD", {"minimum": 48, "maximum": 96}, 4),
    ]
    for track in tracks:
        track["roles"][0]["sectionInstanceId"] = section_id
    measures = document["measures"]
    for measure, harmony in zip(measures, document["harmony"], strict=False):
        root = harmony["rootPitchClass"]
        duration = measure["durationTicks"]
        start = measure["startTick"]
        bass_pitch = 36 + root + (12 if rng.randrange(2) else 0)
        guitar_pitches = [60 + root, 64 + root, 67 + root]
        keys_pitches = [72 + root, 76 + root, 79 + root]
        tracks[0]["events"].extend(_drum_bar(start, duration, measure["ordinal"]))
        tracks[1]["events"].append(
            _note_event("bass", measure["ordinal"], start, duration, bass_pitch)
        )
        tracks[2]["events"].append(
            _chord_event("guitar", measure["ordinal"], start, duration, guitar_pitches)
        )
        tracks[3]["events"].append(
            _chord_event("keys", measure["ordinal"], start, duration, keys_pitches)
        )
    document["tracks"].extend(tracks)
    return document


def _track(
    track_id: str,
    name: str,
    instrument: Instrument,
    role: str,
    pitch_range: dict[str, int],
    max_polyphony: int,
) -> dict[str, Any]:
    return {
        "id": track_id,
        "name": name,
        "instrument": instrument,
        "playerLevel": "BEGINNER",
        "writtenRange": pitch_range.copy(),
        "soundingRange": pitch_range.copy(),
        "transpositionSemitones": 0,
        "maxPolyphony": max_polyphony,
        "midiProgram": None,
        "roles": [{"sectionInstanceId": "section_placeholder", "role": role}],
        "events": [],
    }


def _drum_bar(start: int, duration: int, ordinal: int) -> list[dict[str, Any]]:
    step = duration // 8
    groove = [
        ("KICK", 100),
        ("CLOSED_HAT", 70),
        ("SNARE", 94),
        ("CLOSED_HAT", 68),
        ("KICK", 92),
        ("CLOSED_HAT", 72),
        ("SNARE", 96),
        ("OPEN_HAT" if ordinal % 4 == 3 else "CLOSED_HAT", 76),
    ]
    if ordinal % 4 == 0:
        groove[-4:] = [
            ("LOW_TOM", 82),
            ("MID_TOM", 86),
            ("HIGH_TOM", 90),
            ("CRASH", 100),
        ]
    if ordinal % 4 == 1:
        groove.insert(0, ("CRASH", 104))
    return [
        {
            "id": f"event_drums_{ordinal:03d}_{index:02d}",
            "type": "DRUM_HIT",
            "startTick": start + step * max(0, index - (1 if ordinal % 4 == 1 else 0)),
            "durationTicks": 1,
            "kitPiece": piece,
            "velocity": velocity,
        }
        for index, (piece, velocity) in enumerate(groove)
    ]


def _note_event(role: str, ordinal: int, start: int, duration: int, pitch: int) -> dict[str, Any]:
    return {
        "id": f"event_{role}_{ordinal:03d}",
        "type": "NOTE",
        "startTick": start,
        "durationTicks": duration,
        "writtenPitch": pitch,
        "soundingPitch": pitch,
        "velocity": 80,
    }


def _chord_event(
    role: str, ordinal: int, start: int, duration: int, pitches: list[int]
) -> dict[str, Any]:
    return {
        "id": f"event_{role}_{ordinal:03d}",
        "type": "CHORD",
        "startTick": start,
        "durationTicks": duration,
        "writtenPitches": pitches,
        "soundingPitches": pitches.copy(),
        "velocity": 72,
        "shapeId": None,
    }


def _measure_for_event(
    event: Mapping[str, Any], measures: list[Mapping[str, Any]]
) -> Mapping[str, Any] | None:
    for measure in measures:
        if measure["startTick"] <= event["startTick"] < (
            measure["startTick"] + measure["durationTicks"]
        ):
            return measure
    return None


def _event_pitches(event: Mapping[str, Any]) -> list[int]:
    if event["type"] == "NOTE":
        return [event["soundingPitch"]]
    if event["type"] == "CHORD":
        return list(event["soundingPitches"])
    return []


def _written_event_pitches(event: Mapping[str, Any]) -> list[int]:
    if event["type"] == "NOTE":
        return [event["writtenPitch"]]
    if event["type"] == "CHORD":
        return list(event["writtenPitches"])
    return []
