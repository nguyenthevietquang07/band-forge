# Cycle 7 Candidate Comparison and Validator Catalog Demo

Authored source fixture: `Am | F | C | G`; no metadata lookup or model call.

```json
{
  "sourceRevisionId": "src_rev_cycle7_demo",
  "candidateCount": 3,
  "candidates": [
    {
      "candidateId": "candidate_e247b98a164644915c58ed3a",
      "seed": 11,
      "accepted": true,
      "hardFindingCount": 0,
      "sourceHarmonyUnchanged": true,
      "lineage": {
        "seed": 11,
        "engineVersion": "rules-baseline-0.1.0",
        "stylePackVersion": "acoustic-pop@1.0.0",
        "validatorVersion": "rules-0.1.0",
        "inputRevisionSet": [
          "src_rev_cycle7_demo"
        ],
        "provenance": "approved-source-locked-rules-baseline"
      },
      "findings": []
    },
    {
      "candidateId": "candidate_7603ce75fbd6c7000e93a2c4",
      "seed": 17,
      "accepted": true,
      "hardFindingCount": 0,
      "sourceHarmonyUnchanged": true,
      "lineage": {
        "seed": 17,
        "engineVersion": "rules-baseline-0.1.0",
        "stylePackVersion": "acoustic-pop@1.0.0",
        "validatorVersion": "rules-0.1.0",
        "inputRevisionSet": [
          "src_rev_cycle7_demo"
        ],
        "provenance": "approved-source-locked-rules-baseline"
      },
      "findings": []
    },
    {
      "candidateId": "candidate_1d44afa66468a8c2a51a28fe",
      "seed": 23,
      "accepted": true,
      "hardFindingCount": 0,
      "sourceHarmonyUnchanged": true,
      "lineage": {
        "seed": 23,
        "engineVersion": "rules-baseline-0.1.0",
        "stylePackVersion": "acoustic-pop@1.0.0",
        "validatorVersion": "rules-0.1.0",
        "inputRevisionSet": [
          "src_rev_cycle7_demo"
        ],
        "provenance": "approved-source-locked-rules-baseline"
      },
      "findings": []
    }
  ],
  "sameSeedReplay": true,
  "validatorCatalog": {
    "validatorVersion": "rules-0.1.0",
    "scope": "hard deterministic structural validators",
    "rules": [
      {
        "ruleId": "BF-LOCK-001",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "description": "Candidate harmony must equal the locked source harmony."
      },
      {
        "ruleId": "BF-LOCK-002",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "description": "Only DRAFT or ACCEPTED source documents can generate candidates."
      },
      {
        "ruleId": "BF-LOCK-003",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "description": "The source document must declare a HARMONY lock."
      },
      {
        "ruleId": "BF-LOCK-004",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "description": "Every source harmony event must remain locked."
      },
      {
        "ruleId": "BF-RIGHTS-001",
        "category": "RIGHTS",
        "severity": "ERROR",
        "description": "Every source reference must carry a rights attestation."
      },
      {
        "ruleId": "BF-SCHEMA-001",
        "category": "SCHEMA",
        "severity": "ERROR",
        "description": "Source and candidate documents must satisfy the canonical schema."
      },
      {
        "ruleId": "BF-STRUCT-001",
        "category": "BAR_ALIGNMENT",
        "severity": "ERROR",
        "description": "Events must fit inside their canonical measure boundaries."
      },
      {
        "ruleId": "BF-TIMING-001",
        "category": "TIMING",
        "severity": "ERROR",
        "description": "Event durations must be positive."
      },
      {
        "ruleId": "BF-RANGE-001",
        "category": "RANGE",
        "severity": "ERROR",
        "description": "Sounding pitches must fit the track sounding range."
      },
      {
        "ruleId": "BF-RANGE-002",
        "category": "RANGE",
        "severity": "ERROR",
        "description": "Written pitches must fit the track written range."
      },
      {
        "ruleId": "BF-POLY-001",
        "category": "POLYPHONY",
        "severity": "ERROR",
        "description": "Event voice count must fit the track polyphony limit."
      }
    ],
    "representativeFailures": [
      {
        "accepted": false,
        "ruleId": "BF-LOCK-001",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "message": "Candidate changed locked source harmony.",
        "trackId": null,
        "measureId": null
      },
      {
        "accepted": false,
        "ruleId": "BF-LOCK-002",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "message": "Source document is not usable.",
        "trackId": null,
        "measureId": null
      },
      {
        "accepted": false,
        "ruleId": "BF-LOCK-003",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "message": "Source harmony lock is missing.",
        "trackId": null,
        "measureId": null
      },
      {
        "accepted": false,
        "ruleId": "BF-LOCK-004",
        "category": "SOURCE_LOCK",
        "severity": "ERROR",
        "message": "Source harmony is not fully locked.",
        "trackId": null,
        "measureId": null
      },
      {
        "accepted": false,
        "ruleId": "BF-RIGHTS-001",
        "category": "RIGHTS",
        "severity": "ERROR",
        "message": "Every source reference must carry a rights attestation.",
        "trackId": null,
        "measureId": null
      },
      {
        "accepted": false,
        "ruleId": "BF-SCHEMA-001",
        "category": "SCHEMA",
        "severity": "ERROR",
        "message": "ArrangementDocument schema violation at document: 'tracks' is a required property",
        "trackId": null,
        "measureId": null
      },
      {
        "accepted": false,
        "ruleId": "BF-STRUCT-001",
        "category": "BAR_ALIGNMENT",
        "severity": "ERROR",
        "message": "Event exceeds the canonical measure boundary.",
        "trackId": "generated_drums",
        "measureId": null
      },
      {
        "accepted": false,
        "ruleId": "BF-TIMING-001",
        "category": "TIMING",
        "severity": "ERROR",
        "message": "Event duration must be positive.",
        "trackId": "generated_drums",
        "measureId": "measure_001"
      },
      {
        "accepted": false,
        "ruleId": "BF-RANGE-001",
        "category": "RANGE",
        "severity": "ERROR",
        "message": "Event pitch is outside the track sounding range.",
        "trackId": "generated_guitar",
        "measureId": "measure_001"
      },
      {
        "accepted": false,
        "ruleId": "BF-RANGE-002",
        "category": "RANGE",
        "severity": "ERROR",
        "message": "Event pitch is outside the track written range.",
        "trackId": "generated_guitar",
        "measureId": "measure_001"
      },
      {
        "accepted": false,
        "ruleId": "BF-POLY-001",
        "category": "POLYPHONY",
        "severity": "ERROR",
        "message": "Event voice count exceeds the track polyphony limit.",
        "trackId": "generated_guitar",
        "measureId": "measure_001"
      }
    ]
  }
}
```

This demonstrates bounded deterministic candidate comparison and machine-readable hard-validator evidence. It does not claim musical quality, playability, audio, notation, regeneration, learned generation, or production readiness.
