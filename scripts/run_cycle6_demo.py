"""Run the deterministic generator baseline against an authored source fixture."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from bandforge_domain.arrangements import build_arrangement_seed, validate_arrangement_document
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate

ROOT = Path(__file__).parents[1]


def main() -> int:
    chart = normalize_chart(
        StructuredChartInput(
            title="Cycle 6 Authored Fixture",
            key="A_MINOR",
            bars=["Am", "F", "C", "G"],
        )
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_cycle6_demo",
        "sha256:" + "c" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_cycle6_demo",
        version_id="arr_version_cycle6_demo",
    )
    first = generate_candidate(source, ArrangementControls(seed=17, tempo_bpm=100))
    second = generate_candidate(source, ArrangementControls(seed=17, tempo_bpm=100))
    validate_arrangement_document(first.document)
    evidence = {
        "sourceRevisionId": source["sourceRefs"][0]["sourceRevisionId"],
        "candidateVersionId": first.document["versionId"],
        "accepted": first.accepted,
        "sameSeedSemanticReplay": first.document == second.document,
        "trackInstruments": [track["instrument"] for track in first.document["tracks"]],
        "sourceHarmonyUnchanged": first.document["harmony"] == source["harmony"],
        "lineage": {
            "seed": first.lineage.seed,
            "engineVersion": first.lineage.engine_version,
            "stylePackVersion": first.lineage.style_pack_version,
            "validatorVersion": first.lineage.validator_version,
            "inputRevision": first.lineage.input_revision,
        },
        "findingCount": len(first.findings),
    }
    report = ROOT / "reports" / "cycle-6-generator-demo.md"
    report.write_text(
        "# Cycle 6 Deterministic Generator Demo\n\n"
        "Authored source fixture: `Am | F | C | G`; no metadata lookup or model call.\n\n"
        f"```json\n{json.dumps(evidence, indent=2)}\n```\n\n"
        "This demonstrates a deterministic rules baseline and schema-valid candidate "
        "document. It does not claim playability, audio, learned generation, or "
        "production readiness.\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
