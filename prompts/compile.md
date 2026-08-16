# compile — turning a reference video into a recreatable spec

Watch a reference clip and produce two artifacts:

    targets/<code>.intent.json    what the shot MEANS and which parts are load-bearing
    targets/<code>.v<n>.txt       the prompt that recreates it

The spec exists so that a change — swapping the character, moving the setting,
altering a prop — can be made without silently destroying the thing that made the
original work. The prompt is disposable; the spec is not.

`targets/` is gitignored. These are working files, not published output.

## 1. Inventory the reference

Look before writing. The sweep tools work on a reference just as well as on a
candidate, and they are the cheapest way to see everything that is actually there:

    python tools/sweep.py strips ref.mp4 refsweep/    # blocking and motion over time
    python tools/sweep.py tiles  ref.mp4 refsweep/    # every region at 4x
    python tools/sweep.py plan   ref.mp4              # what the tiles and strips are

The tiles matter most. Set dressing, edge intrusions and props are exactly what gets
missed on a casual watch and exactly what carries the meaning. They are written as a
6-row by 4-column grid named `f<frame>_t<row><col>`, so **the frame edges are column
0 and column 3, and rows 0 and 5** — open those deliberately. Things cropped by the
frame are easy to overlook and are often doing the work.

Record the duration, whether there is a cut, and where the beats fall, into `shot`.
If you are compiling part of a longer reference, put the span in `segment`; a spec
that does not say which seconds it describes cannot be checked against anything.

Then ask of every prop: **what is it for?** A thing in a person's hands is rarely
just a thing. It may be a pun, a threat, a tell, or genuine busywork, and those
demand different prompts — busywork can be swapped for anything, a pun cannot be
touched. Getting this wrong is the failure mode that survives every downstream check,
because the object will be present and correct and mean nothing.

## 2. Find the premise before listing anything

**Write down what the video is doing and why it is funny, interesting or watchable,
in one paragraph, before you inventory a single element.** A list of objects
assembled without the premise produces a prompt that reproduces the furniture and
loses the point — a clip can contain every element and mean nothing.

Then write the **mechanism**: the two to four specific devices that deliver the
premise. Not "it is funny" but *how* — a visual pun, a mismatch between what is said
and how it is said, something intruding at the edges, a late reveal.

## 3. Classify every element by what it does

For each thing in the frame, record:

| field | what it is for |
|---|---|
| `id` | a handle |
| `what` | plain description, the words you would use in a prompt |
| `function` | **why it is there** — what breaks if it is removed |
| `necessity` | `required` or `preferred` |
| `evidence` | where you saw it, so a later reader can re-check |

`function` is the field that earns its keep. A constraint added later for an
unrelated reason — identity safety, a length trim — can delete a required element,
and nothing downstream will notice because every other check measures pixels rather
than meaning. Write the function so the deletion is obviously wrong.

Also record:

- `performance.affect` and `performance.forbidden_affect` — affect is load-bearing.
  A pleasant delivery can destroy a premise even with every object present.
- `composition.shot_size`, `subject_share`, `composition.forbidden` — note *why* a
  forbidden framing breaks it, not just that it does.
- `must_be_true` — statements a naive viewer should be able to confirm from the
  finished clip. These are what the blind judges in `judge.md` are checking.
- `forbidden_assertions` — sentences the prompt must never contain.

### A trap in `forbidden_assertions`

Do not add a blunt negation that collides with a required element. Suppressing the
model's habit of adding extra people requires the prompt to say there are no
additional people — which a crude "no other people in frame" rule cannot distinguish
from deleting the two people who are supposed to be there. Keep forbidden assertions
narrow and literal, and let element coverage enforce presence.

The collision is not limited to counting people. Any instruction that *tightens* —
a closer shot size, a push-in, a tidier background — can delete an element at the
frame edge as a side effect, and G2 will not notice, because the element is still
named in the prompt while no longer being in the shot the prompt describes. Record
that reasoning next to the assertion so a later editor sees the coupling.

### Real brands, and names spoken aloud

If the reference carries a real company's trade dress, or a real name is spoken, it
is doing one of two jobs: it is incidental, or it is what the premise is about.

- **Incidental** — strip it. Ask for unbranded, worn equipment and plain garments. A
  wrong wordmark reads as fake faster than no wordmark.
- **Load-bearing** — genericise rather than reproduce. Keep the shape of the line and
  swap the name. A recreation puts a real, named organisation inside a premise its
  owner never agreed to, which is a claim about them rather than a recreation of a
  shot, and it is worth neither the exposure nor the argument.

Record which call you made and why in the spec; it is a semantic edit to the
reference and the next person needs to know it was deliberate.

## 3a. The file

`gate.py` hard-requires `elements[]`, `forbidden_assertions`, `performance`
and `composition`. Everything else is for the human reader and for whoever revises
this later. `targets/` is gitignored, so there is no example in the repo to copy —
this is the shape:

