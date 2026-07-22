"""Run deterministic candidate comparison and validator-catalog evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from bandforge_domain.arrangements import build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import (
    ArrangementControls,
    build_validator_catalog,
    compare_candidates,
)

ROOT = Path(__file__).parents[1]


def main() -> int:
    chart = normalize_chart(
        StructuredChartInput(
            title="Cycle 7 Authored Fixture",
            key="A_MINOR",
            bars=["Am", "F", "C", "G"],
        )
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_cycle7_demo",
        "sha256:" + "d" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_cycle7_demo",
        version_id="arr_version_cycle7_demo",
    )
    summaries = compare_candidates(
        source,
        [11, 17, 23],
        ArrangementControls(style="acoustic-pop", tempo_bpm=105, difficulty="BEGINNER"),
    )
    catalog = build_validator_catalog(source)
    evidence = {
        "sourceRevisionId": source["sourceRefs"][0]["sourceRevisionId"],
        "candidateCount": len(summaries),
        "candidates": [summary.to_dict() for summary in summaries],
        "sameSeedReplay": compare_candidates(
            source,
            [17],
            ArrangementControls(style="acoustic-pop", tempo_bpm=105, difficulty="BEGINNER"),
        )[0].to_dict()
        == summaries[1].to_dict(),
        "validatorCatalog": catalog,
    }
    report = ROOT / "reports" / "cycle-7-candidate-validation-demo.md"
    report.write_text(
        "# Cycle 7 Candidate Comparison and Validator Catalog Demo\n\n"
        "Authored source fixture: `Am | F | C | G`; no metadata lookup or model call.\n\n"
        f"```json\n{json.dumps(evidence, indent=2)}\n```\n\n"
        "This demonstrates bounded deterministic candidate comparison and machine-readable "
        "hard-validator evidence. It does not claim musical quality, playability, audio, "
        "notation, regeneration, learned generation, or production readiness.\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
