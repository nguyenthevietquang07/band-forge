from datetime import UTC, datetime

import pytest

from bandforge_domain.arrangements import (
    SourceNotReadyError,
    build_arrangement_seed,
    validate_arrangement_document,
)
from bandforge_domain.chart import StructuredChartInput, normalize_chart

FIXED_NOW = datetime(2026, 7, 19, tzinfo=UTC)
SOURCE_HASH = "sha256:" + "a" * 64


def test_build_arrangement_seed_matches_committed_schema() -> None:
    chart = normalize_chart(StructuredChartInput(title="Late Set", key="A_MINOR", bars=["Am", "F"]))

    document = build_arrangement_seed(chart, "src_rev_0001", SOURCE_HASH, FIXED_NOW)

    validate_arrangement_document(document)
    assert document["global"]["ticksPerQuarter"] == 960
    assert document["harmony"][0]["isLocked"] is True
    assert document["tracks"][0]["name"] == "Source Guide"
    assert document["tracks"][0]["events"] == []


def test_build_arrangement_seed_rejects_unresolved_source_findings() -> None:
    chart = normalize_chart(
        StructuredChartInput(title="Late Set", key="A_MINOR", bars=["Cmaj9#11"])
    )

    with pytest.raises(SourceNotReadyError, match="Resolve every source finding"):
        build_arrangement_seed(chart, "src_rev_0001", SOURCE_HASH, FIXED_NOW)
