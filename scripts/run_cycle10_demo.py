"""Run the Cycle 10 playback-plan demo and save its evidence."""

from __future__ import annotations

import json
import shutil
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from bandforge_domain.arrangements import build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate
from bandforge_domain.playback import PlaybackControls, build_playback_plan

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "cycle-10-mvp-playback-demo.md"


def candidate_fixture() -> dict:
    chart = normalize_chart(
        StructuredChartInput(
            title="Cycle 10 Candidate Playback",
            key="A_MINOR",
            bars=["Am", "F", "C", "G"],
        )
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_cycle10_demo",
        "sha256:" + "e" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_cycle10_demo",
        version_id="version_cycle10_source",
    )
    result = generate_candidate(source, ArrangementControls(seed=41, tempo_bpm=104))
    if not result.accepted:
        raise RuntimeError(f"fixture candidate was rejected: {result.findings}")
    candidate = deepcopy(result.document)
    candidate["status"] = "ACCEPTED"
    return candidate


def main() -> None:
    candidate = candidate_fixture()
    before = deepcopy(candidate)
    controls = PlaybackControls(
        muted_track_ids=("generated_bass",),
        solo_track_ids=("generated_bass", "generated_guitar"),
        loop_start_measure_id="measure_002",
        loop_end_measure_id="measure_003",
        metronome=True,
        count_in_bars=1,
        tempo_override_bpm=116,
    )
    plan = build_playback_plan(candidate, controls)
    if candidate != before:
        raise RuntimeError("playback planning mutated the canonical candidate")

    browsers = {
        "agentBrowser": shutil.which("agent-browser") is not None,
        "chrome": shutil.which("chrome") is not None,
        "msedge": shutil.which("msedge") is not None,
    }
    evidence = {
        "candidateVersionId": plan.candidate_version_id,
        "candidateStatus": candidate["status"],
        "sourceRevisionIds": [ref["sourceRevisionId"] for ref in candidate["sourceRefs"]],
        "rightsAttested": all(ref["rightsAttested"] for ref in candidate["sourceRefs"]),
        "lineage": candidate["extensions"]["bandforge.generation-lineage"],
        "controls": {
            "mutedTrackIds": list(controls.muted_track_ids),
            "soloTrackIds": list(controls.solo_track_ids),
            "loopMeasureIds": [controls.loop_start_measure_id, controls.loop_end_measure_id],
            "metronome": controls.metronome,
            "countInBars": controls.count_in_bars,
            "tempoOverrideBpm": controls.tempo_override_bpm,
        },
        "plan": {
            "tempoBpm": plan.tempo_bpm,
            "activeTrackIds": list(plan.active_track_ids),
            "eventCount": len(plan.events),
            "musicalEventCount": sum(event.kind != "CLICK" for event in plan.events),
            "clickEventCount": sum(event.kind == "CLICK" for event in plan.events),
            "loopStartTick": plan.loop_start_tick,
            "loopEndTick": plan.loop_end_tick,
        },
        "canonicalCandidateUnchanged": candidate == before,
        "browserAutomationAvailable": browsers,
        "sourceBoundary": (
            "Candidate notes derive only from the supplied structured chart; no metadata "
            "or streaming lookup supplies music."
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Cycle 10 MVP playback demo\n\n"
        "Command: `python scripts/run_cycle10_demo.py`\n\n"
        "The demo builds an accepted, rights-attested deterministic candidate from "
        "an authored structured chart, then constructs an immutable playback plan "
        "with mute/solo, measure looping, metronome, count-in, and tempo override.\n\n"
        "```json\n" + json.dumps(evidence, indent=2) + "\n```\n\n"
        "The web screen consumes the accepted candidate projection returned after "
        "the approved source seed. Browser automation availability is recorded "
        "above; no hosted audio or private-beta behavior is claimed.\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2))
    print(f"Evidence written to {REPORT}")


if __name__ == "__main__":
    main()
