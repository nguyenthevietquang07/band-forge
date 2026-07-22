from copy import deepcopy
from datetime import UTC, datetime

import pytest

from bandforge_domain.arrangements import build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate
from bandforge_domain.notation import export_candidate_musicxml, validate_musicxml


def _candidate_document():
    chart = normalize_chart(
        StructuredChartInput(title="Notation Fixture", key="A_MINOR", bars=["Am", "F", "C", "G"])
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_notation_001",
        "sha256:" + "a" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_notation_001",
        version_id="version_notation_001",
    )
    result = generate_candidate(source, ArrangementControls(seed=17, tempo_bpm=108))
    assert result.accepted
    return result.document


def test_musicxml_export_is_deterministic_and_structurally_traceable():
    candidate = _candidate_document()

    first = export_candidate_musicxml(candidate)
    second = export_candidate_musicxml(candidate)

    assert first.data == second.data
    assert first.manifest == second.manifest
    assert first.data.startswith(b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    assert validate_musicxml(first.data, candidate) == {
        "format": "MusicXML 4.0",
        "root": "score-partwise",
        "divisions": 960,
        "partCount": len(candidate["tracks"]),
        "measureCount": len(candidate["measures"]),
    }
    assert first.manifest["sourceRevisionIds"] == ["src_rev_notation_001"]
    assert first.manifest["acceptedVersionId"] == candidate["versionId"]
    assert first.manifest["rightsAttested"] is True
    assert first.manifest["lineage"] == candidate["extensions"]["bandforge.generation-lineage"]


def test_musicxml_export_rejects_unaccepted_schema_invalid_rights_and_overflow():
    candidate = _candidate_document()

    draft = deepcopy(candidate)
    draft["status"] = "DRAFT"
    with pytest.raises(ValueError, match="accepted"):
        export_candidate_musicxml(draft)

    invalid_schema = deepcopy(candidate)
    invalid_schema["global"]["ticksPerQuarter"] = 480
    with pytest.raises(ValueError, match="schema"):
        export_candidate_musicxml(invalid_schema)

    unattested = deepcopy(candidate)
    unattested["sourceRefs"][0]["rightsAttested"] = False
    with pytest.raises(ValueError, match="rights"):
        export_candidate_musicxml(unattested)

    overflow = deepcopy(candidate)
    overflow["tracks"][1]["events"][0]["startTick"] = 999999
    with pytest.raises(ValueError, match="measure"):
        export_candidate_musicxml(overflow)


def test_musicxml_validator_rejects_malformed_xml_and_wrong_divisions():
    candidate = _candidate_document()
    artifact = export_candidate_musicxml(candidate)

    with pytest.raises(ValueError, match="XML"):
        validate_musicxml(artifact.data[:-20], candidate)

    wrong_divisions = artifact.data.replace(
        b"<divisions>960</divisions>", b"<divisions>480</divisions>", 1
    )
    with pytest.raises(ValueError, match="divisions"):
        validate_musicxml(wrong_divisions, candidate)


def test_musicxml_validator_rejects_measure_identity_drift():
    candidate = _candidate_document()
    artifact = export_candidate_musicxml(candidate)
    drifted = artifact.data.replace(b'id="measure_001"', b'id="measure_999"', 1)

    with pytest.raises(ValueError, match="measure identity"):
        validate_musicxml(drifted, candidate)


def test_musicxml_export_rejects_missing_or_mistyped_lineage():
    candidate = _candidate_document()

    missing = deepcopy(candidate)
    del missing["extensions"]["bandforge.generation-lineage"]
    with pytest.raises(ValueError, match="lineage"):
        export_candidate_musicxml(missing)

    mistyped = deepcopy(candidate)
    mistyped["extensions"]["bandforge.generation-lineage"]["seed"] = "17"
    with pytest.raises(ValueError, match="lineage"):
        export_candidate_musicxml(mistyped)


def test_musicxml_export_accepts_direction_only_track():
    candidate = _candidate_document()
    candidate["tracks"][0]["events"] = [
        {
            "id": "direction_001",
            "type": "DIRECTION",
            "startTick": 0,
            "durationTicks": 960,
            "kind": "TEXT",
            "value": "Intro",
        }
    ]

    artifact = export_candidate_musicxml(candidate)

    assert b"<direction>" in artifact.data
    assert validate_musicxml(artifact.data, candidate)["measureCount"] == 4


def test_standalone_musicxml_validator_rejects_zero_measure_score():
    empty_score = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P001"><part-name>Keys</part-name></score-part></part-list>
  <part id="P001" />
</score-partwise>
"""

    with pytest.raises(ValueError, match="measure"):
        validate_musicxml(empty_score)
