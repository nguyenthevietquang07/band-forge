# Input and User Experience Design

## 1. Input Principle

Ask "What do you have?" rather than forcing every musician into one form. Every
path converges on the same reviewable source revision and canonical measure grid.
The UI must distinguish imported facts, inferred values, defaults, and unresolved
content.

## 2. Source Types and Trust

| Source | Musical value | Initial confidence behavior | MVP treatment |
|---|---|---|---|
| Structured form/grid | highest | user-authored, explicit | fully supported |
| ChordPro/text chart | high after parse | flag unknown chords/sections | fully supported |
| MusicXML | high for notation | validate schema, preserve unsupported features | import supported after structured MVP |
| MIDI | timing/notes, weak notation semantics | infer tracks/grid with visible confidence | import supported after MusicXML |
| PDF/image lead sheet | visual reference, uncertain machine parse | original visible; extracted fields need approval | upload/preview first, OMR later |
| Song title/artist | metadata only | never harmony-complete | optional metadata search |

The generation button remains disabled until form and harmonic timeline are
approved. The UI explains the missing musical information in plain language.

## 3. Workspace Layout

Desktop uses three persistent regions:

```text
+----------------------+---------------------------+--------------------------+
| SOURCE               | ARRANGEMENT BUILDER       | LIVE REVIEW              |
| upload / text / grid | key tempo style band      | chart / score / warnings |
| parse confidence     | sections roles difficulty | playback cursor          |
| unresolved items     | locks generate modes      | candidate comparison     |
+----------------------+---------------------------+--------------------------+
```

- Source is where the user resolves what the song *is*.
- Arrangement Builder is where the user decides how this band will play it.
- Live Review is where the user sees and hears the current candidate.

Panels may collapse, but the domain distinction remains. Mobile uses a linear
flow: capture source, approve summary, choose preset, generate, listen/review.

## 4. Source Capture Flow

### Step 1: choose source

Offer large source-type rows with icon, title, and one-line expectation:

- Paste chords or notes
- Build a chart
- Import MusicXML or MIDI
- Upload a PDF or photo

"Find song metadata" is a small optional action after title entry, not the
primary musical input.

### Step 2: parse and normalize

Show the original on the left and normalized form/chords on the right. Each
inferred field has confidence and provenance. Examples:

- green/confirmed: explicit user value or validated structured input;
- amber/review: parser inference or low-confidence OMR;
- red/blocking: unknown chord, incomplete bar, ambiguous repeat;
- gray/default: product assumption such as 4/4 or 120 BPM.

Color is never the sole signal; use icon and label.

### Step 3: approval

Display a compact checklist: title, key, meter, tempo, form, chord timeline,
melody, and rights confirmation. Approval freezes a source revision. Later
corrections create another revision and mark dependent arrangements stale.

## 5. Chord/Text Input Grammar

Support a forgiving subset and normalize into structured values:

```text
{title: Autumn Walk}
{key: G}
{time: 4/4}
{tempo: 104}

[Verse 1 x2]
| G | D/F# | Em7 | Cadd9 |

[Chorus]
| C | D | Bm7 Em7 | Am7 D7 |
```

Rules:

- `|` delimits bars; multiple chords divide the bar evenly unless beat offsets
  are given (`C@1 G@3`);
- section labels use brackets; repeat counts expand in canonical form;
- comments/lyrics are preserved but not interpreted as instructions;
- unknown directives and symbols are preserved and surfaced;
- the parser never silently changes enharmonic spelling or bar count.

ChordPro-compatible imports preserve lyrics and supported environment directives
such as verse, chorus, and bridge. Export should not imply complete compatibility
with every ChordPro implementation until verified by fixtures.

## 6. PDF and Image Flow

The MVP provides secure upload, image/PDF preview, crop/rotate, and manual
side-by-side transcription into the structured editor. This is already useful
for turning a paper lead sheet into a gig packet.

Later OMR flow:

1. normalize image orientation, resolution, and contrast in a sandbox;
2. run a versioned OMR adapter asynchronously;
3. convert output to MusicXML, validate, and normalize;
4. align extracted measures with page bounding boxes;
5. show confidence and original image snippets for review;
6. require explicit approval before generation.

Audiveris can output MusicXML but documents important limits: printed common
Western notation only, imperfect accuracy, and a correction-oriented workflow.
It is AGPL-licensed, so integration/deployment implications require review. The
core product must not depend on OMR success.

## 7. Arrangement Controls

Controls follow musician language:

- key and tempo inputs;
- meter menu;
- style pack and feel segmented controls;
- instrument roster with per-player level;
- density and energy sliders with labeled discrete positions;
- reharmonization amount (`OFF`, `LIGHT`, `COLORFUL`);
- fill policy and solo-space toggles;
- section energy timeline;
- lock icons on harmony, melody, section, bar, and track.

Advanced model parameters remain hidden from ordinary users. "Fresh" is a
musical mode, not a temperature field.

## 8. Candidate Review

Show at most three candidates. The comparison header includes seed label,
validation state, playability by instrument, warning count, and concise musical
differences such as "sparser keys; bass approaches chorus; drums open hats."

Review modes:

- full score;
- chord chart;
- one player part;
- band timeline/role view;
- validation findings;
- side-by-side diff for selected scope.

Clicking a finding selects its bar and track in notation and timeline. Candidate
selection creates a draft; acceptance is a separate deliberate action.

## 9. Playback

Playback is always available after a candidate has a MIDI preview. Controls:

- play/pause and seek;
- count-in and metronome;
- tempo override from 50% to 150% within safe limits;
- mute/solo per track;
- loop selected bars/section;
- master volume and per-track volume;
- score cursor following current measure/beat.

Use browser synthesis/samples for immediacy. Label it a preview mix. Do not spend
the MVP on realistic production audio. The symbolic timeline is authoritative;
the audio scheduler consumes it and reports current tick to the notation cursor.

## 10. Expected UI States

Every major surface implements loading, empty, partial, success, stale, failure,
cancelled, permission-denied, and offline/reconnect behavior. A generation page
refresh reconnects to the job. A stale source or base version blocks acceptance
until the user reviews the dependency change.

## 11. Accessibility

- Full keyboard navigation and visible focus.
- Text labels for icon-only controls and tooltips for unfamiliar music actions.
- Status changes announced through polite live regions, with terminal failures
  assertive when necessary.
- Findings available as a filterable list independent of visual notation.
- Playback does not autoplay.
- Motion/cursor following respects reduced-motion preferences.
- Long chord names and section labels wrap without covering notation controls.

