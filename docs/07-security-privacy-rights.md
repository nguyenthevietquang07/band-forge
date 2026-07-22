# Security, Privacy, and Rights

This is a product-engineering policy, not legal advice. Before commercial launch,
qualified counsel should review music licensing, dataset use, generated-output
terms, and the jurisdictions in which BandForge operates.

## 1. Threat Model Summary

Protected assets include private charts/uploads, generated arrangements, user
identity, workspace membership, signed artifact URLs, model credentials,
provider budgets, and training/evaluation data.

Primary threats:

- cross-workspace object access or insecure direct object references;
- malicious PDF/image/XML/MIDI uploads and parser exploitation;
- ZIP/XML bombs, oversized decompression, path traversal, and hanging parsers;
- stored XSS in titles, lyrics, comments, metadata, and SVG;
- prompt injection contained in uploaded text or third-party metadata;
- queue abuse, expensive generation denial of service, and duplicate billing;
- leaked private charts through logs, analytics, model providers, or public URLs;
- unauthorized copyrighted content ingestion or dataset use;
- model memorization or excessive similarity to training examples;
- supply-chain vulnerabilities in notation, media, and parsing libraries.

## 2. Authorization

- Every resource belongs to exactly one workspace.
- All repository queries require authorized workspace context derived from the
  authenticated membership, never trusted from request JSON alone.
- Roles are owner, arranger, musician, and viewer. Only owners manage members or
  retention; only arrangers mutate shared sources/arrangements; musicians can
  comment/report and personalize display/transposition views.
- Artifact download tokens are short-lived, single-resource, and authorized at
  issuance. Object keys are unguessable but obscurity is not authorization.
- Audit membership changes, source approvals, acceptance, exports, deletes,
  consent changes, and administrative access.

## 3. Upload Security

Follow defense in depth:

- allowlist only `.musicxml`, `.xml`, `.mxl`, `.mid`, `.midi`, `.cho`, `.txt`,
  `.pdf`, `.png`, `.jpg`, and `.jpeg` when the matching feature is enabled;
- validate declared type, extension, file signature, parser result, and size;
- generate storage names and preserve the original display name only as escaped
  metadata;
- upload into a private quarantine prefix outside any executable/web root;
- scan for malware where available before parsing;
- parse in a sandboxed worker with no credentials, no outbound network, CPU,
  memory, wall-time, page, track, event, XML-entity, and decompression limits;
- disable external XML entities and network schema resolution; use local
  MusicXML schemas;
- rasterize or sanitize previews; never embed user SVG/HTML directly;
- move to the approved object prefix only after checks; record hash and scanner
  versions;
- rate-limit upload count and total uncompressed bytes.

OWASP advises allowlisting extensions, distrust of client Content-Type, random
server filenames, size limits, authorization, storage outside the web root, and
content scanning. BandForge applies all of them.

## 4. Model and Prompt Security

- Uploaded lyrics/comments/metadata are data, never executable instructions.
- Build structured prompts from typed fields and delimit untrusted content.
- Give model adapters no tool access, database credentials, or network authority.
- Validate output against a strict schema and domain rules.
- Redact secrets and unnecessary personal/source content before provider calls.
- Support a local/rules-only mode. Record whether a third-party provider received
  user content and disclose it in privacy settings.
- Apply per-workspace token/cost caps, timeouts, and circuit breakers.
- Do not log full prompts or full source charts by default.

## 5. Privacy and Retention

- Private by default; no public link is created implicitly.
- Encrypt transport and provider-managed storage; separate secrets from config.
- Logs use IDs and hashes, not note/lyric payloads.
- Analytics capture workflow events and aggregate musical features only when
  necessary; never copy the entire arrangement into general analytics.
- User uploads and generated artifacts have a documented retention policy and a
  deletion workflow covering database records, object versions, caches, and
  backups according to stated backup retention.
- Production support access is time-bound, audited, and least privilege.
- User material is excluded from training by default. Training consent is
  separate, revocable for future runs, specific about data/use, and not bundled
  with basic product terms.

## 6. Music Rights Boundary

BandForge stores and transforms musical compositions and sheet representations,
which can be copyrighted independently of recordings. Therefore:

- users attest they own or are permitted to use each uploaded source;
- the product provides a notice/reporting and takedown channel before public
  sharing is introduced;
- title/artist lookup returns catalog metadata only;
- Spotify search may assist metadata selection, but Spotify content may not be
  used to train an AI model under Spotify's current developer policy;
- MusicBrainz is optional metadata with its service terms and rate limits;
- do not scrape chord/tab/lyrics websites;
- a future licensed chart provider must expose explicit entitlements and usage
  terms; provider content remains provenance-tagged and access-controlled;
- exports include source/provenance metadata where appropriate but do not claim
  ownership of the underlying composition.

## 7. Dataset Rights Gate

Before any training/evaluation dataset enters the pipeline, record source,
version, content hash, code license, data/content license, attribution, allowed
uses, restrictions, territorial concerns if known, and reviewer approval.

CC BY 4.0 permits sharing/adaptation, including commercially, subject to
attribution and related conditions. CC BY-NC-SA is not acceptable for a
commercial production model without another license. Public availability and a
repository's software license are insufficient evidence for music-content use.

## 8. Secrets and Supply Chain

- Secrets live in the deployment secret manager and `.env` only for local
  development; `.env.example` contains names, not values.
- Use least-privilege service identities for DB, queue, object storage, and model
  provider.
- Pin dependencies and base images; run dependency, container, and secret scans.
- Generate an SBOM for releases.
- Verify dataset/model/artifact hashes and model provenance.
- Review AGPL and other reciprocal licenses before server integration. Audiveris
  is optional pending this review.

## 9. Abuse and Operational Controls

- Per-user/workspace rate limits and concurrent-job caps;
- bounded candidate counts, source size, arrangement duration, and track count;
- billing/cost guard before enqueue and final accounting after provider use;
- anomaly alerts for repeated parser failures, cross-workspace denials, excessive
  downloads, and provider spend;
- global and per-provider kill switches;
- incident runbook for data exposure, malicious upload, model-provider leak, and
  rights complaint.

## 10. Security Acceptance Gate

No public beta with uploads until tenant isolation tests, signed-URL tests,
malicious-file fixtures, parser limits, secret scanning, dependency review,
deletion verification, audit logs, rate limits, and a rights/takedown workflow
are implemented and demonstrated.

