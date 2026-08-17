# compile — turning a reference video into a recreatable spec

Watch a reference clip and produce two artifacts:

    targets/<code>.intent.json    what the shot MEANS and which parts are load-bearing
    targets/<code>.v<n>.txt       the prompt that recreates it

The spec exists so that a change — swapping the character, moving the setting,
altering a prop — can be made without silently destroying the thing that made the
original work. The prompt is disposable; the spec is not.

`targets/` is gitignored. These are working files, not published output.

## 1. Say what happens

Before measuring anything, watch the clip and write down in plain language:

- **The plot.** What happens, in order. Who does what, and what has changed by the end.
- **The format.** What kind of video this is, the genre it borrows, and what that genre
  normally does.
- **Each person's role** — their part in the plot, not their appearance.
- **What each role implies.** A role carries physical conditions with it — how a person
  is positioned, what is done to them, what they would be holding or wearing. Write those
  expectations down before you have seen them, because they are what every later
  observation gets checked against.

Then the **premise**: what the video is doing and why it is funny, interesting or
watchable, in one paragraph. And the **mechanism**: the two to four specific devices
that deliver it — a visual pun, a mismatch between what is said and how it is said,
something intruding at the edges, a late reveal.

This comes first because the two instruments fail differently and each is the check on
the other. Reading a plot, a genre, a role or an affect is coarse and robust. Counting
hands, resolving a join, deciding where one object ends and the next begins is precise
and fragile — adjacent things merge into one, a single thing reads as two, and the
mistake looks exactly like an observation. Establish the plot first so the measurements have something
to be tested against; measure afterwards so the plot has something to be corrected by.
Neither settles the spec on its own.

## 2. Inventory and reconstruct

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

### This step is not time-boxed

Every later step is cheap to redo; this one is not. A misread here clears the gate,
generates faithfully, and comes back confirmed by every downstream reader — all of them
check your sentence, not the clip — so it survives a whole production run and costs
every generation in it. Take as long as it takes. Three rules follow.

**Sample every frame, not a few.** For each load-bearing subject, cut its region out of
the whole clip as contact sheets and read them in order, raising `fps` until nothing
changes between adjacent cells:

    ffmpeg -i ref.mp4 -vf "fps=N,crop=W:H:X:Y,scale=400:-1" sheet/f%03d.jpg
    ffmpeg -pattern_type glob -i 'sheet/f*.jpg' -filter_complex tile=3x4 sheet%d.jpg

**Zoom, but know what it cannot do.** 4x is where you start; when a count is in doubt,
crop tighter — 6x, 8x — and look for the *join* a wider crop merges away: two hands read
as one mass, two strands as one strand, two people as one person. Magnification settles
some of these and quietly fails at others, and it will not tell you which. When two
looks disagree, stop zooming and use the step below.

**Count before you describe.** How many hands, fists, strands, tools, people? Numbers
first — a count is falsifiable, a description is not. Then for each: **whose is it, and
what is it attached to?** Trace every limb back to a shoulder or to the edge it enters
from, every strand end to end, every tool to the hand holding it. Anything entering from
an edge belongs to a body you cannot see.

### Reconstruct one track at a time, and run them in parallel

A clip is several things each doing something over time, and the spec is only as good
as its worst-understood one. Reconstruct them as **tracks**, each covering the whole
duration. At minimum one each for:

- **gaze**, per person — where the eyes point, when they move, in which direction, and
  what the lids do
- **gesture** — what hands and bodies do: holds, shifts, regrips, what stays put
- **every load-bearing prop** — its topology, what it is attached to, what changes
- **camera** — framing and distance over time
- **speech**, per person — the words verbatim, with the timestamp each line starts and
  ends. Burned-in captions are a separate track: they are post, and they can differ
  from what was said

One fresh agent per track, cut by **subject** — one person's eyes, one prop, the camera
— never by region. Subjects move: a strand runs across the picture, a limb reaches into
someone else's space, a head drifts with the framing. So crops overlap freely, and a
track follows its subject wherever it goes rather than letting it leave the crop. Two
agents on the same pixels is not waste; they answer different questions and run
concurrently anyway. (`sweep.py` partitions instead, because its packages cover a fixed
set of tiles. A track is not a region.)

Give a track agent no premise and no spec: one told what the shot means hands the
meaning back as an observation.

