# Cycle 9 MusicXML and Player-Packet Integrity Demo

Authored source fixture: `Am | F | C | G`; no title lookup, streaming metadata, or model call supplied musical content.

```json
{
  "sourceRevisionId": "src_rev_cycle9_demo",
  "candidateAccepted": true,
  "acceptedVersionId": "candidate_88874fa44f35e4fad24fb878",
  "musicxml": {
    "format": "MusicXML 4.0",
    "bytes": 19480,
    "sha256": "sha256:d8ab3b57c9cbabf064fa58da93cf99aaad630e764f8a72022a41c8e75744e730",
    "validation": {
      "format": "MusicXML 4.0",
      "root": "score-partwise",
      "divisions": 960,
      "partCount": 5,
      "measureCount": 4
    },
    "savedPath": "reports\\cycle-9-score.musicxml",
    "savedBytes": 19480,
    "savedSha256": "sha256:d8ab3b57c9cbabf064fa58da93cf99aaad630e764f8a72022a41c8e75744e730",
    "savedValidation": {
      "format": "MusicXML 4.0",
      "root": "score-partwise",
      "divisions": 960,
      "partCount": 5,
      "measureCount": 4
    },
    "manifest": {
      "artifactType": "MUSICXML_SCORE_PARTWISE",
      "format": "MusicXML 4.0",
      "ticksPerQuarter": 960,
      "sourceRevisionIds": [
        "src_rev_cycle9_demo"
      ],
      "acceptedVersionId": "candidate_88874fa44f35e4fad24fb878",
      "rightsAttested": true,
      "lineage": {
        "seed": 29,
        "engineVersion": "rules-baseline-0.1.0",
        "stylePackVersion": "acoustic-pop@1.0.0",
        "validatorVersion": "rules-0.1.0",
        "inputRevisionSet": [
          "src_rev_cycle9_demo"
        ],
        "provenance": "approved-source-locked-rules-baseline"
      },
      "trackIds": [
        "track_source_guide",
        "generated_drums",
        "generated_bass",
        "generated_guitar",
        "generated_keys"
      ],
      "contentHash": "sha256:d8ab3b57c9cbabf064fa58da93cf99aaad630e764f8a72022a41c8e75744e730"
    },
    "deterministicReplay": true
  },
  "playerPacket": {
    "bytes": 20253,
    "sha256": "sha256:3dbdbb582a91b6b49441a04804cb6cc2731c12464e814cb97295c65902a8aab1",
    "validation": {
      "fileNames": [
        "manifest.json",
        "score.musicxml"
      ],
      "musicxmlBytes": 19480,
      "sourceRevisionIds": [
        "src_rev_cycle9_demo"
      ],
      "acceptedVersionId": "candidate_88874fa44f35e4fad24fb878",
      "rightsAttested": true
    },
    "savedPath": "reports\\cycle-9-player-packet.zip",
    "savedBytes": 20253,
    "savedSha256": "sha256:3dbdbb582a91b6b49441a04804cb6cc2731c12464e814cb97295c65902a8aab1",
    "savedValidation": {
      "fileNames": [
        "manifest.json",
        "score.musicxml"
      ],
      "musicxmlBytes": 19480,
      "sourceRevisionIds": [
        "src_rev_cycle9_demo"
      ],
      "acceptedVersionId": "candidate_88874fa44f35e4fad24fb878",
      "rightsAttested": true
    },
    "manifestPath": "reports\\cycle-9-player-packet-manifest.json",
    "manifest": {
      "artifactType": "BAND_FORGE_PLAYER_PACKET",
      "formatVersion": "1.0",
      "files": {
        "score.musicxml": {
          "bytes": 19480,
          "sha256": "sha256:d8ab3b57c9cbabf064fa58da93cf99aaad630e764f8a72022a41c8e75744e730"
        }
      },
      "sourceRevisionIds": [
        "src_rev_cycle9_demo"
      ],
      "acceptedVersionId": "candidate_88874fa44f35e4fad24fb878",
      "rightsAttested": true,
      "lineage": {
        "seed": 29,
        "engineVersion": "rules-baseline-0.1.0",
        "stylePackVersion": "acoustic-pop@1.0.0",
        "validatorVersion": "rules-0.1.0",
        "inputRevisionSet": [
          "src_rev_cycle9_demo"
        ],
        "provenance": "approved-source-locked-rules-baseline"
      }
    },
    "deterministicReplay": true
  },
  "rightsAttested": true,
  "sourceHarmonyPreserved": true
}
```

This demonstrates deterministic MusicXML 4.0 score-partwise bytes, 960-tick structural smoke validation, and a deterministic ZIP packet with manifest hashes, source revision IDs, accepted version, rights attestation, and generation lineage. It does not claim browser rendering, readable engraving, playability, PDF, signed downloads, transposition, or audio playback.
