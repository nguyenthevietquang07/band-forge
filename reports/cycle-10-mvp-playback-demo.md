# Cycle 10 MVP playback demo

Command: `python scripts/run_cycle10_demo.py`

The demo builds an accepted, rights-attested deterministic candidate from an authored structured chart, then constructs an immutable playback plan with mute/solo, measure looping, metronome, count-in, and tempo override.

```json
{
  "candidateVersionId": "candidate_75ec0b80734adf3aa5254967",
  "candidateStatus": "ACCEPTED",
  "sourceRevisionIds": [
    "src_rev_cycle10_demo"
  ],
  "rightsAttested": true,
  "lineage": {
    "seed": 41,
    "engineVersion": "rules-baseline-0.1.0",
    "stylePackVersion": "acoustic-pop@1.0.0",
    "validatorVersion": "rules-0.1.0",
    "inputRevisionSet": [
      "src_rev_cycle10_demo"
    ],
    "provenance": "approved-source-locked-rules-baseline"
  },
  "controls": {
    "mutedTrackIds": [
      "generated_bass"
    ],
    "soloTrackIds": [
      "generated_bass",
      "generated_guitar"
    ],
    "loopMeasureIds": [
      "measure_002",
      "measure_003"
    ],
    "metronome": true,
    "countInBars": 1,
    "tempoOverrideBpm": 116
  },
  "plan": {
    "tempoBpm": 116,
    "activeTrackIds": [
      "generated_guitar"
    ],
    "eventCount": 14,
    "musicalEventCount": 2,
    "clickEventCount": 12,
    "loopStartTick": 3840,
    "loopEndTick": 11520
  },
  "canonicalCandidateUnchanged": true,
  "browserAutomationAvailable": {
    "agentBrowser": false,
    "chrome": false,
    "msedge": false
  },
  "sourceBoundary": "Candidate notes derive only from the supplied structured chart; no metadata or streaming lookup supplies music."
}
```

The web screen consumes the accepted candidate projection returned after the approved source seed. Browser automation availability is recorded above; no hosted audio or private-beta behavior is claimed.
