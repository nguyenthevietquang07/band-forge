# Cycle 4 Editor Demo Evidence

Date: 2026-07-22T12:28:42.112492+00:00

Source fixture: original/authored demo chart `Am | F | Cmaj9#11 | G`; the title and artist are metadata only.

```json
{
  "scope": "Cycle 4 structured source editor",
  "browserVerified": false,
  "staticPage": {
    "status": 200,
    "containsEditorHeading": true
  },
  "song": {
    "status": 201,
    "replayStatus": 201,
    "sameIdOnReplay": true,
    "requestId": "req_7190e1d0eddd473694e8a4afed0741e2"
  },
  "invalidRevision": {
    "status": 201,
    "revisionId": "src_rev_300e0971e2cc49d2b17b8633a21d3af6",
    "findingBars": [
      3
    ]
  },
  "correctedRevision": {
    "status": 201,
    "revisionId": "src_rev_5d23327e320c40ff85f1f26a87d6de73",
    "newImmutableId": true,
    "findingCount": 0
  },
  "approval": {
    "status": 200,
    "revisionStatus": "APPROVED"
  },
  "chartExport": {
    "status": 200,
    "contentType": "text/html; charset=utf-8",
    "containsTitle": true,
    "containsSourceRevision": true,
    "containsContentHash": true
  },
  "lockedSeed": {
    "status": 201,
    "arrangementId": "arrangement_009b5899ca2845a584cc64df57d58b24",
    "versionId": "arr_version_3fc32597831d4d7596cf240e62044bc3",
    "ticksPerQuarter": 960,
    "lockTypes": [
      "HARMONY"
    ],
    "sourceRevisionId": "src_rev_5d23327e320c40ff85f1f26a87d6de73"
  }
}
```

The real HTTP flow created an idempotent song, observed a blocking finding on bar 3, submitted a corrected immutable revision, approved it, and created a source-locked ArrangementDocument seed. Browser visual automation was unavailable (`agent-browser`, Chrome/Edge, and Chrome DevTools MCP were not available); the static page was fetched over HTTP and API behavior was exercised over HTTP. Generation, playback, notation, export, imports, model planning, and scale readiness remain roadmap work.
