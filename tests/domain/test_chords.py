from bandforge_domain.chords import ParsedChord, ParseFinding, parse_chord


def test_parse_chord_preserves_display_symbol_and_root() -> None:
    parsed = parse_chord("F#m7")

    assert isinstance(parsed, ParsedChord)
    assert parsed.display_symbol == "F#m7"
    assert parsed.root_pitch_class == 6
    assert parsed.quality == "MINOR"
    assert parsed.extensions == ["7"]


def test_parse_chord_returns_finding_for_unsupported_symbol() -> None:
    result = parse_chord("Cmaj9#11")

    assert isinstance(result, ParseFinding)
    assert result.code == "UNSUPPORTED_CHORD_SYMBOL"
    assert result.message == "Chord symbol 'Cmaj9#11' is not supported by this source editor."
