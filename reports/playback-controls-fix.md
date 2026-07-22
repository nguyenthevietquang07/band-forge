# BandForge playback control defect repair

Date: 2026-07-22

## User-observed failure

At `http://127.0.0.1:8012/`, mute and solo controls had no effect and the
four-piece preview sounded like only the keys were active.

## Root causes

1. Candidate track IDs use underscores (`generated_bass`), while the rendered
   checkbox element IDs use hyphens. The browser constructed an element ID from
   the canonical track ID, failed to find the checkbox, and sent empty
   `mutedTrackIds` and `soloTrackIds` arrays.
2. The Web Audio scheduler discarded event track identity and velocity. Every
   pitch used the same low-gain sine oscillator; low drum trigger frequencies
   and bass fundamentals were weak while the keys' simultaneous chord tones
   dominated.

## Repair

- Playback settings now read canonical IDs from checked `data-track-id`
  controls and validate them against candidate tracks.
- Preview scheduling preserves track identity and velocity.
- Drums, bass, guitar, keys, and metronome clicks receive distinct bounded
  oscillator profiles. This is a functional local preview, not a claim of
  realistic sampled-instrument audio.
- Changing mute or solo while playback is active automatically requests and
  schedules the updated canonical plan. The preview restarts at the selected
  loop boundary; seamless mid-beat gain automation is not claimed.

## TDD evidence

- Red: `python -m pytest tests/web/test_editor_static.py -q` produced 2 failed,
  8 passed. The failures proved mute selection was lost and `previewVoice` did
  not exist.
- Review red: after the initial repair, a new live-change regression produced
  1 failed, 10 passed because `refreshPlayingPreview` did not exist.
- Focused green: the same command now produces 11 passed.

## Live browser evidence

Command (against isolated Chrome DevTools on the running local app):

`$env:BANDFORGE_CHROME_DEBUG_PORT='9224'; node scripts/run_playback_browser_check.mjs`

Result: exit 0. The browser created and approved a source, created a locked
seed, loaded an accepted candidate, reached Web Audio `Playing` state, and
verified:

- together: drums 16 events, bass 4, guitar 4, keys 4;
- while already playing, muting each generated track removed only that track;
- while already playing, soloing each generated track returned only that track;
- isolated oscillator starts proved drums use sine/sawtooth/square voices, bass
  uses triangle, guitar uses sawtooth, and keys use sine;
- the canonical source-guide track emitted zero audio events;
- all playback-plan responses were HTTP 200;
- browser console errors/warnings: 0.

Artifacts:

- `reports/playback-controls-fixed-browser.json`
- `reports/playback-controls-fixed-browser.png`

## Honest boundary

The repair makes controls effective and instrument roles distinguishable in
the local Web Audio preview. It does not provide professional instrument
samples, prove subjective musical quality, or fix the separately identified
MusicXML/MuseScore instrument-mapping defects.
