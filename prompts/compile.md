Watch a reference clip and produce two artifacts:

    output/<id>/spec.json         what the shot MEANS and which parts are load-bearing
    output/<id>/prompt.v<n>.txt   the prompt that recreates it

The spec exists so that a change — swapping the character, moving the setting,
altering a prop — can be made without silently destroying the thing that made the
original work. The prompt is disposable; the spec is not.

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

Plot first so a later count can be wrong; count second so the plot can be corrected.
Reading a plot, a genre, a role or an affect is coarse and robust. Counting hands,
resolving a join, deciding where one object ends and the next begins is precise and
fragile — adjacent things merge into one, a single thing reads as two, and the
mistake looks exactly like an observation.

## 2. Inventory and reconstruct

Look before writing. The sweep tools work on a reference just as well as on a
candidate, and they are the cheapest way to see everything that is actually there:

    vg sweep strips ref.mp4 refsweep/    # blocking and motion over time
    vg sweep tiles  ref.mp4 refsweep/    # every region at 4x
    vg sweep plan   ref.mp4              # what the tiles and strips are

The tiles matter most. Set dressing, edge intrusions and props are exactly what gets
missed on a casual watch and exactly what carries the meaning. They are written as a
6-row by 4-column grid named `f<frame>_t<row><col>`, so **the frame edges are column
0 and column 3, and rows 0 and 5** — open those deliberately. Things cropped by the
frame are easy to overlook and are often doing the work.

### This step is not time-boxed

Do not stop early. A misread here clears the gate and is confirmed by every later
reader — they check your sentence, not the clip — so it survives the whole run and
costs every generation in it. Take as long as it takes.

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

### Conflicts

Tracks disagree with each other, and your own eyes disagree with themselves at
different magnifications. Do not resolve it by picking a side, and do not assume
another look will help. The same misread can repeat at every zoom and every reader,
so agreement is not confirmation.

- Prefer the physically possible account. An observation that needs a one-armed
  person, an object holding itself up, or an action nobody would perform is probably
  wrong; looking again usually returns the same answer with more conviction.
- Prefer the account that makes sense given the plot and premise. Pixels that
  contradict what the video is doing are probably a misread of the pixels.
- An accurate part can imply a false whole. Ask what arrangement produces both the
  sighting and a working scene.
- Every person has two hands and two arms whether you can see them.
- If the literal reading's consequences are absurd, the reading is wrong.
- If nothing fits: `known_blind_spots`.
- `what` = observation. `function` / premise = reasoning. Never write a conclusion
  as if it were seen. Downstream cannot catch that.

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
  finished clip. For each required prop, at least one has to say how the thing
  **works** — what it is doing, what would happen if it were let go — and not
  merely that it is there. A presence claim is satisfied by an object that is
  present and inert, which is the failure this spec exists to catch.
- `forbidden_assertions` — sentences the prompt must never contain.

### The file

`gate.py` hard-requires `elements[]`, `forbidden_assertions`, `performance`
and `composition`. Everything else is for the human reader and for whoever revises
this later. There is no example in the repo to copy — this is the shape:

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
edge, and G1 will not notice, because the element is still named in the prompt while
no longer being in the shot the prompt describes. Keep assertions narrow and literal,
let element coverage enforce presence, and record the coupling beside the assertion.

**`what` must not be a prompt sentence.** G1 scores stem-token overlap between each
element's `what` and the prompt. Author both in one pass and it passes by construction,
having checked nothing. Describe the thing to someone who has not seen the video, then
write the prompt separately.

**`what` must not carry the reading.** `what` is the observation, `function` is the
reading. A `what` that states what something *reads as* rather than what it is cannot be
checked against the video by anybody, including you, because the sentence is true of the
reading rather than of the picture.

**Affect is invisible to the gates.** G3 checks only `forbidden_affect`; nothing
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

`docs/prompt-language.md` has the blocks and their order, the register each constraint
belongs in, the rules that come from model behaviour, and how the timeline is written.
Write the prompt from it.

Two things belong to this step rather than to that file:

- **Write the prompt from the spec, in a separate pass.** A `what` field and a prompt
  sentence authored together pass G1 by construction and check nothing (§3, Traps).
- **Every `required` element needs a clause of its own.** G1 measures that coverage, and
  it is the only check that sees an element at all.

## 6. Swaps and changes

### Swapping the character

Apply the new identity to the spec, then rewrite CHARACTER and REFERENCES so the
person comes from the face image and not from the original clip.

### Other user changes

Apply the change to the **spec first**, then regenerate the prompt from it. If the
change contradicts a `required` element's `function`, say so plainly and ask — that
is the case the spec exists to catch. A change to the setting or the wardrobe is
usually free; a change to the mechanism is a different video.

Write the replacement clause in the register `docs/prompt-language.md` names.

## 7. Gate

    vg gate output/<id>/spec.json output/<id>/prompt.v4.txt

`G1` checks that every required element survived into the prompt; `G2` and `G3` check
that no clause contradicts the premise, the affect or the composition.

Iterate until it passes.
