# Cycle 5 Chart Export Demo Evidence

Date: 2026-07-19

Command: `python scripts/run_cycle4_demo.py`

The real HTTP walkthrough now also fetched
`/v1/source-revisions/{approvedRevisionId}/chart-export` after approval. The
response was `200 text/html; charset=utf-8` and contained the authored chart
title, approved source revision ID, and persisted content hash. The same run
verified the invalid bar-3 finding, distinct corrected revision, approval, and
source-locked seed with `ticksPerQuarter=960` and a `HARMONY` lock.

This is a deterministic HTML/print chart artifact, not a PDF. `reportlab` and
`weasyprint` were unavailable in the local environment, so PDF generation and
PDF validation remain unimplemented and are not claimed.
