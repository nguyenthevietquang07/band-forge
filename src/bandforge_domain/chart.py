"""Structured chord-chart input and deterministic canonical timeline creation."""

from __future__ import annotations

from dataclasses import dataclass

from bandforge_domain.chords import ParseFinding, parse_chord

TICKS_PER_QUARTER = 960
FOUR_FOUR_BAR_TICKS = TICKS_PER_QUARTER * 4


@dataclass(frozen=True)
class StructuredChartInput:
    title: str
    key: str
    bars: list[str]


@dataclass(frozen=True)
class Measure:
    ordinal: int
    start_tick: int
    duration_ticks: int


@dataclass(frozen=True)
class HarmonyEvent:
    ordinal: int
    start_tick: int
    duration_ticks: int
    root_pitch_class: int
    quality: str
    extensions: list[str]
    display_symbol: str
    bass_pitch_class: int | None


@dataclass(frozen=True)
class NormalizedChart:
    source: StructuredChartInput
    measures: list[Measure]
    harmony: list[HarmonyEvent | None]
    findings: list[ParseFinding]


def normalize_chart(request: StructuredChartInput) -> NormalizedChart:
    """Create a 4/4 locked source grid from one user-authored chord per bar."""
    measures: list[Measure] = []
    harmony: list[HarmonyEvent | None] = []
    findings: list[ParseFinding] = []

    for ordinal, symbol in enumerate(request.bars, start=1):
        start_tick = (ordinal - 1) * FOUR_FOUR_BAR_TICKS
        measures.append(Measure(ordinal, start_tick, FOUR_FOUR_BAR_TICKS))
        parsed = parse_chord(symbol)
        if isinstance(parsed, ParseFinding):
            findings.append(ParseFinding(parsed.code, parsed.message, ordinal))
            harmony.append(None)
            continue
        harmony.append(
            HarmonyEvent(
                ordinal=ordinal,
                start_tick=start_tick,
                duration_ticks=FOUR_FOUR_BAR_TICKS,
                root_pitch_class=parsed.root_pitch_class,
                quality=parsed.quality,
                extensions=parsed.extensions,
                display_symbol=parsed.display_symbol,
                bass_pitch_class=parsed.bass_pitch_class,
            )
        )

    return NormalizedChart(request, measures, harmony, findings)
