import json
import subprocess
from pathlib import Path

# Generated Node snippets intentionally mirror browser control flow.
# ruff: noqa: E501

WEB = Path(__file__).parents[2] / "web"


def _run_node(script: str) -> None:
    result = subprocess.run(
        ["node", "-e", script],
        cwd=WEB,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_editor_static_screen_exposes_reviewable_source_workflow_hooks():
    index = (WEB / "index.html").read_text(encoding="utf-8")
    script = (WEB / "editor.js").read_text(encoding="utf-8")
    styles = (WEB / "editor.css").read_text(encoding="utf-8")

    for label in (
        "song-title",
        "song-artist",
        "metadata-provider-id",
        "rights-attested",
        "chart-key",
        "bar-grid",
        "submit-source",
        "approve-source",
        "create-arrangement",
        "revision-history",
        "findings",
        "request-status",
    ):
        assert f'id="{label}"' in index
    assert "Idempotency-Key" in script
    assert "/v1/source-revisions/" in script
    assert "/approval" in script
    assert "arrangement-seeds" in script
    assert "metadataProviderId" in script
    assert "rightsAttested" in script
    assert "findings" in script
    assert "ticksPerQuarter" in script
    assert "source-locked" in styles
    assert "innerHTML" not in script


def test_editor_does_not_derive_music_from_metadata():
    script = (WEB / "editor.js").read_text(encoding="utf-8")
    assert "spotify" not in script.lower()
    assert "musicbrainz" not in script.lower()
    assert "fetchChords" not in script


def test_editor_static_screen_exposes_local_playback_review_controls():
    index = (WEB / "index.html").read_text(encoding="utf-8")
    script = (WEB / "editor.js").read_text(encoding="utf-8")

    for label in (
        "playback-panel",
        "play-preview",
        "stop-preview",
        "metronome",
        "count-in",
        "tempo-override",
        "loop-start",
        "loop-end",
        "track-mute-generated-bass",
        "track-solo-generated-bass",
    ):
        assert f'id="{label}"' in index
    assert "AudioContext" in script
    assert "createOscillator" in script
    assert "accepted candidate" in index
    assert "arrangement-versions/" in script
    assert "PLAYBACK_FIXTURE" not in script
    assert "state.playback.candidate" in script
    assert "candidate.tracks" in script
    assert "accepted" in script
    assert "metadata" in index.lower()
    assert "spotify" not in script.lower()
    assert "musicbrainz" not in script.lower()


def test_editor_blocks_preview_until_candidate_projection_is_accepted():
    script = (WEB / "editor.js").read_text(encoding="utf-8")
    assert "if (!state.playback.candidate?.accepted)" in script
    assert '"No accepted candidate is ready for playback."' in script


def test_scheduler_consumes_only_canonical_playback_plan_events():
    script = (WEB / "editor.js").read_text(encoding="utf-8")
    assert "/playback-plan" in script
    assert "function schedulePreviewLoop(context, plan)" in script
    assert "plan.events.forEach" in script
    assert "plan.loopStartTick" in script
    assert "plan.loopEndTick" in script
    assert "plan.tempoBpm" in script
    assert "schedulePreviewLoop(context, settings)" not in script
    assert "schedulePreviewLoop(context, plan)" in script
    assert "extractPreviewPitches" not in script
    assert "ticksPerMeasure" not in script
    assert 'Math.min(4, Number($("loop-start")' not in script
    assert 'Math.min(4, Number($("loop-end")' not in script


def test_playback_plan_guard_rejects_candidate_identity_or_lineage_mismatch():
    source_path = json.dumps(str(WEB / "editor.js"))
    _run_node(
        f"""
const fs = require('fs');
const source = fs.readFileSync({source_path}, 'utf8');
function extract(name) {{
  const start = source.indexOf(`function ${{name}}`);
  if (start < 0) throw new Error(`missing ${{name}}`);
  let depth = 0;
  let opened = false;
  for (let i = start; i < source.length; i += 1) {{
    if (source[i] === '{{') {{ depth += 1; opened = true; }}
    if (source[i] === '}}') {{ depth -= 1; if (opened && depth === 0) return source.slice(start, i + 1); }}
  }}
  throw new Error(`unterminated ${{name}}`);
}}
const playbackPlanMatchesCandidate = eval(`(${{extract('playbackPlanMatchesCandidate')}})`);
const candidate = {{ candidateId: 'candidate-1', accepted: true, rightsAttested: true,
  lineage: {{ seed: 7, engineVersion: 'engine', stylePackVersion: 'style', validatorVersion: 'validator', inputRevisionSet: ['source-1'], provenance: 'approved-source-locked-rules-baseline' }} }};
const plan = {{ candidateVersionId: 'candidate-1', lineage: {{ ...candidate.lineage }} }};
if (!playbackPlanMatchesCandidate(plan, candidate)) throw new Error('matching plan was rejected');
if (playbackPlanMatchesCandidate({{ ...plan, candidateVersionId: 'candidate-2' }}, candidate)) throw new Error('candidate identity mismatch accepted');
if (playbackPlanMatchesCandidate({{ ...plan, lineage: {{ ...plan.lineage, seed: 8 }} }}, candidate)) throw new Error('lineage mismatch accepted');
"""
    )


def test_scheduler_executes_returned_plan_events_and_stops_timer_recursion():
    source_path = json.dumps(str(WEB / "editor.js"))
    _run_node(
        f"""
const fs = require('fs');
const source = fs.readFileSync({source_path}, 'utf8');
function extract(name) {{
  const start = source.indexOf(`function ${{name}}`);
  if (start < 0) throw new Error(`missing ${{name}}`);
  let depth = 0;
  let opened = false;
  for (let i = start; i < source.length; i += 1) {{
    if (source[i] === '{{') {{ depth += 1; opened = true; }}
    if (source[i] === '}}') {{ depth -= 1; if (opened && depth === 0) return source.slice(start, i + 1); }}
  }}
  throw new Error(`unterminated ${{name}}`);
}}
const midiFrequency = (midi) => 440 * 2 ** ((midi - 69) / 12);
const previewVoice = eval(`(${{extract('previewVoice')}})`);
const schedulePlaybackPlan = eval(`(${{extract('schedulePlaybackPlan')}})`);
const scheduled = [];
const timers = [];
let playing = true;
const context = {{ currentTime: 10 }};
const plan = {{ tempoBpm: 120, loopStartTick: 960, loopEndTick: 7680, events: [
  {{ eventId: 'returned-1', kind: 'NOTE', startTick: 960, durationTicks: 480, pitches: [60] }},
  {{ eventId: 'returned-2', kind: 'CLICK', startTick: 7200, durationTicks: 120, pitches: [84] }}
] }};
const scheduleTone = (_context, frequency, start, duration) => scheduled.push({{ frequency, start, duration }});
const setTimer = (callback, delay) => {{ timers.push({{ callback, delay }}); return timers.length; }};
schedulePlaybackPlan(context, plan, scheduleTone, setTimer, () => playing);
if (scheduled.length !== 2) throw new Error(`expected two returned events, got ${{scheduled.length}}`);
    if (timers.length !== 1 || Math.round(timers[0].delay) !== 3580) throw new Error('loop tick/tempo delay was not honored');
timers[0].callback();
if (timers.length !== 2) throw new Error('playing callback did not recurse');
playing = false;
timers[1].callback();
if (timers.length !== 2) throw new Error('stopped callback scheduled another timer');
"""
    )


def test_playback_settings_reads_rendered_data_track_controls():
    source_path = json.dumps(str(WEB / "editor.js"))
    _run_node(
        f"""
const fs = require('fs');
const source = fs.readFileSync({source_path}, 'utf8');
function extract(name) {{
  const start = source.indexOf(`function ${{name}}`);
  if (start < 0) throw new Error(`missing ${{name}}`);
  let depth = 0;
  let opened = false;
  for (let i = start; i < source.length; i += 1) {{
    if (source[i] === '{{') {{ depth += 1; opened = true; }}
    if (source[i] === '}}') {{ depth -= 1; if (opened && depth === 0) return source.slice(start, i + 1); }}
  }}
  throw new Error(`unterminated ${{name}}`);
}}
const state = {{ playback: {{ candidate: {{ candidate: {{
  tracks: [
    {{ id: 'generated_drums' }}, {{ id: 'generated_bass' }},
    {{ id: 'generated_guitar' }}, {{ id: 'generated_keys' }}
  ],
  measures: [{{ id: 'measure_001' }}, {{ id: 'measure_002' }}]
}} }} }} }};
const controls = [
  {{ checked: true, dataset: {{ trackId: 'generated_bass', mode: 'mute' }} }},
  {{ checked: true, dataset: {{ trackId: 'generated_drums', mode: 'solo' }} }},
  {{ checked: false, dataset: {{ trackId: 'generated_keys', mode: 'solo' }} }}
];
const fixed = {{
  'loop-start': {{ value: '1' }}, 'loop-end': {{ value: '2' }},
  metronome: {{ checked: false }}, 'count-in': {{ value: '0' }},
  'tempo-override': {{ value: '130' }}
}};
const $ = (id) => fixed[id];
const document = {{ querySelectorAll: (selector) => controls.filter((control) =>
  control.checked && selector.includes(`data-mode="${{control.dataset.mode}}"`)
) }};
const playbackSettings = eval(`(${{extract('playbackSettings')}})`);
const settings = playbackSettings();
if (JSON.stringify(settings.mutedTrackIds) !== JSON.stringify(['generated_bass']))
  throw new Error(`mute selection was lost: ${{JSON.stringify(settings.mutedTrackIds)}}`);
if (JSON.stringify(settings.soloTrackIds) !== JSON.stringify(['generated_drums']))
  throw new Error(`solo selection was lost: ${{JSON.stringify(settings.soloTrackIds)}}`);
"""
    )


def test_playback_control_change_replans_only_while_playing():
    source_path = json.dumps(str(WEB / "editor.js"))
    _run_node(
        f"""
const fs = require('fs');
const source = fs.readFileSync({source_path}, 'utf8');
function extract(name) {{
  const start = source.indexOf(`function ${{name}}`);
  if (start < 0) throw new Error(`missing ${{name}}`);
  let depth = 0;
  let opened = false;
  for (let i = start; i < source.length; i += 1) {{
    if (source[i] === '{{') {{ depth += 1; opened = true; }}
    if (source[i] === '}}') {{ depth -= 1; if (opened && depth === 0) return source.slice(start, i + 1); }}
  }}
  throw new Error(`unterminated ${{name}}`);
}}
const state = {{ playback: {{ intentToPlay: false }} }};
const refreshPlayingPreview = eval(`(async ${{extract('refreshPlayingPreview')}})`);
let calls = 0;
const replay = async () => {{ calls += 1; }};
(async () => {{
  if (await refreshPlayingPreview(replay)) throw new Error('stopped preview was replanned');
  if (calls !== 0) throw new Error('stopped preview invoked playback');
  state.playback.intentToPlay = true;
  if (!(await refreshPlayingPreview(replay))) throw new Error('playing preview was not replanned');
  if (calls !== 1) throw new Error(`expected one replan, got ${{calls}}`);
}})().catch((error) => {{ console.error(error); process.exit(1); }});
"""
    )


def test_playback_session_cancellation_stops_sources_timers_and_stale_requests():
    source_path = json.dumps(str(WEB / "editor.js"))
    _run_node(
        f"""
const fs = require('fs');
const source = fs.readFileSync({source_path}, 'utf8');
function extract(name) {{
  const start = source.indexOf(`function ${{name}}`);
  if (start < 0) throw new Error(`missing ${{name}}`);
  let depth = 0;
  let opened = false;
  for (let i = start; i < source.length; i += 1) {{
    if (source[i] === '{{') {{ depth += 1; opened = true; }}
    if (source[i] === '}}') {{ depth -= 1; if (opened && depth === 0) return source.slice(start, i + 1); }}
  }}
  throw new Error(`unterminated ${{name}}`);
}}
let aborted = 0;
let stopped = 0;
const cleared = [];
const state = {{ playback: {{
  sessionId: 4,
  playing: true,
  intentToPlay: true,
  requestController: {{ abort: () => {{ aborted += 1; }} }},
  timers: new Set([11, 12]),
  nodes: [{{ stop: () => {{ stopped += 1; }} }}, {{ stop: () => {{ stopped += 1; }} }}],
}} }};
const window = {{ clearTimeout: (timer) => cleared.push(timer) }};
const cancelActivePlayback = eval(`(${{extract('cancelActivePlayback')}})`);
const playbackSessionIsCurrent = eval(`(${{extract('playbackSessionIsCurrent')}})`);
if (!playbackSessionIsCurrent(4)) throw new Error('active session was rejected');
cancelActivePlayback();
if (state.playback.sessionId !== 5) throw new Error('session generation was not advanced');
if (aborted !== 1) throw new Error('in-flight request was not aborted');
if (stopped !== 2) throw new Error('scheduled sources were not stopped');
if (cleared.length !== 2) throw new Error('all loop timers were not cleared');
if (state.playback.playing) throw new Error('playing state survived cancellation');
if (!state.playback.intentToPlay) throw new Error('internal cancellation lost replay intent');
if (playbackSessionIsCurrent(4)) throw new Error('stale session remained current');
"""
    )


def test_preview_request_is_abortable_and_rejects_stale_completion():
    script = (WEB / "editor.js").read_text(encoding="utf-8")
    assert "new AbortController()" in script
    assert "signal: requestController.signal" in script
    assert "if (!playbackSessionIsCurrent(sessionId)) return false;" in script
    assert 'if (error.name === "AbortError") return;' in script


def test_preview_uses_local_sampled_acoustic_players_and_cancelable_envelopes():
    script = (WEB / "editor.js").read_text(encoding="utf-8")
    assert 'from "./vendor/webaudiofontplayer-1.0.3/index.mjs"' in script
    for preset in ("0000_FluidR3", "0252_FluidR3", "0330_FluidR3", "12830_FluidR3"):
        assert preset in script
        assert (WEB / "assets" / "soundfonts" / f"{preset}.json").is_file()
    assert "WebAudioFontPlayer.load" in script
    assert "queueWaveTable" in script
    assert "envelope.cancel(true)" in script
    assert (WEB / "vendor" / "webaudiofontplayer-1.0.3" / "LICENSE").is_file()
    package = json.loads(
        (WEB / "vendor" / "webaudiofontplayer-1.0.3" / "package.json").read_text(
            encoding="utf-8"
        )
    )
    assert package["name"] == "webaudiofontplayer"
    assert package["version"] == "1.0.3"
    assert package["license"] == "MIT"
    assert (WEB / "vendor" / "webaudiofontplayer-1.0.3" / "PROVENANCE.md").is_file()
    assert (WEB / "assets" / "soundfonts" / "ATTRIBUTION.md").is_file()


def test_scheduler_preserves_track_identity_velocity_and_distinct_sample_roles():
    source_path = json.dumps(str(WEB / "editor.js"))
    _run_node(
        f"""
const fs = require('fs');
const source = fs.readFileSync({source_path}, 'utf8');
function extract(name) {{
  const start = source.indexOf(`function ${{name}}`);
  if (start < 0) throw new Error(`missing ${{name}}`);
  let depth = 0;
  let opened = false;
  for (let i = start; i < source.length; i += 1) {{
    if (source[i] === '{{') {{ depth += 1; opened = true; }}
    if (source[i] === '}}') {{ depth -= 1; if (opened && depth === 0) return source.slice(start, i + 1); }}
  }}
  throw new Error(`unterminated ${{name}}`);
}}
const midiFrequency = eval(`(${{extract('midiFrequency')}})`);
const previewVoice = eval(`(${{extract('previewVoice')}})`);
const schedulePlaybackPlan = eval(`(${{extract('schedulePlaybackPlan')}})`);
const scheduled = [];
const events = [
  {{ eventId: 'drum', trackId: 'generated_drums', kind: 'DRUM_HIT', startTick: 0, durationTicks: 240, pitches: [42], velocity: 92 }},
  {{ eventId: 'bass', trackId: 'generated_bass', kind: 'NOTE', startTick: 0, durationTicks: 960, pitches: [36], velocity: 84 }},
  {{ eventId: 'guitar', trackId: 'generated_guitar', kind: 'CHORD', startTick: 0, durationTicks: 960, pitches: [60], velocity: 76 }},
  {{ eventId: 'keys', trackId: 'generated_keys', kind: 'CHORD', startTick: 0, durationTicks: 960, pitches: [64], velocity: 72 }}
];
const plan = {{ tempoBpm: 120, loopStartTick: 0, loopEndTick: 3840, events }};
schedulePlaybackPlan(
  {{ currentTime: 0 }}, plan,
  (_context, frequency, _start, _duration, gain, voice) => scheduled.push({{ frequency, gain, voice }}),
  () => 1, () => false
);
if (scheduled.length !== 4) throw new Error(`expected four scheduled voices, got ${{scheduled.length}}`);
const byTrack = Object.fromEntries(scheduled.map((item) => [item.voice.trackId, item]));
for (const event of events) {{
  if (!byTrack[event.trackId]) throw new Error(`missing scheduled ${{event.trackId}} voice`);
  if (byTrack[event.trackId].voice.velocity !== event.velocity) throw new Error(`lost ${{event.trackId}} velocity`);
}}
if (JSON.stringify([...new Set(scheduled.map((item) => item.voice.sampleRole))].sort()) !==
    JSON.stringify(['bass', 'drums', 'guitar', 'keys']))
  throw new Error('sample players do not distinguish all generated instrument roles');
if (byTrack.generated_drums.frequency === midiFrequency(42))
  throw new Error('drum kit number was incorrectly rendered as a pitched MIDI note');
"""
    )


def test_playback_controls_cover_each_generated_track():
    index = (WEB / "index.html").read_text(encoding="utf-8")
    for track_id in ("generated-drums", "generated-bass", "generated-guitar", "generated-keys"):
        assert f'id="track-mute-{track_id}"' in index
        assert f'id="track-solo-{track_id}"' in index
