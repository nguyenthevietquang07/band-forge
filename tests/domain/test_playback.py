from copy import deepcopy
from datetime import UTC, datetime

import pytest

from bandforge_domain.arrangements import build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate
from bandforge_domain.playback import PlaybackControls, build_playback_plan


def _candidate_document():
    chart = normalize_chart(
        StructuredChartInput(
            title="Playback Fixture", key="A_MINOR", bars=["Am", "F", "C", "G"]
        )
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_playback_001",
        "sha256:" + "d" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_playback_001",
        version_id="version_playback_001",
    )
    result = generate_candidate(source, ArrangementControls(seed=31, tempo_bpm=104))
    assert result.accepted
    return result.document


def test_playback_plan_is_immutable_and_uses_accepted_candidate_gate():
    candidate = _candidate_document()
    before = deepcopy(candidate)

    plan = build_playback_plan(candidate)

    assert candidate == before
    assert plan.candidate_version_id == candidate["versionId"]
    assert plan.lineage == candidate["extensions"]["bandforge.generation-lineage"]
    assert plan.tempo_bpm == 104
    assert plan.events
    assert plan.active_track_ids == tuple(track["id"] for track in candidate["tracks"])

    draft = deepcopy(candidate)
    draft["status"] = "DRAFT"
    with pytest.raises(ValueError, match="accepted"):
        build_playback_plan(draft)


def test_playback_plan_applies_solo_before_mute_and_preserves_loop_boundaries():
    candidate = _candidate_document()
    controls = PlaybackControls(
        muted_track_ids=("generated_bass",),
        solo_track_ids=("generated_guitar", "generated_bass"),
        loop_start_measure_id="measure_002",
        loop_end_measure_id="measure_003",
    )

    plan = build_playback_plan(candidate, controls)

    assert plan.active_track_ids == ("generated_guitar",)
    assert {event.track_id for event in plan.events} == {"generated_guitar"}
    assert plan.loop_start_tick == 3840
    assert plan.loop_end_tick == 11520
    assert all(
        plan.loop_start_tick <= event.start_tick < plan.loop_end_tick
        for event in plan.events
    )


def test_playback_plan_adds_count_in_metronome_and_bounded_tempo_override():
    candidate = _candidate_document()
    plan = build_playback_plan(
        candidate,
        PlaybackControls(
            metronome=True,
            count_in_bars=2,
            tempo_override_bpm=120,
        ),
    )

    click_events = [event for event in plan.events if event.kind == "CLICK"]
    assert len(click_events) == 24
    assert click_events[0].start_tick == -7680
    assert click_events[-1].start_tick == 3840 * 4 - 960
    assert plan.tempo_bpm == 120
    assert plan.count_in_bars == 2
    assert plan.metronome is True

    with pytest.raises(ValueError, match="tempo"):
        build_playback_plan(candidate, PlaybackControls(tempo_override_bpm=239))
    with pytest.raises(ValueError, match="tempo"):
        build_playback_plan(candidate, PlaybackControls(tempo_override_bpm=39))


def test_playback_plan_rejects_schema_and_rights_failures():
    candidate = _candidate_document()
    invalid = deepcopy(candidate)
    invalid["tracks"][1]["events"][0]["durationTicks"] = 0
    with pytest.raises(ValueError, match="schema"):
        build_playback_plan(invalid)

    no_rights = deepcopy(candidate)
    no_rights["sourceRefs"][0]["rightsAttested"] = False
    with pytest.raises(ValueError, match="rights"):
        build_playback_plan(no_rights)

    high_tempo = deepcopy(candidate)
    high_tempo["global"]["tempoMap"][0]["bpm"] = 240
    with pytest.raises(ValueError, match="candidate tempo"):
        build_playback_plan(high_tempo)


def test_playback_plan_maps_generated_drum_kit_pieces_to_general_midi_pitches():
    candidate = _candidate_document()

    drum_events = [
        event
        for track in candidate["tracks"]
        if track["id"] == "generated_drums"
        for event in track["events"]
        if event["type"] == "DRUM_HIT"
    ]

    plan = build_playback_plan(candidate)
    pitches_by_event = {
        event.event_id: event.pitches
        for event in plan.events
        if event.track_id == "generated_drums"
    }

    assert drum_events
    expected_pitches = {
        "KICK": (36,),
        "SNARE": (38,),
        "CLOSED_HAT": (42,),
        "OPEN_HAT": (46,),
        "CRASH": (49,),
        "LOW_TOM": (45,),
        "MID_TOM": (47,),
        "HIGH_TOM": (50,),
    }
    for drum_event in drum_events:
        assert pitches_by_event[drum_event["id"]] == expected_pitches[drum_event["kitPiece"]]


def test_playback_controls_reject_invalid_loop_and_count_in_values():
    with pytest.raises(ValueError, match="count-in"):
        PlaybackControls(count_in_bars=5)
    with pytest.raises(ValueError, match="solo"):
        build_playback_plan(_candidate_document(), PlaybackControls(solo_track_ids=("missing",)))