> You are reconstructing ONE track of a short video: **<TRACK>**. Work only inside the
> crop you are given, and report only what is inside it.
>
> Sample every frame, not a selection. Cut your region out of the whole clip and lay it
> out as contact sheets, raising the rate until nothing changes between adjacent cells:
>
>     ffmpeg -i CLIP -vf "fps=N,crop=W:H:X:Y,scale=400:-1" sheet/f%03d.jpg
>     ffmpeg -pattern_type glob -i 'sheet/f*.jpg' -filter_complex tile=3x4 sheet%d.jpg
>
> Where a count or a join will not resolve, crop tighter and scale harder — 6x, 8x,
> whatever settles it — rather than guessing or giving up. Two things merged into one by
> a wide crop is the failure you are looking for.
>
> Report a **timeline**: the spans this track holds a state, what the state is, and what
> changed at each boundary. Give timestamps. Describe direction and magnitude in the
> picture's own terms — screen-left, downward, a third of the way across the frame — and
> do NOT name what you think something is looking at or reaching for. You cannot see
> outside your crop, and naming the target is the guess that gets copied into the spec.
>
> Return JSON: {track, spans: [{t_start, t_end, state, changed_at_boundary}],
> counts: {...}, unresolved: [...]}

Merge the returns into `tracks`, then resolve targets yourself: one track reporting
where the eyes go plus another reporting who stands there is what identifies who is
being checked. No single track could know it.

### When observations and expectations disagree

Tracks disagree with each other, and your own eyes disagree with themselves at different
magnifications. Do not resolve it by picking a side, and do not assume another look will
help.

**Visual error here is systematic, not noisy.** A misread does not average out with more
samples. It survives magnification, it recurs at every timestamp, and separate readers
reproduce it because they share the failure mode rather than because it is true. So a
second look agreeing with the first confirms very little, and two agents agreeing with
each other confirms little more — they are not independent when they fail the same way.
Repetition launders nothing, and confidence grows with it regardless.

**An observation that contradicts physics or plain sense should be de-weighted, not
re-checked.** If the literal reading requires a person to have one arm, an object to
hold itself up, or an action nobody would perform, the likeliest explanation is that the
observation is wrong — and going back for another look will usually return the same
answer with more conviction attached. Prefer the account that is physically coherent.
Looking again is worth it only when there is a specific reason to think a different view
would resolve it; otherwise it costs time and buys false certainty.

None of which makes observation worthless or reasoning sovereign. Most conflicts dissolve
once you notice that an observation is being over-extended rather than being false: an
accurate description of a *part* can carry a false implication about the whole. Ask what
arrangement would produce both the thing that was seen and a scene that works.

Two checks that usually find it:

- **Count what must exist.** Every person in the shot has two hands and two arms whether
  or not you can see them. An arrangement that leaves one unaccounted for is the wrong
  arrangement, whoever reported it and however often.
- **Follow the literal reading to its consequences.** If those consequences are absurd,
  the reading is the problem, not the world.

If nothing satisfies both, record it in `known_blind_spots` rather than forcing it.
Either way, label how you got there: reasoning belongs in the premise and in `function`,
`what` stays the observation. A conclusion reached by argument is fine and often right;
one reached by argument and then written down as though it were seen is what nothing
downstream can catch.

Record the duration, whether there is a cut, and where the beats fall, into `shot`.
If you are compiling part of a longer reference, put the span in `segment`; a spec
that does not say which seconds it describes cannot be checked against anything.
`shot.beats` is the spine; `tracks` is what each thing is doing against it.

## 3. Classify every element by what it does

For each thing in the frame, record:

| field | what it is for |
|---|---|
| `id` | a handle |
| `what` | what a camera recorded — objects, counts, contacts, whose limb — and no interpretation |
| `function` | **why it is there** — what breaks if it is removed |
| `necessity` | `required` or `preferred` |
| `evidence` | where you saw it, so a later reader can re-check |

`function` is the field that earns its keep. Ask it of every prop: **what is it for?**
A thing in a person's hands is rarely just a thing — it may be a pun, a threat, a tell,
or genuine busywork, and those demand different prompts. Busywork can be swapped for
anything; a pun cannot be touched.

It also survives edits that `what` does not. A constraint added later for an
unrelated reason — identity safety, a length trim — can delete a required element,
and nothing downstream will notice because every other check measures pixels rather
than meaning. Write the function so the deletion is obviously wrong.

Also record:

- `performance.affect` and `performance.forbidden_affect` — affect is load-bearing.
  A pleasant delivery can destroy a premise even with every object present.
- `composition.shot_size`, `subject_share`, `composition.forbidden` — note *why* a
  forbidden framing breaks it, not just that it does.
