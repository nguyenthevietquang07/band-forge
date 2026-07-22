# BandForge

BandForge is a contract-first local application that turns a user-authored or
licensed chord chart into a validated four-piece rehearsal packet. It uses a
versioned canonical `ArrangementDocument`, deterministic candidate generation,
hard musical constraints, browser playback, and MIDI/MusicXML export.

![BandForge source editor and playback controls](reports/playback-controls-fixed-browser.png)

## Why it is interesting

- **Workflow integrity:** immutable source revisions, explicit rights
  attestation, approval, source locks, and complete candidate lineage.
- **Deterministic music systems:** seeded drums, bass, guitar, and keys
  generation with schema, timing, range, polyphony, and source-lock gates.
- **Interoperability:** Standard MIDI type 1, MusicXML, and a manifest-backed
  player-packet ZIP derive from the canonical document.
- **Failure-aware browser playback:** mute/solo, loop, metronome, count-in,
  tempo override, role-aware samples, and cancellation-safe replay.

## Run it locally

Requires Python 3.11+ and Node.js.

```powershell
git clone https://github.com/nguyenthevietquang07/band-forge.git
cd band-forge
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Terminal 1
python -m uvicorn bandforge_api.main:app --app-dir src --host 127.0.0.1 --port 8011

# Terminal 2
python -m http.server 8012 --bind 127.0.0.1 --directory web
```

Open <http://127.0.0.1:8012>. Enter only musical material you authored or are
licensed to use; song metadata is never used as a source of chords or notes.

## Reproduce the demo and checks

The committed demo fixture is the original, title-free progression
`Am | F | C | G`.

```powershell
python scripts/run_cycle4_demo.py
python scripts/run_cycle6_demo.py
python scripts/run_cycle8_demo.py
python scripts/run_cycle9_demo.py
python scripts/run_cycle10_demo.py

python -m pytest -q
python -m ruff check src tests scripts
python -m openapi_spec_validator contracts/openapi.yaml
node --check web/editor.js
```

Current local verification: **97 tests passed**, alongside lint, semantic
OpenAPI validation, JavaScript syntax validation, HTTP/domain demos, and an
isolated browser playback check. Details: [architecture](docs/ARCHITECTURE.md),
[verification](docs/VERIFICATION.md), and the
[playback repair case study](reports/acoustic-preview-overlap-fix.md).

## Scope

This is a deterministic acoustic-pop MVP. It does not claim professional
arrangement quality, a trained music model, a hosted product, or a copyrighted
chart catalog. The local FluidR3 preview presets are attributed under CC BY 3.0
in [ATTRIBUTION.md](web/assets/soundfonts/ATTRIBUTION.md); the bundled playback
runtime is MIT-licensed with recorded
[provenance](web/vendor/webaudiofontplayer-1.0.3/PROVENANCE.md).
