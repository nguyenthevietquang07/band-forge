# Post-MVP acoustic preview and overlap repair

Date: 2026-07-22

Status: implemented and verified for the bounded local browser-preview defect.

## Scope and exclusions

This repair replaces pitched-track oscillator previews with local sampled
acoustic instruments, expands the deterministic drum groove beyond kick/snare/
closed hat, and makes Play/Stop/replay cancellation session-safe. The canonical
playback plan, ArrangementDocument, source locks, lineage, rights attestation,
and deterministic generator remain authoritative.

It does not train a model, infer music from song metadata, prove professional
arrangement quality, perform a human listening panel, or repair every external
MuseScore sound-bank choice. Those are separate concerns.

## Root causes

1. Generated piano, guitar, bass, and drums were rendered with simple Web Audio
   oscillators, so their timbre was intentionally synthetic.
2. The generator emitted only kick, snare, and closed-hat events.
3. An older playback-plan request could finish after Stop or a newer Play and
   schedule stale events. Recursive loop timers were not all retained for
   cancellation.

## Implementation

- Vendored pinned MIT `webaudiofontplayer@1.0.3`; package metadata, archive and
  runtime hashes, and the upstream stale `Version: 1.0.2` bundle-banner note are
  recorded in `web/vendor/webaudiofontplayer-1.0.3/PROVENANCE.md`.
- Self-hosted four CC BY 3.0 FluidR3 presets: acoustic grand piano,
  steel-string guitar, fingered bass, and standard drum kit. Attribution and
  conversion provenance are in `web/assets/soundfonts/ATTRIBUTION.md`.
- Preview scheduling now uses cancelable sample envelopes for all four generated
  roles; only metronome/count-in clicks retain a short synthesized voice.
- Added monotonic playback session IDs, an abortable plan request, stale-result
  rejection, complete timer tracking, source-envelope cancellation, and
  separate user playback intent from active scheduling state.
- The deterministic drum pattern now uses eighth-note grooves, open-hat accents,
  first-bar crash accents, and a fourth-bar low/mid/high-tom fill. Playback maps
  the schema's supported kit pieces to General MIDI percussion pitches.

## TDD evidence

Red run before implementation:

```text
4 failed, 30 passed
```

The failures covered stale session cancellation, abortable requests, live
replanning intent, and the missing expanded drum vocabulary. The sampler test
then failed before local runtime/assets were integrated.

Focused green run:

```text
35 passed in 2.35s
node --check web/editor.js: passed
```

Final full verification after the implementation code:

```text
97 passed in 11.46s
OpenAPI validation: passed
Cycle 6 generator demo: passed
Cycle 10 playback demo: passed
```

Ruff initially caught one overlong test line; it was corrected before final
closure and rerun in the final gate.

## Real Chrome evidence

The isolated Chrome/CDP demo ran against the live local screen on
`http://127.0.0.1:8012/` and the restarted API on port 8011. It observed:

- all four generated roles together;
- four individual mute cases and four individual solo cases;
- zero pitched-track oscillator starts;
- local `AudioBufferSourceNode` starts matching every returned non-click pitch;
- 33 generated drum events in the four-bar verification candidate;
- Stop canceling 12 scheduled sample sources in the final solo case;
- rapid Play -> Stop -> Play producing exactly 12 final sample starts for the
  12 returned pitches, rather than stacked duplicate playback;
- zero browser console errors or warnings.

Evidence: `reports/playback-controls-fixed-browser.json` and
`reports/playback-controls-fixed-browser.png`.

## Pinned assets

| File | Bytes | SHA-256 |
|---|---:|---|
| `0000_FluidR3.json` | 2,305,137 | `3335b20071972832bcc46bafb7c42cea6ef81966d92a231bcbc55b18fcde88a9` |
| `0252_FluidR3.json` | 475,895 | `65e14fe6e4b3f93d75cac440ab90a138a0127c54d3a612ca57e211a2b69f6ba4` |
| `0330_FluidR3.json` | 533,727 | `2a2e7521e1f05413dbb394fa4facd6b7b7410cb09cb3a78731a428d2478e40ce` |
| `12830_FluidR3.json` | 2,302,364 | `e5e5a01da62a4aa46123e43bcdd5c5e5327d1da0f7e8944a920c3e08bd404f1d` |

Research basis: the current WebAudioFontPlayer documentation describes decoded
sample presets, `queueWaveTable`, per-envelope cancellation, and queue
cancellation; the FluidR3 pre-rendered source identifies CC BY 3.0; MDN defines
scheduled-source `stop()` semantics and `AbortController` cancellation.

## Honest remaining gaps

Sampled timbre is materially different from oscillator synthesis, but this is
not evidence that the generated arrangement sounds like a professional band.
The current generator still uses simple whole-bar bass/chord events and one
bounded acoustic-pop rule pack. Guitar strum timing, bass articulation,
section-aware dynamics, musician evaluation, mix balancing, and broader style
variation require separate evidence-backed work. Model training is not needed
to validate this repair and remains outside the approved MVP boundary.
