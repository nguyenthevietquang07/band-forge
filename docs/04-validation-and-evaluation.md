# Validation and Evaluation

## 1. What Validation Can and Cannot Prove

Validation can prove structural and contract properties and can detect many
theory, orchestration, and playability risks. It cannot prove that musicians
will enjoy an arrangement, that every player finds it comfortable, or that a
performance will sound flawless. BandForge therefore uses three layers:

1. deterministic hard validation;
2. style/playability scoring and warnings;
3. human playback, score review, and rehearsal feedback.

## 2. Finding Contract

Every finding has:

```json
{
  "ruleId": "BF-RHY-001",
  "ruleVersion": "1.2.0",
  "severity": "ERROR",
  "category": "STRUCTURE",
  "message": "Bass events exceed measure duration by 120 ticks.",
  "trackId": "bass",
  "sectionInstanceId": "chorus-1",
  "measureId": "m-17",
  "startTick": 61440,
  "eventIds": ["ev-991"],
  "isRepairable": true,
  "suggestedAction": "Trim the final note to the bar boundary."
}
```

Severities are `ERROR`, `WARNING`, and `INFO`. `ERROR` blocks readiness.
Findings are stable machine contracts; UI wording may be localized separately.

## 3. Hard Validators

### Contract and structure

- schema validation and supported schema version;
- globally unique stable IDs;
- contiguous, non-overlapping measure grid;
- valid section-to-measure coverage;
- nonnegative integer timing and positive durations;
- events contained in arrangement and track bounds;
- exact bar-duration accounting for notated voices;
- valid tempo, key, meter, and chord vocabularies;
- lock preservation outside regeneration scope.

### Instrument feasibility

- written and sounding pitch in absolute range;
- polyphony not above instrument/profile maximum;
- keyboard hand-span and guitar shape/fret constraints where a concrete shape is
  emitted;
- monophonic instruments have no overlapping notes;
- drum notes map to supported normalized kit pieces;
- transposing instruments maintain written/sounding consistency.

### Artifact validity

- MusicXML validates against the MusicXML 4.0 XSD and imports into the chosen
  notation renderer fixture suite;
- MIDI parses after export, has matching track count/time map, and no hanging
  notes;
- PDF exists, has expected pages, no empty player part, and renders in a visual
  smoke test;
- artifact SHA-256, media type, and size match metadata.

## 4. Theory and Arrangement Rules

Theory rules are style-aware. Parallel fifths may matter in one voicing pack and
be irrelevant in another; therefore they are not universal hard errors.

Checks include:

- note-to-current-chord classification: chord tone, available tension,
  diatonic non-chord tone, chromatic approach, or unresolved conflict;
- accented dissonance preparation/resolution where required by style;
- guide-tone and tendency-tone resolution;
- bass compatibility with root/slash-bass intent;
- melody versus reharmonized chord compatibility;
- voice crossing/overlap and excessive parallel motion where enabled;
- repeated register collisions between bass/left hand/guitar;
- comping onset collision and combined density;
- fill intrusion under melody or vocal phrase;
- phrase continuity, cadence support, and deliberate space;
- drum/bass kick alignment ranges by style;
- excessive simultaneous activity across all supporting tracks.

`music21` can support chord, interval, key, and voice-leading analysis, but
BandForge rule semantics remain in versioned rule packs so library behavior does
not silently define the product.

## 5. Playability Score

Compute per-track and aggregate playability from transparent features:

- range comfort and range-edge exposure;
- maximum and percentile leap size at tempo;
- note density and shortest inter-onset interval;
- syncopation and subdivision complexity;
- chord size, span, inversion change, fret-position change;
- repeated-note speed and articulation change;
- continuous playing/endurance without rests;
- sight-reading complexity: accidentals, tuplets, ties, ledger lines, rhythmic
  vocabulary, and page turns;
- independence burden when a player sings and plays, if selected.

Map score bands to `BEGINNER`, `INTERMEDIATE`, and `ADVANCED` using calibrated
thresholds per instrument. Until calibrated with musicians, label the result a
heuristic estimate and expose its features.

## 6. Repair Loop

Only allow repairs with local, predictable effects:

- quantize an event within tolerance;
- trim/split a note at a bar boundary and add a tie;
- octave-shift into range;
- remove an optional chord tone;
- select a nearby legal voicing;
- replace an unresolved passing tone;
- reduce fill density or move it to an allowed window.

The repairer produces a patch and new finding run. It may perform at most three
passes per candidate and may not alter locked material. Nonlocal harmonic or
structural errors reject the candidate rather than triggering an uncontrolled
rewrite.

## 7. Candidate Scoring

After hard validation, rank with a versioned weighted score:

```text
score = 0.25 conditional_adherence
      + 0.20 playability
      + 0.15 harmonic_coherence
      + 0.15 rhythmic_coordination
      + 0.10 role_balance
      + 0.10 phrase_structure
      + 0.05 calibrated_novelty
      - warning_penalties
```

Weights are initial hypotheses. Evaluation reports must record component scores,
rule-pack version, and weight-set ID. Never tune against the final held-out test
set.

## 8. Diversity and Similarity

Represent each arrangement with bar/track feature vectors:

- normalized onset histogram;
- pitch-class and interval histograms;
- chord-voicing class;
- register and density curves;
- role assignment sequence;
- fill locations;
- n-grams of abstract rhythm/pitch intervals.

Use a weighted distance to filter near-identical candidates and enforce the
requested variation band. Add a nearest-neighbor search against licensed
training examples for memorization review; a close match is quarantined for
inspection, not automatically claimed as plagiarism detection.

## 9. Offline Evaluation Suite

### Fixture corpus

Maintain hand-authored, redistributable fixtures covering keys, supported meters,
styles, chord qualities, inversions, song forms, difficulty levels, invalid
inputs, and edge cases. Each fixture states expected hard findings and invariants.

### Objective metrics

- hard-valid candidate rate;
- control adherence by field;
- lock-preservation rate;
- candidate diversity and novelty-band pass rate;
- range/polyphony/density/playability distributions;
- chord-tone and available-tension rates by metrical strength;
- groove consistency, pitch-class entropy, empty-beat/measure rate;
- cross-track onset collision and register-overlap metrics;
- export round-trip loss and artifact success;
- P50/P95 latency, peak memory, model calls, and cost per job.

MusPy offers objective pitch/rhythm metrics, but they are diagnostic statistics,
not direct measures of musical quality.

### Human evaluation

Use blinded A/B or ranked studies with musicians. Stratify by instrument and
level. Ask separately about:

- part playability;
- role clarity and usefulness;
- stylistic fit;
- band coherence;
- musical interest without distraction;
- confidence taking the chart to rehearsal.

Collect comments by bar and track. Do not collapse every dimension into one
question.

## 10. Release Gates

For a style/instrument combination to be labeled supported:

- 100% schema/export fixtures pass;
- at least 99% hard-valid output across a frozen stress suite, or every failure
  is safely withheld;
- lock-preservation is 100% outside requested scope;
- no known critical range/polyphony/rights/security issue;
- human study sample and method are published internally;
- median playability/coherence meets the predeclared threshold;
- latency and cost meet the deployment budget;
- weaknesses are shown in the model/style card.

These are proposed gates. Reports must distinguish targets from measured facts.

