# Research Sources and Decision Evidence

Research date: 2026-07-19. Prefer these primary/official sources over summaries.
Recheck versions, policies, licenses, and service terms before implementation or
commercial launch.

## Formats and Rendering

- [MusicXML 4.0 specification](https://www.w3.org/2021/06/musicxml40/) describes
  an open exchange format for digital sheet music and reports broad application
  support. BandForge uses it for interchange, not canonical business state.
- [MusicXML structure tutorial](https://www.w3.org/2021/06/musicxml40/tutorial/structure-of-musicxml-files/)
  explains partwise/timewise structures and notes that partwise is most common.
- [MusicXML MIDI-compatible tutorial](https://www.w3.org/2021/06/musicxml40/tutorial/midi-compatible-part/)
  documents divisions, pitches, key, meter, and playback-oriented elements.
- [MusicXML 4.0 XSD](https://www.w3.org/2021/06/musicxml40/listings/musicxml.xsd/)
  supports local schema validation; the docs recommend local catalogs rather
  than network schema loading.
- [MIDI Association Standard MIDI Files](https://midi.org/standard-midi-files)
  defines time-stamped multitrack interchange and explicitly says SMF need not be
  an application's in-memory format.
- [OpenSheetMusicDisplay class documentation](https://opensheetmusicdisplay.github.io/classdoc/classes/OpenSheetMusicDisplay.html)
  documents loading MusicXML and rendering into an HTML container.
- [Tone.js Sampler documentation](https://tonejs.github.io/docs/15.1.22/classes/Sampler.html)
  documents browser sample mapping and repitching for preview playback.
- [ChordPro section directives](https://www.chordpro.org/chordpro/directives-env/)
  define verse/chorus/bridge environments and unknown-section behavior.

## Music Analysis, Constraints, and Jobs

- [music21 documentation](https://music21.org/music21docs/) and
  [voice-leading reference](https://music21.org/music21docs/moduleReference/moduleVoiceLeading.html)
  support chord, key, interval, crossing, overlap, resolution, and voice-leading
  analysis. The library is BSD-licensed, but bundled corpus content has separate
  rights considerations.
- [OR-Tools CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver)
  documents integer-only constraint models and feasible/optimal/infeasible
  outcomes. It is an optional voicing solver, not the first implementation.
- [FastAPI background-task caveat](https://fastapi.tiangolo.com/tutorial/background-tasks/)
  recommends larger tools such as Celery for heavy computation across processes
  or servers.
- [Celery 5.6 introduction](https://docs.celeryq.dev/en/stable/getting-started/introduction.html)
  describes broker-mediated task distribution and horizontal worker scaling.
- [PostgreSQL JSON types](https://www.postgresql.org/docs/current/datatype-json.html)
  explains `jsonb` processing/indexing advantages and row-lock implications for
  large documents. BandForge stores immutable snapshots rather than mutating
  deep fields in place.
- [MDN Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
  documents one-way reconnectable browser event streams and connection limits.
- [OpenAPI specification](https://spec.openapis.org/oas/latest.html) is the API
  contract standard used for server/client/schema verification.

## Generation Research and Libraries

- [MMM: Exploring Conditional Multi-Track Music Generation with the Transformer](https://arxiv.org/abs/2008.06048)
  motivates explicit per-track/bar representations and controllable inpainting.
- [Versatile Multi-Track Music Arrangement](https://arxiv.org/abs/2408.15176)
  researches sequence-to-sequence fine-tuning for band arrangement and related
  tasks.
- [MuPT](https://arxiv.org/abs/2404.06393) highlights synchronized multitrack
  representation as a response to cross-track measure alignment problems.
- [MusPy metrics](https://muspy.readthedocs.io/en/stable/metrics.html) documents
  pitch/rhythm metrics including scale consistency, entropy, polyphony, empty
  beats, drum patterns, and groove consistency, while framing them as
  distributional evaluation tools.
- [pretty_midi documentation](https://craffel.github.io/pretty-midi/) and
  [Mido documentation](https://mido.readthedocs.io/en/stable/) are candidate
  MIDI adapters.
- [Magenta note-seq](https://github.com/magenta/note-seq) documents conversion,
  quantization, extraction, and training representations, but the repository was
  archived on 2026-05-06 and warns of changed MIDI tick limits that can amplify
  corrupt-file memory risk. It is research reference, not a core dependency.

## Dataset Candidates

- [Groove MIDI Dataset](https://magenta.tensorflow.org/datasets/groove): 13.6
  hours of expressive, tempo-aligned drum MIDI/audio under CC BY 4.0.
- [Slakh2100](https://www.slakh.com/): 2,100 synthesized multitrack mixtures
  with aligned MIDI, 34 instrument classes, CC BY 4.0, and documented duplicates
  that preprocessing must address.
- [POP909 repository](https://github.com/music-x-lab/POP909-Dataset) and
  [paper](https://arxiv.org/abs/2008.07142): MIDI melody, bridge, piano, and
  chord/beat/key annotations for arrangement research. The repository's MIT
  software/data notice does not remove the need to review rights in underlying
  songs before commercial model training.
- [MAESTRO](https://magenta.withgoogle.com/maestro-wave2midi2wave): aligned
  virtuoso piano MIDI/audio under a noncommercial share-alike license; useful
  for research but excluded from a commercial BandForge model by default.
- [Creative Commons BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/)
  summarizes reuse and attribution obligations. Review legal code and other
  rights for each dataset.

## Input, Metadata, and OMR

- [Audiveris Handbook](https://audiveris.github.io/audiveris/_pages/handbook/)
  describes printed common-Western-notation OMR to MusicXML, imperfect accuracy,
  manual correction, and AGPL licensing. This supports an optional reviewed
  adapter, not an MVP dependency.
- [Spotify search API](https://developer.spotify.com/documentation/web-api/reference/search)
  provides catalog metadata and currently states Spotify content may not be used
  to train an ML/AI model. It does not provide chord charts.
- [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API) provides music
  metadata, requires a meaningful User-Agent, and currently limits ordinary
  clients to an average of one request per second per IP unless agreed otherwise.

## Security and Rights

- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
  supports extension/type/signature validation, random names, size limits,
  authorization, segregated storage, scanning, and defense in depth.
- [U.S. Copyright Office musical composition deposit guidance](https://www.copyright.gov/register/pa-deposit-music.html)
  recognizes lead sheets/sheet music as representations of musical compositions.
- [U.S. Copyright Office circular index](https://www.copyright.gov/circs/index.html)
  links current guidance on musical compositions, sound recordings, and
  licensing. Rights conclusions require legal review, not an engineering doc.

## Research Conclusions

1. Use MusicXML and MIDI as open interchange formats while retaining a richer
   versioned canonical document.
2. Use browser notation/playback for fast review, not production audio.
3. Separate creative generation from deterministic validation and artifact
   validation.
4. Begin with hierarchical rules/retrieval and add a conditional multitrack
   model behind stable interfaces only after evaluation exists.
5. Treat OMR as a human-corrected import assistant.
6. Treat song services as metadata only and dataset rights as a release gate.
7. Use durable asynchronous jobs for expensive music processing.

