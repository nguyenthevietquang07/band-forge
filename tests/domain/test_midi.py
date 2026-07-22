from copy import deepcopy
from datetime import UTC, datetime

import pytest

from bandforge_domain.arrangements import build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate
from bandforge_domain.midi import export_candidate_midi, validate_midi_type1


def _candidate_document():
    chart = normalize_chart(
        StructuredChartInput(title="MIDI Fixture", key="A_MINOR", bars=["Am", "F", "C", "G"])
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_midi_001",
        "sha256:" + "e" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_midi_001",
        version_id="version_midi_001",
    )
    result = generate_candidate(source, ArrangementControls(seed=17, tempo_bpm=108))
    assert result.accepted
    return result.document


def test_midi_export_is_deterministic_and_type1_valid():
    candidate = _candidate_document()

    first = export_candidate_midi(candidate)
    second = export_candidate_midi(candidate)

    assert first.data == second.data
    assert first.manifest == second.manifest
    assert first.data[:4] == b"MThd"
    assert validate_midi_type1(first.data) == {
        "format": 1,
        "trackCount": len(candidate["tracks"]) + 1,
        "ticksPerQuarter": 960,
    }
    assert first.manifest["sourceRevisionIds"] == ["src_rev_midi_001"]
    assert first.manifest["rightsAttested"] is True
    assert first.manifest["parentVersionId"] == candidate["versionId"]


def test_midi_export_rejects_unaccepted_and_schema_invalid_candidates():
    candidate = _candidate_document()
    draft = deepcopy(candidate)
    draft["status"] = "DRAFT"

    with pytest.raises(ValueError, match="accepted"):
        export_candidate_midi(draft)

    invalid = deepcopy(candidate)
    invalid["tracks"][1]["events"][0]["durationTicks"] = 0
    with pytest.raises(ValueError, match="schema"):
        export_candidate_midi(invalid)


def test_midi_validator_rejects_truncated_or_non_type1_data():
    candidate = _candidate_document()
    artifact = export_candidate_midi(candidate)

    with pytest.raises(ValueError, match="header"):
        validate_midi_type1(artifact.data[:8])

    invalid_header = bytearray(artifact.data)
    invalid_header[9] = 0
    with pytest.raises(ValueError, match="format"):
        validate_midi_type1(bytes(invalid_header))
