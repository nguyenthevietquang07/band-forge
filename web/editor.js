import WebAudioFontPlayer from "./vendor/webaudiofontplayer-1.0.3/index.mjs";

const SAMPLE_PRESETS = {
  keys: "./assets/soundfonts/0000_FluidR3.json",
  guitar: "./assets/soundfonts/0252_FluidR3.json",
  bass: "./assets/soundfonts/0330_FluidR3.json",
  drums: "./assets/soundfonts/12830_FluidR3.json",
};

const state = {
  apiBase: "http://127.0.0.1:8011",
  songId: null,
  currentRevision: null,
  revisions: [],
  arrangement: null,
  ticksPerQuarter: 960,
  bars: ["Am", "F", "Cmaj9#11", "G"],
  playback: {
    context: null,
    nodes: [],
    timers: new Set(),
    playing: false,
    intentToPlay: false,
    sessionId: 0,
    requestController: null,
    samplePlayers: null,
    sampleLoadPromise: null,
    candidate: null,
    plan: null,
  },
};

const $ = (id) => document.getElementById(id);
const apiKey = (prefix) => `${prefix}-${crypto.randomUUID()}`;

function setStatus(message, error = false) {
  const element = $("request-status");
  element.textContent = message;
  element.classList.toggle("error", error);
}

