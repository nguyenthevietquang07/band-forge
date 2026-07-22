import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const debuggerPort = process.env.BANDFORGE_CHROME_DEBUG_PORT || "9223";
const targetUrl = "http://127.0.0.1:8012/";
const targets = await fetch(`http://127.0.0.1:${debuggerPort}/json/list`).then((response) => response.json());
const target = targets.find((item) => item.type === "page" && item.url === targetUrl);
if (!target) throw new Error(`No Chrome page found for ${targetUrl}`);

const socket = new WebSocket(target.webSocketDebuggerUrl);
const pending = new Map();
const consoleProblems = [];
const playbackRequests = [];
const playbackResponses = [];
let sequence = 0;

socket.addEventListener("message", (message) => {
  const payload = JSON.parse(message.data);
  if (payload.id && pending.has(payload.id)) {
    const { resolve, reject } = pending.get(payload.id);
    pending.delete(payload.id);
    if (payload.error) reject(new Error(payload.error.message));
    else resolve(payload.result);
    return;
  }
  if (payload.method === "Runtime.exceptionThrown") {
    consoleProblems.push(payload.params.exceptionDetails.text);
  }
  if (payload.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(payload.params.type)) {
    consoleProblems.push(`${payload.params.type}: ${payload.params.args.map((item) => item.value || item.description).join(" ")}`);
  }
  if (payload.method === "Network.requestWillBeSent" && payload.params.request.url.endsWith("/playback-plan")) {
    playbackRequests.push({ requestId: payload.params.requestId, postData: payload.params.request.postData });
  }
  if (payload.method === "Network.responseReceived" && payload.params.response.url.endsWith("/playback-plan")) {
    playbackResponses.push({ requestId: payload.params.requestId, status: payload.params.response.status });
  }
});

await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

