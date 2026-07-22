from bandforge_domain.chart import StructuredChartInput, normalize_chart


def test_normalize_chart_creates_contiguous_four_four_bars() -> None:
    chart = normalize_chart(
        StructuredChartInput(title="Late Set", key="A_MINOR", bars=["Am", "F", "C", "G"])
    )

    assert [measure.start_tick for measure in chart.measures] == [0, 3840, 7680, 11520]
    assert [measure.duration_ticks for measure in chart.measures] == [3840, 3840, 3840, 3840]
    assert [event.duration_ticks for event in chart.harmony if event is not None] == [3840] * 4
    assert chart.findings == []


def test_normalize_chart_returns_finding_instead_of_guessing_unknown_chord() -> None:
    chart = normalize_chart(
        StructuredChartInput(title="Late Set", key="A_MINOR", bars=["Am", "Cmaj9#11"])
    )

    assert chart.harmony[1] is None
    assert chart.findings[0].code == "UNSUPPORTED_CHORD_SYMBOL"
    assert chart.findings[0].bar_ordinal == 2