async function request(path, options = {}) {
  const response = await fetch(`${state.apiBase.replace(/\/$/, "")}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const requestId = response.headers.get("X-Request-Id");
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.error || {};
    const suffix = detail.requestId || requestId ? ` · request ${detail.requestId || requestId}` : "";
    throw new Error(`${detail.code || `HTTP ${response.status}`}: ${detail.message || "Request failed"}${suffix}`);
  }
  return payload;
}

function renderBars(focusOrdinal = null) {
  const grid = $("bar-grid");
  grid.replaceChildren();
  state.bars.forEach((chord, index) => {
    const ordinal = index + 1;
    const wrapper = document.createElement("div");
    wrapper.className = "bar";
    wrapper.dataset.barOrdinal = ordinal;
    const label = document.createElement("label");
    label.textContent = `Bar ${ordinal}`;
    label.htmlFor = `bar-${ordinal}`;
    const input = document.createElement("input");
    input.id = `bar-${ordinal}`;
    input.value = chord;
    input.maxLength = 64;
    input.autocomplete = "off";
    input.dataset.barOrdinal = ordinal;
    input.addEventListener("input", (event) => { state.bars[index] = event.target.value; wrapper.classList.remove("has-finding"); input.removeAttribute("aria-invalid"); });
    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight" && state.bars[index + 1] !== undefined) $(`bar-${ordinal + 1}`).focus();
      if (event.key === "ArrowLeft" && index > 0) $(`bar-${ordinal - 1}`).focus();
    });
    wrapper.append(label, input);
    grid.append(wrapper);
  });
  if (focusOrdinal) $(`bar-${focusOrdinal}`)?.focus();
}

function renderHistory() {
  const history = $("revision-history");
  history.replaceChildren();
  if (!state.revisions.length) { const empty = document.createElement("li"); empty.className = "empty"; empty.textContent = "No source revision yet."; history.append(empty); return; }
  state.revisions.forEach((revision) => {
    const item = document.createElement("li");
    item.className = revision.id === state.currentRevision?.id ? "current" : "";
    item.textContent = `${revision.id.slice(-10)} · ${revision.status} · ${revision.findings.length ? `${revision.findings.length} finding(s)` : "clean"}`;
    item.title = revision.id;
    item.addEventListener("click", () => { state.currentRevision = revision; state.bars = [...revision.content.bars]; $("chart-key").value = revision.content.key; renderBars(); renderReview(); });
    history.append(item);
  });
}

function renderReview() {
  const revision = state.currentRevision;
  $("review-panel").hidden = !revision;
  if (!revision) return;
  $("revision-id").textContent = revision.id;
  $("review-status").textContent = revision.status === "APPROVED" ? "Approved" : revision.findings.length ? "Needs review" : "Ready to approve";
  $("review-status").className = `pill ${revision.status === "APPROVED" ? "approved" : "review"}`;
  const findings = $("findings"); findings.replaceChildren();
  revision.findings.forEach((finding) => {
    const item = document.createElement("div"); item.className = "finding";
    const button = document.createElement("button"); button.type = "button"; button.dataset.barOrdinal = finding.barOrdinal;
    const heading = document.createElement("strong"); heading.textContent = `${finding.code} · Bar ${finding.barOrdinal}`;
    button.append(heading, document.createTextNode(finding.message));
    button.addEventListener("click", () => renderBars(finding.barOrdinal)); item.append(button); findings.append(item);
    $(`bar-${finding.barOrdinal}`)?.setAttribute("aria-invalid", "true"); $(`bar-${finding.barOrdinal}`)?.closest(".bar")?.classList.add("has-finding");
  });
  if (!revision.findings.length) { const clean = document.createElement("p"); clean.className = "helper"; clean.textContent = "No blocking findings. Confirm the rights attestation, then approve this immutable revision."; findings.append(clean); }
  $("approve-source").disabled = Boolean(revision.findings.length) || revision.status === "APPROVED";
  $("create-arrangement").disabled = revision.status !== "APPROVED";
  renderHistory();
}

async function ensureSong() {
  if (state.songId) return state.songId;
  const song = await request("/v1/songs", { method: "POST", headers: { "Idempotency-Key": apiKey("editor-song") }, body: JSON.stringify({ title: $("song-title").value.trim(), artist: $("song-artist").value.trim() || null, metadataProviderId: $("metadata-provider-id").value.trim() || null }) });
  state.songId = song.id; $("song-id").textContent = song.id; return song.id;
}

async function submitSource() {
  if (!$("song-title").value.trim()) throw new Error("INVALID_REQUEST: Add a song title before reviewing the source.");
  if (!$("rights-attested").checked) throw new Error("RIGHTS_ATTESTATION_REQUIRED: Confirm you own or are licensed to use this source.");
  const songId = await ensureSong();
  const revision = await request(`/v1/songs/${songId}/sources`, { method: "POST", headers: { "Idempotency-Key": apiKey("editor-source") }, body: JSON.stringify({ sourceType: "STRUCTURED", rightsAttested: true, content: { key: $("chart-key").value, bars: state.bars } }) });
  state.currentRevision = revision; state.revisions.push(revision); $("source-status").textContent = revision.findings.length ? "Needs review" : "Ready to approve"; renderReview(); const firstFinding = revision.findings[0]; renderBars(firstFinding?.barOrdinal || null); setStatus(`Revision ${revision.id} created · ${revision.findings.length ? "resolve the highlighted bar" : "ready for approval"}`);
}

async function approveSource() {
  const revision = await request(`/v1/source-revisions/${state.currentRevision.id}/approval`, { method: "POST", headers: { "Idempotency-Key": apiKey("editor-approval") }, body: JSON.stringify({ rightsAttested: true }) });
  state.currentRevision = revision; state.revisions[state.revisions.findIndex((item) => item.id === revision.id)] = revision; $("source-status").textContent = "Approved"; renderReview(); setStatus(`Revision ${revision.id} approved · source is ready to seed`);
}

async function createLockedSeed() {
  const result = await request(`/v1/source-revisions/${state.currentRevision.id}/arrangement-seeds`, { method: "POST" });
  state.arrangement = result.document; $("locked-card").hidden = false; $("arrangement-id").textContent = result.document.arrangementId; $("version-id").textContent = result.document.versionId; $("lock-summary").textContent = `${result.document.locks?.length || 0} source lock(s)`; setStatus(`Locked seed ${result.document.versionId} created from approved source`);
  await loadCandidate(result.id);
}

async function loadCandidate(versionId) {
  const projection = await request(`/v1/arrangement-versions/${versionId}/candidates`, {
    method: "POST",
    body: JSON.stringify({ seed: 0, tempoBpm: Number($("tempo-override").value) || 104 }),
  });
  state.playback.candidate = projection;
  const measureCount = projection.candidate.measures.length;
  $("loop-start").max = String(measureCount);
  $("loop-end").max = String(measureCount);
  $("loop-end").value = String(measureCount);
  $("candidate-id").textContent = projection.candidateId;
  $("candidate-validator").textContent = projection.validatorVersion;
  $("candidate-rights").textContent = projection.rightsAttested ? "Attested" : "Blocked";
  $("play-preview").disabled = !projection.accepted || !projection.rightsAttested;
  $("playback-status").textContent = projection.accepted ? "Accepted candidate ready." : "Waiting for an accepted candidate.";
  setStatus(`Accepted candidate ${projection.candidateId} ready for local playback`);
}

function playbackSettings() {
  const candidate = state.playback.candidate?.candidate;
  const tracks = candidate ? candidate.tracks || [] : [];
  const knownTrackIds = new Set(tracks.map((track) => track.id));
  const selectedTrackIds = (mode) => Array.from(
    document.querySelectorAll(`[data-mode="${mode}"]:checked`),
  ).map((control) => control.dataset.trackId).filter((trackId) => knownTrackIds.has(trackId));
  const mutedTrackIds = selectedTrackIds("mute");
  const soloTrackIds = selectedTrackIds("solo");
  const measures = candidate?.measures || [];
  const startOrdinal = Math.max(1, Math.min(measures.length, Number($("loop-start").value) || 1));
  const endOrdinal = Math.max(startOrdinal, Math.min(measures.length, Number($("loop-end").value) || measures.length));
  return {
    mutedTrackIds,
    soloTrackIds,
    loopStartMeasureId: measures[startOrdinal - 1]?.id,
    loopEndMeasureId: measures[endOrdinal - 1]?.id,
    metronome: $("metronome").checked,
    countInBars: Math.max(0, Math.min(4, Number($("count-in").value) || 0)),
    tempoOverrideBpm: Math.max(40, Math.min(220, Number($("tempo-override").value) || 104)),
  };
}

function midiFrequency(midi) {
  return 440 * 2 ** ((midi - 69) / 12);
}

function previewVoice(event, midi) {
  const velocityGain = Math.max(0.45, Math.min(1.2, (event.velocity || 80) / 90));
  if (event.kind === "CLICK") return { trackId: event.trackId, velocity: event.velocity, midi, oscillatorType: "square", frequency: midiFrequency(midi), gain: 0.025 * velocityGain, durationCap: 0.08 };
  if (event.trackId === "generated_drums") {
    const drum = {
      36: { oscillatorType: "sine", frequency: 72, gain: 0.12, durationCap: 0.18 },
      38: { oscillatorType: "sawtooth", frequency: 190, gain: 0.055, durationCap: 0.12 },
      42: { oscillatorType: "square", frequency: 1200, gain: 0.018, durationCap: 0.055 },
    }[midi] || { oscillatorType: "square", frequency: 600, gain: 0.025, durationCap: 0.08 };
    return { trackId: event.trackId, velocity: event.velocity, midi, sampleRole: "drums", ...drum, gain: Math.min(0.8, 0.65 * velocityGain) };
  }
  if (event.trackId === "generated_bass") return { trackId: event.trackId, velocity: event.velocity, midi, sampleRole: "bass", oscillatorType: "triangle", frequency: midiFrequency(midi), gain: Math.min(0.8, 0.5 * velocityGain) };
  if (event.trackId === "generated_guitar") return { trackId: event.trackId, velocity: event.velocity, midi, sampleRole: "guitar", oscillatorType: "sawtooth", frequency: midiFrequency(midi), gain: Math.min(0.8, 0.42 * velocityGain) };
  return { trackId: event.trackId, velocity: event.velocity, midi, sampleRole: "keys", oscillatorType: "sine", frequency: midiFrequency(midi), gain: Math.min(0.8, 0.38 * velocityGain) };
}

function validatePlaybackPlan(plan, candidateProjection) {
  if (!plan?.accepted || !plan.rightsAttested) throw new Error("Playback plan is not accepted or rights-attested.");
  if (!playbackPlanMatchesCandidate(plan, candidateProjection)) throw new Error("Playback plan candidate or lineage does not match the accepted candidate.");
  return plan;
}

function playbackPlanMatchesCandidate(plan, candidateProjection) {
  return Boolean(
    plan?.candidateVersionId === candidateProjection?.candidateId
    && JSON.stringify(plan?.lineage) === JSON.stringify(candidateProjection?.lineage),
  );
}

function scheduleTone(context, frequency, start, duration, gainValue = 0.045, voice = {}) {
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = voice.oscillatorType || "sine";
  oscillator.frequency.value = frequency;
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(gainValue, start + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + Math.max(0.025, duration - 0.012));
  oscillator.connect(gain).connect(context.destination);
  oscillator.start(start);
  oscillator.stop(start + duration);
  state.playback.nodes.push(oscillator);
}

async function loadSamplePlayers(context) {
  if (state.playback.samplePlayers) return state.playback.samplePlayers;
  if (!state.playback.sampleLoadPromise) {
    state.playback.sampleLoadPromise = Promise.all(
      Object.entries(SAMPLE_PRESETS).map(async ([role, path]) => {
        const response = await fetch(path);
        if (!response.ok) throw new Error(`Unable to load ${role} acoustic samples.`);
        const preset = await response.json();
        return [role, await WebAudioFontPlayer.load(preset, context)];
      }),
    ).then((entries) => {
      state.playback.samplePlayers = Object.fromEntries(entries);
      return state.playback.samplePlayers;
    }).catch((error) => {
      state.playback.sampleLoadPromise = null;
      throw error;
    });
  }
  return state.playback.sampleLoadPromise;
}

function scheduleSampledVoice(context, frequency, start, duration, gainValue, voice) {
  if (!voice.sampleRole) {
    scheduleTone(context, frequency, start, duration, gainValue, voice);
    return;
  }
  const player = state.playback.samplePlayers?.[voice.sampleRole];
  if (!player) throw new Error(`${voice.sampleRole} acoustic samples are not ready.`);
  const envelope = player.queueWaveTable(start, voice.midi, duration, gainValue);
  if (envelope) state.playback.nodes.push({ stop: () => envelope.cancel(true) });
}

// The API projection is canonical: the browser only schedules returned events
// and uses returned loop/tempo values. Domain semantics stay server-side.
function schedulePlaybackPlan(context, plan, scheduleToneFn, setTimer, isPlaying) {
  const tickSeconds = 60 / plan.tempoBpm / 960;
  const timelineStartTick = plan.events.reduce(
    (minimum, event) => Math.min(minimum, event.startTick),
    plan.loopStartTick,
  );
  const now = context.currentTime + 0.06;
  plan.events.forEach((event) => {
    const duration = Math.max(0.025, event.durationTicks * tickSeconds);
    event.pitches.forEach((midi) => {
      const voice = previewVoice(event, midi);
      scheduleToneFn(
        context,
        voice.frequency,
        now + (event.startTick - timelineStartTick) * tickSeconds,
        Math.min(duration, voice.durationCap || duration),
        voice.gain,
        voice,
      );
    });
  });
  const loopSeconds = (plan.loopEndTick - timelineStartTick) * tickSeconds;
  return setTimer(() => {
    if (isPlaying()) schedulePlaybackPlan(context, plan, scheduleToneFn, setTimer, isPlaying);
  }, loopSeconds * 1000 + 80);
}

function schedulePreviewLoop(context, plan) {
  const sessionId = state.playback.sessionId;
  schedulePlaybackPlan(
    context,
    plan,
    scheduleSampledVoice,
    (callback, delay) => {
      const timer = window.setTimeout(() => {
        state.playback.timers.delete(timer);
        callback();
      }, delay);
      state.playback.timers.add(timer);
      return timer;
    },
    () => playbackSessionIsCurrent(sessionId) && state.playback.playing,
  );
}

function playbackSessionIsCurrent(sessionId) {
  return state.playback.intentToPlay && state.playback.sessionId === sessionId;
}

function cancelActivePlayback() {
  state.playback.sessionId += 1;
  state.playback.playing = false;
  if (state.playback.requestController) state.playback.requestController.abort();
  state.playback.requestController = null;
  state.playback.timers.forEach((timer) => window.clearTimeout(timer));
  state.playback.timers.clear();
  state.playback.nodes.forEach((node) => { try { node.stop(); } catch (_) { /* already ended */ } });
  state.playback.nodes = [];
}

function stopPreview() {
  state.playback.intentToPlay = false;
  cancelActivePlayback();
  $("playback-status").textContent = "Stopped";
}

async function playPreview() {
  if (!state.playback.candidate?.accepted) throw new Error("No accepted candidate is ready for playback.");
  if (!state.playback.candidate.rightsAttested) throw new Error("Candidate rights attestation is missing.");
  if (!(window.AudioContext || window.webkitAudioContext)) throw new Error("Web Audio preview is unavailable in this browser.");
  state.playback.intentToPlay = true;
  cancelActivePlayback();
  const sessionId = state.playback.sessionId;
  const requestController = new AbortController();
  state.playback.requestController = requestController;
  const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
  state.playback.context ||= new AudioContextConstructor();
  await state.playback.context.resume();
  if (!playbackSessionIsCurrent(sessionId)) return false;
  const candidate = state.playback.candidate.candidate;
  const settings = playbackSettings();
  const baseTempo = candidate.global?.tempoMap?.[0]?.bpm || 104;
  $("playback-status").textContent = "Loading local acoustic samples…";
  const planRequest = request(`/v1/arrangement-versions/${state.arrangement.versionId}/playback-plan`, {
    method: "POST",
    body: JSON.stringify({
      seed: state.playback.candidate.lineage.seed,
      tempoBpm: baseTempo,
      ...settings,
    }),
    signal: requestController.signal,
  });
  const [plan] = await Promise.all([planRequest, loadSamplePlayers(state.playback.context)]);
  if (!playbackSessionIsCurrent(sessionId)) return false;
  state.playback.requestController = null;
  state.playback.plan = validatePlaybackPlan(plan, state.playback.candidate);
  state.playback.playing = true;
  $("playback-status").textContent = `Playing accepted candidate ${state.playback.candidate.candidateId}`;
  schedulePreviewLoop(state.playback.context, state.playback.plan);
  return true;
}

async function refreshPlayingPreview(playPreviewFn = playPreview) {
  if (!state.playback.intentToPlay) return false;
  await playPreviewFn();
  return true;
}

function reportPlaybackError(error) {
  if (error.name === "AbortError") return;
  stopPreview();
  $("playback-status").textContent = error.message;
}

$("api-base").addEventListener("change", (event) => { state.apiBase = event.target.value.trim(); });
$("add-bar").addEventListener("click", () => { if (state.bars.length < 64) { state.bars.push(""); renderBars(state.bars.length); } });
$("remove-bar").addEventListener("click", () => { if (state.bars.length > 1) { state.bars.pop(); renderBars(); } });
$("submit-source").addEventListener("click", () => submitSource().catch((error) => setStatus(error.message, true)));
$("approve-source").addEventListener("click", () => approveSource().catch((error) => setStatus(error.message, true)));
$("create-arrangement").addEventListener("click", () => createLockedSeed().catch((error) => setStatus(error.message, true)));
$("play-preview").addEventListener("click", () => playPreview().catch(reportPlaybackError));
$("stop-preview").addEventListener("click", stopPreview);
document.querySelectorAll("[data-mode]").forEach((control) => {
  control.addEventListener("change", () => refreshPlayingPreview().catch(reportPlaybackError));
});
renderBars();
