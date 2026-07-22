# Cycle 8 MIDI Artifact and Scoped-Regeneration Demo

Authored source fixture: `Am | F | C | G`; no metadata lookup or model call.

```json
{
  "sourceRevisionId": "src_rev_cycle8_demo",
  "candidateVersionId": "candidate_c534aad9bc6edd374d0ecf55",
  "candidateAccepted": true,
  "midiArtifact": {
    "path": "reports/cycle-8-candidate.mid",
    "bytes": 556,
    "validation": {
      "format": 1,
      "trackCount": 6,
      "ticksPerQuarter": 960
    },
    "manifest": {
      "artifactType": "STANDARD_MIDI_FILE",
      "format": 1,
      "ticksPerQuarter": 960,
      "trackCount": 6,
      "parentVersionId": "candidate_c534aad9bc6edd374d0ecf55",
      "sourceRevisionIds": [
        "src_rev_cycle8_demo"
      ],
      "rightsAttested": true,
      "provenance": {
        "seed": 23,
        "engineVersion": "rules-baseline-0.1.0",
        "stylePackVersion": "acoustic-pop@1.0.0",
        "validatorVersion": "rules-0.1.0",
        "inputRevisionSet": [
          "src_rev_cycle8_demo"
        ],
        "provenance": "approved-source-locked-rules-baseline"
      },
      "contentHash": "sha256:f45487bd823fa5dcd5e0dae005c06ef91077fce69e8c3a710ecc2bd9490bf5a7"
    }
  },
  "regeneratedCandidateVersionId": "regen_e846a91148d191e16d649025",
  "regeneratedMidiArtifact": {
    "path": "reports/cycle-8-regenerated.mid",
    "bytes": 556,
    "validation": {
      "format": 1,
      "trackCount": 6,
      "ticksPerQuarter": 960
    },
    "manifest": {
      "artifactType": "STANDARD_MIDI_FILE",
      "format": 1,
      "ticksPerQuarter": 960,
      "trackCount": 6,
      "parentVersionId": "regen_e846a91148d191e16d649025",
      "sourceRevisionIds": [
        "src_rev_cycle8_demo"
      ],
      "rightsAttested": true,
      "provenance": {
        "seed": 23,
        "engineVersion": "rules-baseline-0.1.0",
        "stylePackVersion": "acoustic-pop@1.0.0",
        "validatorVersion": "rules-0.1.0",
        "inputRevisionSet": [
          "src_rev_cycle8_demo"
        ],
        "provenance": "approved-source-locked-rules-baseline"
      },
      "contentHash": "sha256:1b21fc58246788fe2c3966907e087b1b0d5ea6b1070ae47db49ed81043d728a9"
    }
  },
  "candidateInputUnchanged": true,
  "sourceHarmonyUnchanged": true,
  "scopedRegeneration": {
    "parentVersionId": "candidate_c534aad9bc6edd374d0ecf55",
    "newVersionId": "regen_e846a91148d191e16d649025",
    "trackIds": [
      "generated_bass"
    ],
    "measureIds": [
      "measure_002"
    ],
    "seed": 91,
    "mode": "SAFE",
    "sourceRevisionIds": [
      "src_rev_cycle8_demo"
    ],
    "rightsAttested": true,
    "provenance": {
      "seed": 23,
      "engineVersion": "rules-baseline-0.1.0",
      "stylePackVersion": "acoustic-pop@1.0.0",
      "validatorVersion": "rules-0.1.0",
      "inputRevisionSet": [
        "src_rev_cycle8_demo"
      ],
      "provenance": "approved-source-locked-rules-baseline"
    },
    "changedEventIds": [
      "event_bass_002"
    ],
    "outsideScopeContentHashBefore": "sha256:0894d36ce4e540dc4cfb17fbc73b5120172dad33b93fc386c92a2208c17c7ad8",
    "outsideScopeContentHashAfter": "sha256:0894d36ce4e540dc4cfb17fbc73b5120172dad33b93fc386c92a2208c17c7ad8",
    "preservedOutsideScope": true
  }
}
```

This demonstrates deterministic type-1 MIDI bytes, structural MIDI validation, rights/provenance manifesting, and immutable SAFE event-scope regeneration. It does not claim browser playback, audio quality, musician playability, notation, or support for later regeneration modes.