- `must_be_true` — statements a naive viewer should be able to confirm from the
  finished clip. These are what the blind readers in `judge.md` are checking. For
  each required prop, at least one has to say how the thing **works** — what it is
  doing, what would happen if it were let go — and not merely that it is there. A
  presence claim is satisfied by an object that is present and inert, which is the
  failure this spec exists to catch.
- `forbidden_assertions` — sentences the prompt must never contain.

### The file

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
  "tracks": {
    "gaze": [{"t": "0.0-0.6", "state": "<direction, lids>", "changed_at": "<what moved>"}],
    "gesture": [{"t": "...", "state": "...", "changed_at": "..."}],
    "<prop-id>": [{"t": "...", "state": "...", "changed_at": "..."}],
    "camera": [{"t": "...", "state": "...", "changed_at": "..."}]
  },
  "elements": [
    {"id": "<short-handle>",
     "what": "<what a camera recorded: objects, counts, contacts, whose limb. No reading.>",
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

### Traps

Four ways to write a spec that passes everything and checks nothing.

**A blunt negation can delete a required element.** Suppressing the model's habit of
adding onlookers needs the prompt to say there are no *additional* people — which a
crude "no other people in frame" cannot distinguish from deleting the two who belong
there. Nor is the collision limited to counting: any instruction that *tightens* — a
closer shot size, a push-in, a tidier background — can drop an element at the frame
edge, and G2 will not notice, because the element is still named in the prompt while
no longer being in the shot the prompt describes. Keep assertions narrow and literal,
let element coverage enforce presence, and record the coupling beside the assertion.

**`what` must not be a prompt sentence.** G2 scores stem-token overlap between each
element's `what` and the prompt. Author both in one pass and it passes by construction,
having checked nothing. Describe the thing to someone who has not seen the video, then
write the prompt separately.

**`what` must not carry the reading.** `what` is the observation, `function` is the
reading. A `what` that states what something *reads as* rather than what it is cannot be
checked against the video by anybody, including you, because the sentence is true of the
reading rather than of the picture.

**Affect is invisible to the gates.** G4 checks only `forbidden_affect`; nothing
verifies that `performance.affect` reached the prompt. Where affect *is* the joke,
record it as a `required` element too — the only way coverage sees it.

## 4. Red-team the spec

Compiling is one person reading one video once. Before writing a prompt, hand the
spec's observations to a fresh agent and ask it to knock them down.

Pull the `what` fields out of `elements[]` with their ids and list them as numbered
claims. Send the observations only — strip anything interpretive, because a claim that
cannot be falsified from the picture is not worth sending. Give the agent the
reference's tiles and strips, the payload below, and **nothing else**: not the premise,
not the mechanism, not the prompt. The premise is exactly what makes a wrong reading
feel obvious, and a reader who has it will confirm whatever the spec says.

> You are checking a written description of a short video against the video itself.
> The description was written by someone who watched it once. It may be wrong. Your
> job is to find where.
>
> You have the video's tiles and strips. The tiles are already at 4x — start there
> rather than re-cropping a whole frame. Check every claim across the whole run of
> frames rather than at a few timestamps, and where a count or a join is in question,
> crop tighter and scale harder — 6x, 8x, whatever settles it — instead of guessing or
> giving up. Two things merged into one by a wide crop is the failure you are looking
> for.
>
> Below is a numbered list of claims about what is in the picture. Take each one and
> **try to prove it false.** Default to `contradicted` when the picture does not
> plainly support it. Three verdicts only:
>
> - `confirmed` — the picture plainly shows this
> - `contradicted` — the picture shows something else; say what it actually shows
> - `not_visible` — will not resolve even after cropping tighter and scaling harder.
>   A real answer, and expected
>
> Flag separately any claim that the picture seems to support but that could not be true
> of a real scene — a body that would need an extra limb, an object nothing is holding up,
> an action that would accomplish nothing. Say what makes it impossible. A claim can look
> right in every frame and still be incoherent, and that is worth more than another look.
>
> Then, separately and in your own words: **for every hand and arm in the picture, say
> whose body it belongs to and how you can tell.** Anything entering from a frame edge
> belongs to someone you cannot see. Then list anything else you can see that no claim
> mentions and that looks like it might matter — an object, a connection between two
> things, a person, a contact.
>
> Return JSON: {claims: [{id, verdict, what_the_picture_shows, where: [{frame, tile}]}],
> limbs: [{which, belongs_to, how_you_can_tell, where: [{frame, tile}]}],
> unlisted: [{what, why_it_might_matter, where: [{frame, tile}]}]}

Every `contradicted` goes back into the spec before a prompt is written, and so does
anything in `limbs` or `unlisted` that turns out to carry meaning. Resolve
`not_visible` on a required element too: something no one can make out at 4x is not
something a viewer is going to read.

Run this again after any change to `elements[]`, and treat a disagreement as the
spec's problem until the picture says otherwise. The whole value of the step is that
it has not read your premise; arguing it round to your reading throws that away.

## 5. Write the prompt

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
    AUDIO             who speaks, the exact words they say, and that nobody narrates

Rules that come from what the models actually do:

- **Quote the spoken line, never describe it.** Describing it does not get you a
  paraphrase, it gets you gibberish — syllables with the prosody of speech and no words
  in them, lip-synced confidently. Given the exact sentence, the model says it.
  Transcribe as spoken and keep the broken grammar, the wrong tense and the odd word
  order; correcting them costs the performance. Script in AUDIO, each line in the
  TIMELINE at the clock reference where it starts. Where captions and audio disagree,
  follow what is said — the caption is post.
- **Negatives go inline.** No Seedance endpoint accepts `negative_prompt`.
- **State counts explicitly.** Dialogue scenes attract extra onlookers, and removing
  them from a start frame does not stop it. "Exactly two other people, and no more."
- **Negate the drifty push-in.** It is a default and does not stop on its own.
- **Ask for involuntary movement** by name: breathing that creases the shirt, blinks,
  a swallow, a weight shift. Ask it of everyone in frame rather than only whoever is
  speaking, or they all go still between scripted beats.
- **Ask for unretouched skin.** The beauty prior applies to video as well as stills.
- **Forbid in-frame text and logos.** Any glyph will be reproduced garbled, and a
  wrong wordmark on an otherwise convincing object reads as fake faster than a
  blank one.

### Constrain what a thing is, not where it sits

Every constraint falls into one of three registers, and only two of them are safe to
write:

| register | what it fixes | write it? |
|---|---|---|
| identity | what the thing **is** — one continuous strand, the same tool, three people | yes, lock it hard |
| relation | how things **stand to each other** — what holds what, what is within reach | yes, this is the target |
| pose | where a thing **sits at each instant** | never |

A pose constraint is satisfiable by exactly one configuration, so the model spends its
whole motion budget holding it and the thing goes dead. Identity and relation each admit
a *family* of configurations, and movement survives inside a family. So pair every lock
with the motion that has to continue through it: a strand keeps its route and its count
while the hands fidget inside it; a tool stays the same tool at the same distance while
the hand holding it drifts and re-grips. This applies to whatever you were not thinking
about — a figure at the frame edge, a hand that only holds something — where the freeze
reads exactly as badly and is easier to write by accident.

**Geometry is a bound, never a target.** A measured figure is safe as a limit and
dangerous as a value: "no deeper than a fifth of the frame width" admits a family,
while "a fifth of the frame width in" admits one, and one is a pose. Anchor the bound
to something already in the frame rather than to an absolute — "no larger than his
hand, entering only at the frame edge" — since size and reach are judged against a
body, and naming the object alone fixes neither. Prefer the relation to either:
"close enough that he would have to lean away from it" survives being obeyed.

### Write the timeline, not only the state

The blocks above describe what is true for the whole take. Anything that **changes**
needs a time, or the model picks one state and holds it for the duration.

So add a TIMELINE block, written from `tracks`. One line per change, with a clock
reference and the track it belongs to:

    TIMELINE
    0.0-0.6  <track>: state at the top of the take
    0.6      <track>: what changes, and in which direction
    0.6-1.8  <track>: the state it holds through the next beat
    1.8      <track>: the next change
    ...     one line per change, each naming its track and its clock reference

Two rules for it:

**Say what holds, not only what moves.** A timeline listing only changes reads as
permission to change everything unlisted. Close it with the things that must be
identical at the first frame and the last — the wrap, the count, the shot size, who is
holding what.

**Do not write a pose per instant** — that is the freeze above at finer resolution.
Time the *transitions*: when a thing starts, when it changes, which direction it goes.
Leave the state between them free.

No endpoint here documents a per-timestamp parameter, so the timeline is prose. Check
before writing it anyway: a multi-prompt or per-segment input turns it from persuasion
into instruction.

## 6. Swaps and changes

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

## 7. Gate before generating

    python tools/gate.py targets/X.intent.json targets/X.v4.txt

`G2` checks that every required element survived into the prompt; `G3` and `G4` check
that no clause contradicts the premise, the affect or the composition. It is free and
it catches the class of failure that costs a whole generation.

Iterate until it passes. Then hand off to `judge.md`, which owns everything from
generation onward.
