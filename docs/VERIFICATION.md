# Verification

## Current result

The latest local closure recorded **97 passing tests** plus Ruff, semantic
OpenAPI validation, JavaScript syntax validation, deterministic export demos,
and an isolated browser playback check.

## Reproduce

```powershell
python -m pytest -q
python -m ruff check src tests scripts
python -m openapi_spec_validator contracts/openapi.yaml
node --check web/editor.js

python scripts/run_cycle4_demo.py
python scripts/run_cycle6_demo.py
python scripts/run_cycle8_demo.py
python scripts/run_cycle9_demo.py
python scripts/run_cycle10_demo.py
```

## What the evidence covers

- Structured source review, blocking invalid bars, immutable correction,
  approval, and source locking through real local HTTP calls.
- Deterministic candidate replay, source-harmony preservation, complete
  lineage, and hard validation across four generated instruments.
- Type-1 MIDI, MusicXML, and player-packet structural validation.
- `SAFE` scoped regeneration with unchanged outside-scope content hashes.
- Playback plan controls and the browser repair for mute/solo, role-aware
  sample scheduling, and stop/replay cancellation.

## Boundaries

The tests and demos establish structural correctness and local behavior. They
do not establish professional musical quality, human playability, production
availability, or a trained-model result. The browser screenshot and repair
case study are local verification evidence, not a user-adoption claim.
