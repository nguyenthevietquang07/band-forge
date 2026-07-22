from copy import deepcopy
from datetime import UTC, datetime

import pytest

from bandforge_domain.arrangements import build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate
from bandforge_domain.regeneration import regenerate_scoped


def _candidate_document():
    chart = normalize_chart(
        StructuredChartInput(
            title="Regeneration Fixture", key="A_MINOR", bars=["Am", "F", "C", "G"]
        )
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_regen_001",
        "sha256:" + "f" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_regen_001",
        version_id="version_regen_001",
    )
    result = generate_candidate(source, ArrangementControls(seed=23))
    assert result.accepted
    return result.document


def test_safe_regeneration_is_immutable_and_changes_only_selected_scope():
    candidate = _candidate_document()
    selected_track = "generated_bass"
    selected_measure = "measure_002"
    before = deepcopy(candidate)

    result = regenerate_scoped(
        candidate,
        track_ids=[selected_track],
        measure_ids=[selected_measure],
        seed=91,
        mode="SAFE",
    )

    assert result.document is not candidate
    assert candidate == before
    assert result.document["versionId"] != candidate["versionId"]
    assert result.document["parentVersionId"] == candidate["versionId"]
    assert result.manifest["mode"] == "SAFE"
    assert result.manifest["trackIds"] == [selected_track]
    assert result.manifest["measureIds"] == [selected_measure]
    assert result.manifest["changedEventIds"]
    assert result.manifest["preservedOutsideScope"] is True

    for before_track, after_track in zip(
        candidate["tracks"], result.document["tracks"], strict=True
    ):
        for before_event, after_event in zip(
            before_track["events"], after_track["events"], strict=True
        ):
            in_scope = (
                before_track["id"] == selected_track
                and before_event["id"] in result.manifest["changedEventIds"]
            )
            if not in_scope:
                assert after_event == before_event


def test_safe_regeneration_persists_scope_diff_and_lineage():
    candidate = _candidate_document()

    result = regenerate_scoped(
        candidate,
        track_ids=["generated_guitar"],
        measure_ids=["measure_001", "measure_003"],
        seed=7,
    )

    proof = result.document["extensions"]["bandforge.regeneration"]
    assert proof == result.manifest
    assert result.manifest["sourceRevisionIds"] == ["src_rev_regen_001"]
    assert result.manifest["rightsAttested"] is True
    assert result.manifest["provenance"] == candidate["extensions"][
        "bandforge.generation-lineage"
    ]


def test_regeneration_rejects_invalid_candidates_scope_and_modes():
    candidate = _candidate_document()
    invalid = deepcopy(candidate)
    invalid["validationSummary"]["status"] = "INVALID"

    with pytest.raises(ValueError, match="accepted"):
        regenerate_scoped(invalid, ["generated_bass"], ["measure_001"], seed=1)
    with pytest.raises(ValueError, match="SAFE"):
        regenerate_scoped(candidate, ["generated_bass"], ["measure_001"], seed=1, mode="FRESH")
    with pytest.raises(ValueError, match="track"):
        regenerate_scoped(candidate, ["missing_track"], ["measure_001"], seed=1)
    with pytest.raises(ValueError, match="measure"):
        regenerate_scoped(candidate, ["generated_bass"], ["missing_measure"], seed=1)
