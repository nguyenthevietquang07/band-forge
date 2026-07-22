from copy import deepcopy
from datetime import UTC, datetime

import pytest

from bandforge_domain.arrangements import build_arrangement_seed, validate_arrangement_document
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import (
    ArrangementControls,
    build_validator_catalog,
    compare_candidates,
    generate_candidate,
    validate_candidate,
)


def _source_document():
    chart = normalize_chart(
        StructuredChartInput(title="Generator Fixture", key="A_MINOR", bars=["Am", "F", "C", "G"])
    )
    return build_arrangement_seed(
        chart,
        "src_rev_generator_001",
        "sha256:" + "b" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_generator_001",
        version_id="arr_version_generator_001",
    )


def test_deterministic_candidate_is_reproducible_and_lineage_complete():
    document = _source_document()
    controls = ArrangementControls(seed=17)

    first = generate_candidate(document, controls)
    second = generate_candidate(document, controls)

    assert first.accepted is True
    assert first.findings == ()
    assert first.document == second.document
    assert {track["roles"][0]["role"] for track in first.document["tracks"][1:]} == {
        "PULSE",
        "FOUNDATION",
        "COMP",
        "PAD",
    }
    assert first.lineage.seed == 17
    assert first.lineage.engine_version == "rules-baseline-0.1.0"
    assert first.lineage.style_pack_version == "acoustic-pop@1.0.0"
    assert first.lineage.validator_version == "rules-0.1.0"
    assert first.lineage.input_revision == "src_rev_generator_001"
    assert first.document["harmony"] == document["harmony"]
    validate_arrangement_document(first.document)


def test_deterministic_drum_arrangement_uses_groove_accents_and_a_fill():
    result = generate_candidate(_source_document(), ArrangementControls(seed=17))
    drum_track = next(
        track for track in result.document["tracks"] if track["id"] == "generated_drums"
    )
    pieces = {event["kitPiece"] for event in drum_track["events"]}

    assert pieces >= {
        "KICK",
        "SNARE",
        "CLOSED_HAT",
        "OPEN_HAT",
        "CRASH",
        "LOW_TOM",
        "MID_TOM",
        "HIGH_TOM",
    }
    assert len({event["id"] for event in drum_track["events"]}) == len(drum_track["events"])
    validate_arrangement_document(result.document)


def test_candidate_generation_returns_hard_finding_when_source_harmony_unlocks():
    document = _source_document()
    document["harmony"][0]["isLocked"] = False

    result = generate_candidate(document, ArrangementControls(seed=17))

    assert result.accepted is False
    assert result.findings[0].rule_id == "BF-LOCK-004"


def test_candidate_generation_rejects_source_without_rights_attestation():
    document = _source_document()
    document["sourceRefs"][0]["rightsAttested"] = False

    result = generate_candidate(document, ArrangementControls(seed=17))

    assert result.accepted is False
    assert any(finding.rule_id == "BF-RIGHTS-001" for finding in result.findings)


def test_candidate_validation_catches_bar_and_polyphony_violation():
    document = _source_document()
    result = generate_candidate(document, ArrangementControls(seed=17))
    broken = deepcopy(result.document)
    broken["tracks"][1]["events"][0]["startTick"] = 999999
    broken["tracks"][3]["events"][0]["soundingPitches"] = [60, 62, 64, 65, 67]

    findings = validate_candidate(broken, document)

    assert {finding.rule_id for finding in findings} >= {
        "BF-STRUCT-001",
        "BF-POLY-001",
    }


def test_generation_rejects_schema_invalid_source_before_acceptance():
    document = _source_document()
    del document["tracks"]

    result = generate_candidate(document, ArrangementControls(seed=17))

    assert result.accepted is False
    assert any(finding.rule_id == "BF-SCHEMA-001" for finding in result.findings)


def test_generation_rejects_a_schema_invalid_candidate():
    document = _source_document()
    document["global"]["title"] = ""

    result = generate_candidate(document, ArrangementControls(seed=17))

    assert result.accepted is False
    assert any(finding.rule_id == "BF-SCHEMA-001" for finding in result.findings)


def test_candidate_validation_reports_nonpositive_event_durations():
    document = _source_document()
    result = generate_candidate(document, ArrangementControls(seed=17))
    broken = deepcopy(result.document)
    broken["tracks"][1]["events"][0]["durationTicks"] = 0
    broken["tracks"][3]["events"][0]["durationTicks"] = -1

    findings = validate_candidate(broken, document)

    assert sum(finding.rule_id == "BF-TIMING-001" for finding in findings) == 2