```json
{
  "source": "<shortcode or filename>",
  "segment": "0.0-4.0s",
  "premise": "<one paragraph: what this is doing and why it works>",
  "mechanism": ["<the specific devices that deliver the premise>"],
  "shot": {"duration_s": 4.0, "cut_count": 0, "beats": ["0.7-1.0s pause"]},
  "elements": [
    {"id": "cable-coil",
     "what": "<plain description, in the words you would use to a stranger>",
     "function": "<what breaks if this is removed>",
     "necessity": "required",
     "evidence": "<where you saw it>"}
  ],
  "performance": {
    "affect": "flat, tired, resigned",
    "forbidden_affect": ["cheerful", "relaxed"],
    "note": "<why affect is load-bearing here>"
  },
  "composition": {
    "shot_size": "medium, mid-thigh to just above the head",
    "subject_share": "<fraction of FRAME HEIGHT the subject spans>",
    "forbidden": ["wide shot"],
    "note": "<why a forbidden framing breaks it>"
  },
  "must_be_true": ["<what a naive viewer should be able to confirm>"],
  "forbidden_assertions": ["<sentences the prompt must never contain>"],
  "known_blind_spots": ["<what this spec cannot check>"]
}
```

### Do not write `what` as a prompt sentence

G2 scores stem-token overlap between each element's `what` and the prompt. If you
author both in one pass, phrasing the `what` the way you intend to phrase the prompt,
it passes by construction and has checked nothing. **Write `what` as you would
describe the thing to someone who has not seen the video**, then write the prompt
separately. A gate that passes on prose written to satisfy it is not evidence.

### Affect is not covered by any gate

G4 checks only `forbidden_affect`. Nothing verifies that `performance.affect`
survived into the prompt, so on a clip where the affect *is* the joke, also record it
as a `required` element — that is the only way the coverage check sees it.

## 4. Write the prompt

Blocks, in this order. Each answers one question and repeats nothing:

    GLOBAL STYLE      what kind of footage this is, and everything it is NOT
    REFERENCES        which reference supplies what, and what NOT to take from it
    PREMISE           the point of the shot, stated as the point
    CHARACTER         identity, pinned to a reference image
    EDGE / SECONDARY  anything intruding, with its exact count
    PROP AND HANDS    grip, contact, size, and that it does not change
    FRAMING           shot size, subject placement, and a stillness lock
    PERFORMANCE       affect, and the involuntary movement that sells it
    LOCATION          the room, including incidental ugliness
    LIGHTING          sources, direction, and what blows out
    CAMERA            how it is held and what it must not do
    TEXT AND BRANDING what carries no writing, and what is unbranded
    AUDIO             who speaks, and that nobody narrates

Rules that come from what the models actually do:

- **Negatives go inline.** No Seedance endpoint accepts `negative_prompt`.
- **State counts explicitly.** Dialogue scenes attract extra onlookers, and removing
  them from a start frame does not stop it. "Exactly two other people, and no more."
- **Lock what must not change** across the take — the grip, the shot size, the seated
  position. Drifty push-in is a default and has to be negated.
- **Ask for involuntary movement** by name: breathing that creases the shirt, blinks,
  a swallow, a weight shift. Otherwise the subject goes still between scripted beats.
- **Ask for unretouched skin.** The beauty prior applies to video as well as stills.
- **Forbid in-frame text and logos.** Any glyph will be reproduced garbled, and a
  wrong wordmark on an otherwise convincing object reads as fake faster than a
  blank one.
- **Anchor scale and reach to something in frame.** An object at the wrong size
  against a body is spotted instantly, and one that intrudes further than intended
  changes the shot. Naming the object alone fixes neither; tie it to a landmark —
  "no larger than his hand, entering only at the frame edge".

## 5. Swaps and changes

### Swapping the character

Generate the new identity with `face-gen.md`, then split the references explicitly:

> @Image 1 is the man. @Video 1 is the camera and the room. Take the face, head,
> build, skin and shirt from @Image 1 and keep them exactly. Take ONLY the camera
> behaviour, shot size, subject distance and exposure from @Video 1 — do NOT take the
> person from @Video 1, and do NOT copy any logo, badge or printed mark from it.

Without that second half the original performer leaks back in.

### When to reach for an image instead of text

Generate a reference image whenever the thing is easier to *show* than to describe,
and feed it in as an additional reference:

- a prop whose exact geometry matters, or which must be unbranded and worn
- a spatial arrangement — who is where, what is cropped by which edge
- a costume or a specific material
- anything you have already failed to get right in text twice

Stills are cheap relative to video. A round of image iteration costs a fraction of
one video generation and removes an ambiguity that would otherwise be re-rolled on
every attempt.

### Other user changes

Apply the change to the **spec first**, then regenerate the prompt from it. If the
change contradicts a `required` element's `function`, say so plainly and ask — that
is the case the spec exists to catch. A change to the setting or the wardrobe is
usually free; a change to the mechanism is a different video.

## 6. Gate before generating

    python tools/gate.py targets/X.intent.json targets/X.v4.txt

`G2` checks that every required element survived into the prompt; `G3` and `G4` check
that no clause contradicts the premise, the affect or the composition. It is free and
it catches the class of failure that costs a whole generation.

Iterate until it passes. Then hand off to `judge.md`, which owns everything from
generation onward.