function command(method, params = {}) {
  const id = ++sequence;
  socket.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

async function evaluate(expression) {
  const result = await command("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function waitFor(expression, label, timeoutMs = 10000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (await evaluate(expression)) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out waiting for ${label}`);
}

await command("Runtime.enable");
await command("Page.enable");
await command("Network.enable");
await command("Page.addScriptToEvaluateOnNewDocument", { source: `(() => {
  window.__bfOscillatorStarts = [];
  window.__bfBufferStarts = [];
  window.__bfBufferStops = [];
  const originalStart = OscillatorNode.prototype.start;
  OscillatorNode.prototype.start = function (...args) {
    window.__bfOscillatorStarts.push({ type: this.type, frequency: this.frequency.value });
    return originalStart.apply(this, args);
  };
  const originalBufferStart = AudioBufferSourceNode.prototype.start;
  AudioBufferSourceNode.prototype.start = function (...args) {
    window.__bfBufferStarts.push({ when: args[0], duration: this.buffer?.duration || 0 });
    return originalBufferStart.apply(this, args);
  };
  const originalBufferStop = AudioBufferSourceNode.prototype.stop;
  AudioBufferSourceNode.prototype.stop = function (...args) {
    window.__bfBufferStops.push({ when: args[0] });
    return originalBufferStop.apply(this, args);
  };
})()` });
await command("Page.reload", { ignoreCache: true });
await waitFor("document.readyState === 'complete'", "page load");

await evaluate(`(() => {
  const setValue = (id, value) => {
    const element = document.getElementById(id);
    element.value = value;
    element.dispatchEvent(new Event('input', { bubbles: true }));
  };
  setValue('song-title', 'Playback control browser verification');
  setValue('song-artist', 'BandForge');
  setValue('bar-3', 'C');
  document.getElementById('rights-attested').checked = true;
  document.getElementById('submit-source').click();
})()`);
await waitFor("document.getElementById('review-status').textContent === 'Ready to approve'", "clean source revision");
await evaluate("document.getElementById('approve-source').click()");
await waitFor("document.getElementById('review-status').textContent === 'Approved'", "source approval");
await evaluate("document.getElementById('create-arrangement').click()");
await waitFor("document.getElementById('play-preview').disabled === false", "accepted candidate");

const trackIds = ["generated_drums", "generated_bass", "generated_guitar", "generated_keys"];
const canonicalTrackIds = ["track_source_guide", ...trackIds];
let playbackStarted = false;

async function selectControls({ mute = [], solo = [] }) {
  const responseCount = playbackResponses.length;
  await evaluate(`(() => {
    window.__bfOscillatorStarts = [];
    window.__bfBufferStarts = [];
    window.__bfBufferStops = [];
    document.querySelectorAll('[data-mode]').forEach((control) => { control.checked = false; });
    ${JSON.stringify(mute)}.forEach((trackId) => {
      document.querySelector('[data-mode="mute"][data-track-id="' + trackId + '"]').checked = true;
    });
    ${JSON.stringify(solo)}.forEach((trackId) => {
      document.querySelector('[data-mode="solo"][data-track-id="' + trackId + '"]').checked = true;
    });
    if (${playbackStarted}) {
      document.querySelector('[data-mode]').dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      document.getElementById('play-preview').click();
    }
  })()`);
  const started = Date.now();
  while (playbackResponses.length === responseCount && Date.now() - started < 10000) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  if (playbackResponses.length === responseCount) throw new Error("Timed out waiting for playback-plan response");
  await waitFor(
    "document.getElementById('playback-status').textContent.startsWith('Playing accepted candidate')",
    "browser audio scheduling",
  );
  await waitFor("window.__bfBufferStarts.length > 0", "sample source creation", 30000);
  playbackStarted = true;
  return playbackResponses.at(-1);
}

async function verifyPlan(expected, label, response) {
  if (response.status !== 200) throw new Error(`${label} playback-plan returned ${response.status}`);
  const responseBody = await command("Network.getResponseBody", { requestId: response.requestId });
  const payload = JSON.parse(responseBody.body);
  const matchingRequest = playbackRequests.find((request) => request.requestId === response.requestId);
  const request = JSON.parse(matchingRequest.postData);
  const eventCounts = payload.events.reduce((counts, event) => {
    counts[event.trackId] = (counts[event.trackId] || 0) + 1;
    return counts;
  }, {});
  const plan = {
    activeTrackIds: payload.activeTrackIds,
    eventCounts,
    requestedMutedTrackIds: request.mutedTrackIds,
    requestedSoloTrackIds: request.soloTrackIds,
    oscillators: await evaluate("window.__bfOscillatorStarts"),
    sampleSources: await evaluate("window.__bfBufferStarts"),
    status: await evaluate("document.getElementById('playback-status').textContent"),
  };
  if (JSON.stringify(plan.activeTrackIds) !== JSON.stringify(expected)) {
    throw new Error(`${label} active tracks ${JSON.stringify(plan.activeTrackIds)} did not match ${JSON.stringify(expected)}`);
  }
  if (expected.filter((trackId) => trackIds.includes(trackId)).some((trackId) => !plan.eventCounts[trackId])) {
    throw new Error(`${label} plan omitted events for an active track: ${JSON.stringify(plan.eventCounts)}`);
  }
  if (plan.eventCounts.track_source_guide) throw new Error(`${label} scheduled source-guide events`);
  const expectedSampleSources = payload.events.reduce((count, event) => (
    event.kind === "CLICK" ? count : count + event.pitches.length
  ), 0);
  if (plan.sampleSources.length !== expectedSampleSources) {
    throw new Error(`${label} scheduled ${plan.sampleSources.length} samples; expected ${expectedSampleSources}`);
  }
  return plan;
}

const evidence = { allTogether: null, mute: {}, solo: {}, previewVoices: null };
let response = await selectControls({});
evidence.allTogether = await verifyPlan(canonicalTrackIds, "all together", response);

for (const trackId of trackIds) {
  response = await selectControls({ mute: [trackId] });
  evidence.mute[trackId] = await verifyPlan(canonicalTrackIds.filter((item) => item !== trackId), `mute ${trackId}`, response);
  if (JSON.stringify(evidence.mute[trackId].requestedMutedTrackIds) !== JSON.stringify([trackId])) {
    throw new Error(`mute ${trackId} request lost the selected control`);
  }
}

for (const trackId of trackIds) {
  response = await selectControls({ solo: [trackId] });
  evidence.solo[trackId] = await verifyPlan([trackId], `solo ${trackId}`, response);
  if (JSON.stringify(evidence.solo[trackId].requestedSoloTrackIds) !== JSON.stringify([trackId])) {
    throw new Error(`solo ${trackId} request lost the selected control`);
  }
  if (evidence.solo[trackId].oscillators.length) throw new Error(`solo ${trackId} used oscillator synthesis`);
}

const stoppedBefore = await evaluate("window.__bfBufferStops.length");
await evaluate("document.getElementById('stop-preview').click()");
await waitFor("document.getElementById('playback-status').textContent === 'Stopped'", "explicit stop");
const stoppedAfter = await evaluate("window.__bfBufferStops.length");
if (stoppedAfter <= stoppedBefore) throw new Error("Stop did not cancel scheduled sample sources");

const raceResponseCount = playbackResponses.length;
await evaluate(`(() => {
  window.__bfBufferStarts = [];
  document.getElementById('play-preview').click();
  document.getElementById('stop-preview').click();
  document.getElementById('play-preview').click();
})()`);
const raceStarted = Date.now();
while (playbackResponses.length === raceResponseCount && Date.now() - raceStarted < 30000) {
  await new Promise((resolve) => setTimeout(resolve, 100));
}
if (playbackResponses.length === raceResponseCount) throw new Error("Timed out waiting for stop/replay race response");
await waitFor(
  "document.getElementById('playback-status').textContent.startsWith('Playing accepted candidate')",
  "stop/replay final playback",
  30000,
);
const raceResponse = playbackResponses.at(-1);
const raceBody = await command("Network.getResponseBody", { requestId: raceResponse.requestId });
const racePlan = JSON.parse(raceBody.body);
const expectedRaceSources = racePlan.events.reduce((count, event) => (
  event.kind === "CLICK" ? count : count + event.pitches.length
), 0);
const actualRaceSources = await evaluate("window.__bfBufferStarts.length");
if (actualRaceSources !== expectedRaceSources) {
  throw new Error(`stop/replay stacked ${actualRaceSources} sample sources; expected ${expectedRaceSources}`);
}
evidence.stopReplay = { stoppedSources: stoppedAfter - stoppedBefore, expectedRaceSources, actualRaceSources };
evidence.previewVoices = "Local FluidR3 sample sources verified for every generated role; click remains synthesized.";

const screenshot = await command("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
const root = path.resolve(import.meta.dirname, "..");
fs.writeFileSync(path.join(root, "reports", "playback-controls-fixed-browser.png"), Buffer.from(screenshot.data, "base64"));
evidence.consoleProblems = consoleProblems;
evidence.checkedAt = new Date().toISOString();
evidence.url = targetUrl;
fs.writeFileSync(
  path.join(root, "reports", "playback-controls-fixed-browser.json"),
  `${JSON.stringify(evidence, null, 2)}\n`,
  "utf8",
);

if (consoleProblems.length) throw new Error(`Browser console problems: ${consoleProblems.join(" | ")}`);
console.log(JSON.stringify(evidence, null, 2));
socket.close();
