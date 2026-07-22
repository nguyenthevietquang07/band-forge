"""Run the Cycle 8 MIDI artifact and scoped-regeneration integrity demo."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from bandforge_domain.arrangements import build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate
from bandforge_domain.midi import export_candidate_midi, validate_midi_type1
from bandforge_domain.regeneration import regenerate_scoped

ROOT = Path(__file__).parents[1]


def main() -> int:
    chart = normalize_chart(
        StructuredChartInput(
            title="Cycle 8 Authored Fixture",
            key="A_MINOR",
            bars=["Am", "F", "C", "G"],
        )
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_cycle8_demo",
        "sha256:" + "1" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_cycle8_demo",
        version_id="version_cycle8_demo",
    )
    generated = generate_candidate(source, ArrangementControls(seed=23, tempo_bpm=108))
    if not generated.accepted:
        raise RuntimeError(f"demo candidate was rejected: {generated.findings}")
    candidate_before = deepcopy(generated.document)
    artifact = export_candidate_midi(generated.document)
    midi_validation = validate_midi_type1(artifact.data)

    regenerated = regenerate_scoped(
        generated.document,
        track_ids=["generated_bass"],
        measure_ids=["measure_002"],
        seed=91,
        mode="SAFE",
    )
    regenerated_artifact = export_candidate_midi(regenerated.document)
    regenerated_validation = validate_midi_type1(regenerated_artifact.data)
    evidence = {
        "sourceRevisionId": source["sourceRefs"][0]["sourceRevisionId"],
        "candidateVersionId": generated.document["versionId"],
        "candidateAccepted": generated.accepted,
        "midiArtifact": {
            "path": "reports/cycle-8-candidate.mid",
            "bytes": len(artifact.data),
            "validation": midi_validation,
            "manifest": artifact.manifest,
        },
        "regeneratedCandidateVersionId": regenerated.document["versionId"],
        "regeneratedMidiArtifact": {
            "path": "reports/cycle-8-regenerated.mid",
            "bytes": len(regenerated_artifact.data),
            "validation": regenerated_validation,
            "manifest": regenerated_artifact.manifest,
        },
        "candidateInputUnchanged": generated.document == candidate_before,
        "sourceHarmonyUnchanged": regenerated.document["harmony"] == source["harmony"],
        "scopedRegeneration": regenerated.manifest,
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "cycle-8-candidate.mid").write_bytes(artifact.data)
    (reports / "cycle-8-regenerated.mid").write_bytes(regenerated_artifact.data)
    (reports / "cycle-8-midi-manifest.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    (reports / "cycle-8-midi-regeneration-demo.md").write_text(
        "# Cycle 8 MIDI Artifact and Scoped-Regeneration Demo\n\n"
        "Authored source fixture: `Am | F | C | G`; no metadata lookup or model call.\n\n"
        f"```json\n{json.dumps(evidence, indent=2)}\n```\n\n"
        "This demonstrates deterministic type-1 MIDI bytes, structural MIDI validation, "
        "rights/provenance manifesting, and immutable SAFE event-scope regeneration. "
        "It does not claim browser playback, audio quality, musician playability, notation, "
        "or support for later regeneration modes.\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
