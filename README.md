# BandForge

BandForge is a local, contract-first arrangement workspace for turning a
user-authored or licensed chord chart into a reviewable four-piece rehearsal
packet. It keeps a versioned `ArrangementDocument` as the canonical musical
state, then produces deterministic drums, bass, guitar, and keys candidates,
validates them, previews them in the browser, and exports MIDI, MusicXML, and
a printable packet.

It is a portfolio MVP, not a copyrighted chart catalog, a song transcriber, or
a claim that the generated arrangement is professionally playable. A title or
streaming metadata can be metadata only; it can never provide chords or notes.

## What is implemented

- Structured-source editor with invalid-bar findings, immutable corrected
  revisions, explicit approval, source locking, provenance, and 960 TPQ.
- Deterministic four-piece acoustic-pop baseline with hard schema, timing,
  range, polyphony, rights, and source-lock validation.
- Candidate playback with mute, solo, loop, metronome, count-in, tempo
  override, local attributed samples, and cancellation-safe replay.
- Immutable `SAFE` scoped regeneration that preserves content and IDs outside
  the requested track/measure scope.
- Deterministic MIDI type 1, MusicXML, and player-packet ZIP exports.

## Honest limits

- The only implemented arrangement style is a deterministic acoustic-pop
  baseline. EDM, human-quality ranking, professional mix quality, and learned
  generation are not implemented.
- Validators establish structural safety; they do not prove musical quality or
  player comfort. Rehearse generated parts before an event.
- PDF engraving, broad file imports, hosted deployment/authentication, and
  model training are intentionally outside this MVP.

## Quick start

Requires Python 3.11+ and Node.js (Node is used only for JavaScript syntax and
the isolated browser check).

```powershell
git clone https://github.com/nguyenthevietquang07/band-forge.git
cd band-forge

python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"

# Terminal 1: API
python -m uvicorn bandforge_api.main:app --app-dir src --host 127.0.0.1 --port 8011

# Terminal 2: editor
python -m http.server 8012 --bind 127.0.0.1 --directory web
```

Open <http://127.0.0.1:8012>. Enter only a chart you authored or are licensed
to use, attest to rights, resolve any blocked bar, approve it, create a source
lock, and then preview or export an accepted candidate.

## Runnable original-content demo

The committed demo fixtures use the original, title-free chord loop
`Am | F | C | G`; they contain no commercial-song lyrics, notation, or audio.
The editor demo starts and stops its own local API and static server:

```powershell
python scripts/run_cycle4_demo.py
python scripts/run_cycle6_demo.py
python scripts/run_cycle7_demo.py
python scripts/run_cycle8_demo.py
python scripts/run_cycle9_demo.py
python scripts/run_cycle10_demo.py
```

The Cycle 4 demo exercises the editor's real HTTP flow. Cycles 6–10 exercise
the deterministic generator, validation, MIDI, scoped regeneration, MusicXML,
player packet, and playback-plan boundaries. Generated artifacts and evidence
are written under `reports/`.

## Verify

```powershell
python -m pytest -q
python -m ruff check src tests scripts
python -m openapi_spec_validator contracts/openapi.yaml
node --check web/editor.js
```

The latest local closure recorded 97 passing tests plus the checks above. See
[the demo gate](docs/13-cycle-demo-gate.md) and
[the final review](reports/final-mvp-review.md) for evidence and explicit
claim boundaries.

## Browser verification status

The original MVP gate used HTTP/domain evidence because browser automation was
unavailable in that earlier environment. A later isolated Chrome verification
of the local screen covered all four generated roles, each mute/solo state,
expanded drum events, stop/replay cancellation, and a clean console. The two
facts refer to different dates and scopes: the post-MVP browser evidence fixes
playback behavior; it does not retroactively claim a human listening-quality
study or a professional-arrangement result. See
[the reconciliation note](docs/13-cycle-demo-gate.md#browser-evidence-reconciliation)
and [the repair report](reports/acoustic-preview-overlap-fix.md).

## Rights and third-party notices

- Keep user-supplied event charts, lyrics, and performance packets local unless
  you have publication rights. The local ignore rules intentionally exclude
  the user-supplied event demonstration from Git.
- Browser preview presets are a curated FluidR3 subset under CC BY 3.0; see
  [sample attribution](web/assets/soundfonts/ATTRIBUTION.md).
- The bundled `webaudiofontplayer@1.0.3` runtime is MIT-licensed; see its
  [provenance and license](web/vendor/webaudiofontplayer-1.0.3/PROVENANCE.md).
- This repository intentionally does not grant a blanket license for the
  project source until the owner selects one.

## Architecture

`web/` is the dependency-free browser editor. `src/` holds the FastAPI surface,
domain logic, contracts, deterministic generator, validators, and exporters.
The design dossier in `docs/` explains the versioned canonical document,
provenance/rights boundary, and deliberately deferred model-training roadmap.

For publication scope and excluded private material, see
[PUBLISHING.md](PUBLISHING.md).
