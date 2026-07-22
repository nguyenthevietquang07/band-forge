"""Immutable playback plans for reviewing accepted canonical candidates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from bandforge_domain.arrangements import validate_arrangement_document

MIN_TEMPO_BPM = 40
MAX_TEMPO_BPM = 220
BEATS_PER_MEASURE = 4
DRUM_KIT_MIDI = {
    "KICK": 36,
    "SNARE": 38,
    "CLOSED_HAT": 42,
    "LOW_TOM": 45,
    "OPEN_HAT": 46,
    "MID_TOM": 47,
    "CRASH": 49,
    "HIGH_TOM": 50,
    "RIDE": 51,
    "PERCUSSION": 39,
}


@dataclass(frozen=True)
class PlaybackControls:
    """User review controls applied without mutating the candidate."""

    muted_track_ids: tuple[str, ...] = ()
    solo_track_ids: tuple[str, ...] = ()
    loop_start_measure_id: str | None = None
    loop_end_measure_id: str | None = None
    metronome: bool = False
    count_in_bars: int = 0
    tempo_override_bpm: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "muted_track_ids", tuple(dict.fromkeys(self.muted_track_ids)))
        object.__setattr__(self, "solo_track_ids", tuple(dict.fromkeys(self.solo_track_ids)))
        if self.count_in_bars not in range(5):
            raise ValueError("count-in bars must be between 0 and 4")
        if self.tempo_override_bpm is not None and not (
            MIN_TEMPO_BPM <= self.tempo_override_bpm <= MAX_TEMPO_BPM
        ):
            raise ValueError(
                f"tempo override must be between {MIN_TEMPO_BPM} and {MAX_TEMPO_BPM} bpm"
            )
        if (self.loop_start_measure_id is None) != (self.loop_end_measure_id is None):
            raise ValueError("loop start and end measures must be supplied together")


@dataclass(frozen=True)
class PlaybackEvent:
    track_id: str
    event_id: str
    kind: str
    start_tick: int
    duration_ticks: int
    pitches: tuple[int, ...]
    velocity: int


@dataclass(frozen=True)
class PlaybackPlan:
    candidate_version_id: str
    lineage: Mapping[str, Any]
    tempo_bpm: int
    active_track_ids: tuple[str, ...]
    events: tuple[PlaybackEvent, ...]
    loop_start_tick: int
    loop_end_tick: int
    metronome: bool
    count_in_bars: int


def build_playback_plan(
    candidate: Mapping[str, Any], controls: PlaybackControls | None = None
) -> PlaybackPlan:
    """Build a deterministic event projection for an accepted candidate."""
    controls = controls or PlaybackControls()
    _require_accepted_candidate(candidate)
    base_tempo = candidate["global"]["tempoMap"][0]["bpm"]
    if not MIN_TEMPO_BPM <= base_tempo <= MAX_TEMPO_BPM:
        raise ValueError(
            f"candidate tempo must be between {MIN_TEMPO_BPM} and {MAX_TEMPO_BPM} bpm"
        )
    track_ids = tuple(track["id"] for track in candidate["tracks"])
    _require_known_tracks(controls, track_ids)
    loop_start_tick, loop_end_tick = _loop_bounds(candidate, controls)
    active_track_ids = tuple(
        track_id
        for track_id in track_ids
        if (not controls.solo_track_ids or track_id in controls.solo_track_ids)
        and track_id not in controls.muted_track_ids
    )
    events = [
        playback_event
        for track in candidate["tracks"]
        if track["id"] in active_track_ids
        for playback_event in _track_events(track, loop_start_tick, loop_end_tick)
    ]
    if controls.metronome:
        events.extend(_click_events("metronome", loop_start_tick, loop_end_tick))
    if controls.count_in_bars:
        events.extend(
            _click_events(
                "count-in",
                loop_start_tick - controls.count_in_bars * _measure_ticks(candidate),
                loop_start_tick,
            )
        )
    events.sort(key=lambda event: (event.start_tick, event.track_id, event.event_id))
    return PlaybackPlan(
        candidate_version_id=candidate["versionId"],
        lineage=candidate["extensions"]["bandforge.generation-lineage"],
        tempo_bpm=controls.tempo_override_bpm or base_tempo,
        active_track_ids=active_track_ids,
        events=tuple(events),
        loop_start_tick=loop_start_tick,
        loop_end_tick=loop_end_tick,
        metronome=controls.metronome,
        count_in_bars=controls.count_in_bars,
    )


def _require_accepted_candidate(candidate: Mapping[str, Any]) -> None:
    if candidate.get("status") not in {"CANDIDATE", "ACCEPTED"}:
        raise ValueError("playback requires an accepted candidate")
    summary = candidate.get("validationSummary", {})
    if summary.get("status") != "VALID" or summary.get("errorCount") != 0:
        raise ValueError("playback requires an accepted candidate")
    try:
        validate_arrangement_document(candidate)
    except ValueError as error:
        raise ValueError(f"candidate schema invalid: {error}") from error
    if not all(reference.get("rightsAttested") is True for reference in candidate["sourceRefs"]):
        raise ValueError("playback requires rights-attested source references")


def _require_known_tracks(controls: PlaybackControls, track_ids: Sequence[str]) -> None:
    known = set(track_ids)
    if not set(controls.solo_track_ids) <= known:
        raise ValueError("solo track scope contains an unknown track")
    if not set(controls.muted_track_ids) <= known:
        raise ValueError("mute track scope contains an unknown track")


def _loop_bounds(
    candidate: Mapping[str, Any], controls: PlaybackControls
) -> tuple[int, int]:
    measures = candidate["measures"]
    if controls.loop_start_measure_id is None:
        return measures[0]["startTick"], measures[-1]["startTick"] + measures[-1]["durationTicks"]
    by_id = {measure["id"]: measure for measure in measures}
    start = by_id.get(controls.loop_start_measure_id)
    end = by_id.get(controls.loop_end_measure_id)
    if start is None or end is None:
        raise ValueError("loop measure range contains an unknown measure")
    start_index = measures.index(start)
    end_index = measures.index(end)
    if start_index > end_index:
        raise ValueError("loop start measure must not follow loop end measure")
    return start["startTick"], end["startTick"] + end["durationTicks"]


def _measure_ticks(candidate: Mapping[str, Any]) -> int:
    measure = candidate["measures"][0]
    return measure["durationTicks"]


def _track_events(
    track: Mapping[str, Any], loop_start_tick: int, loop_end_tick: int
) -> list[PlaybackEvent]:
    output: list[PlaybackEvent] = []
    for event in track["events"]:
        if event["type"] not in {"NOTE", "CHORD", "DRUM_HIT"}:
            continue
        if not loop_start_tick <= event["startTick"] < loop_end_tick:
            continue
        pitches = event.get("soundingPitches")
        if pitches is None and event.get("type") == "NOTE":
            pitches = [event["soundingPitch"]]
        if pitches is None and event.get("type") == "DRUM_HIT":
            midi_pitch = DRUM_KIT_MIDI.get(event.get("kitPiece"))
            pitches = [] if midi_pitch is None else [midi_pitch]
        output.append(
            PlaybackEvent(
                track_id=track["id"],
                event_id=event["id"],
                kind=event["type"],
                start_tick=event["startTick"],
                duration_ticks=event["durationTicks"],
                pitches=tuple(pitches or ()),
                velocity=event.get("velocity", 80),
            )
        )
    return output


def _click_events(track_id: str, start_tick: int, end_tick: int) -> list[PlaybackEvent]:
    beat_ticks = 960
    output: list[PlaybackEvent] = []
    tick = start_tick
    ordinal = 0
    while tick < end_tick:
        output.append(
            PlaybackEvent(
                track_id=track_id,
                event_id=f"{track_id}_click_{ordinal:04d}",
                kind="CLICK",
                start_tick=tick,
                duration_ticks=120,
                pitches=(84 if ordinal % BEATS_PER_MEASURE == 0 else 72,),
                velocity=92,
            )
        )
        tick += beat_ticks
        ordinal += 1
    return output