def test_candidate_validation_checks_written_and_sounding_ranges():
    document = _source_document()
    result = generate_candidate(document, ArrangementControls(seed=17))
    broken = deepcopy(result.document)
    broken["tracks"][2]["events"][0]["writtenPitch"] = 100
    broken["tracks"][2]["events"][0]["soundingPitch"] = 100
    broken["tracks"][4]["events"][0]["writtenPitches"][0] = 100

    findings = validate_candidate(broken, document)

    assert any(finding.rule_id == "BF-RANGE-001" for finding in findings)
    assert sum(finding.rule_id == "BF-RANGE-002" for finding in findings) == 2


def test_candidate_identity_changes_with_source_revision_and_controls():
    document = _source_document()
    changed_source = deepcopy(document)
    changed_source["sourceRefs"][0]["sourceRevisionId"] = "src_rev_generator_002"

    first = generate_candidate(document, ArrangementControls(seed=17))
    changed_revision = generate_candidate(changed_source, ArrangementControls(seed=17))
    changed_controls = generate_candidate(document, ArrangementControls(seed=17, tempo_bpm=101))

    assert first.document["versionId"] != changed_revision.document["versionId"]
    assert first.document["versionId"] != changed_controls.document["versionId"]


def test_candidate_persists_complete_lineage_in_schema_safe_extensions():
    document = _source_document()
    document["sourceRefs"].append(
        {
            "sourceRevisionId": "src_rev_generator_002",
            "contentHash": "sha256:" + "c" * 64,
            "sourceType": "STRUCTURED",
            "rightsAttested": True,
        }
    )

    result = generate_candidate(document, ArrangementControls(seed=17))
    lineage = result.document["extensions"]["bandforge.generation-lineage"]

    assert lineage == {
        "seed": 17,
        "engineVersion": "rules-baseline-0.1.0",
        "stylePackVersion": "acoustic-pop@1.0.0",
        "validatorVersion": "rules-0.1.0",
        "inputRevisionSet": ["src_rev_generator_001", "src_rev_generator_002"],
        "provenance": "approved-source-locked-rules-baseline",
    }
    validate_arrangement_document(result.document)


def test_unsupported_difficulty_is_rejected_instead_of_silently_ignored():
    with pytest.raises(ValueError, match="BEGINNER"):
        ArrangementControls(difficulty="INTERMEDIATE")


def test_candidate_comparison_returns_bounded_stable_summaries():
    document = _source_document()
    controls = ArrangementControls(tempo_bpm=105)

    first = compare_candidates(document, [11, 17, 23], controls)
    second = compare_candidates(document, [11, 17, 23], controls)

    assert first == second
    assert [summary.seed for summary in first] == [11, 17, 23]
    assert len({summary.candidate_id for summary in first}) == 3
    assert all(summary.accepted for summary in first)
    assert all(summary.hard_finding_count == 0 for summary in first)
    assert all(summary.source_harmony_unchanged for summary in first)
    assert first[0].to_dict()["lineage"]["provenance"] == (
        "approved-source-locked-rules-baseline"
    )


def test_candidate_comparison_rejects_duplicate_or_unbounded_seed_sets():
    document = _source_document()

    with pytest.raises(ValueError, match="distinct"):
        compare_candidates(document, [11, 11])
    with pytest.raises(ValueError, match="8"):
        compare_candidates(document, range(9))


def test_validator_catalog_contains_rules_and_representative_failures():
    catalog = build_validator_catalog(_source_document())

    rule_ids = {rule["ruleId"] for rule in catalog["rules"]}
    failure_ids = {failure["ruleId"] for failure in catalog["representativeFailures"]}

    assert catalog["validatorVersion"] == "rules-0.1.0"
    assert {
        "BF-LOCK-004",
        "BF-RIGHTS-001",
        "BF-SCHEMA-001",
        "BF-TIMING-001",
        "BF-RANGE-001",
        "BF-RANGE-002",
        "BF-POLY-001",
    } <= rule_ids
    assert {
        "BF-LOCK-004",
        "BF-RIGHTS-001",
        "BF-SCHEMA-001",
        "BF-TIMING-001",
        "BF-RANGE-001",
        "BF-RANGE-002",
        "BF-POLY-001",
    } <= failure_ids
    assert all(failure["severity"] == "ERROR" for failure in catalog["representativeFailures"])
