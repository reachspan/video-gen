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

The tiles matter most. Set dressing, edge intrusions and props are exactly what gets
missed on a casual watch and exactly what carries the meaning. Check the frame edges
deliberately: things cropped by the frame are easy to overlook and are often doing
the work.

Note the duration, the shot size, whether there is a cut, and where the beats fall.

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
  wrong wordmark on real trade dress reads as fake faster than no wordmark at all.
- **Anchor scale to something in frame.** An object at the wrong size relative to a
  head is spotted instantly; "held near his head, no larger than his hand" survives
  where "a drill" does not.

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

Reference images are cheap (2 credits on `nano_banana_pro`). A round of image
iteration costs a fraction of one video generation and removes the ambiguity that
would otherwise be re-rolled on every attempt.

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
