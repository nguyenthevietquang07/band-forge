# ADR-005: Song Services Provide Metadata Only

## Status

Accepted.

## Context

Users expect title search, but catalog APIs generally return track metadata, not
authorized lead-sheet harmony. Scraping chart/lyric sites or inferring that a
streaming selection grants arrangement rights creates accuracy and legal risk.

## Decision

Spotify/MusicBrainz-style integrations may fill title, artist, album, artwork,
and identifiers under provider terms. They never satisfy the approved harmonic
source gate and are never used to train a model. Musical source must come from
user-entered, uploaded, public-domain, authored, or explicitly licensed content.

## Alternatives

- Search any song and synthesize official chords: rejected because metadata is
  insufficient and rights/provenance are unclear.
- No metadata search: viable but less convenient; retained as fallback.

## Consequences

The UI must explain why selecting a song still requires musical material.
Metadata-provider failure cannot block arrangement work.

