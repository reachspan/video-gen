# Prompt language — how a prompt is written

Reference for the language a video prompt is written in: which register a constraint
belongs to, what blocks a prompt has, how a timeline is written, and the rules that come
from what these models do. What goes wrong on screen is in `pitfalls.md`.

## Three registers

Every constraint fixes one of three things. Two are safe to write.

| register | fixes | use |
|---|---|---|
| identity | what a thing **is** — one continuous strand, the same tool, three people | lock it hard |
| relation | how things **stand to each other** — what holds what, what is within reach | the target |
| pose | where a thing **sits at each instant** | never |

Identity and relation each admit a family of configurations, and motion survives inside a
family. A pose admits one configuration, so the model spends its motion budget holding it
and the shot goes dead.

Pair every lock with the motion that continues through it:

- the strand keeps its route and its count while the hands fidget inside it
- the tool stays the same tool at the same distance while the hand drifts and re-grips

This applies to the figure at the frame edge and to the hand that only holds something. A
frozen extra reads as badly as a frozen speaker and is easier to write by accident.

**Geometry is a bound, never a target.** "No deeper than a fifth of the frame width"
admits a family. "A fifth of the frame width in" admits one. Anchor a bound to something
already in the frame — "no larger than his hand" — because size and reach are judged
against a body. A relation beats both: "close enough that he would have to lean away from
it" survives being obeyed.

## Turning a defect into a fix

A defect report describes appearance, because appearance is what a reader verifies.
`pitfalls.md` gives the tell for a contactless hold as "no fingertip flattening, no skin
blanching, no dark contact line". Those are evidence of a relation, not the relation.

Copy that wording into a prompt and you have written a pose. Write the relation — the
fingers close on it, it takes their weight — and the evidence follows.

**A fix must not outweigh what it fixes.** The model follows the longest and most
emphatic instruction in a block. A paragraph on how the fingers curl beats one clause
saying the wrists are held together, and the element is lost while every word of it is
still on the page. Coverage still passes: it counts words present, not words that won.
Keep a fix shorter than the invariant it sits under, or restate the invariant above it.

## Rules from model behaviour

- **Quote the spoken line.** A described line returns gibberish with the prosody of
  speech, lip-synced confidently. Given the exact sentence, the model says it. Transcribe
  as spoken and keep the broken grammar, the wrong tense, the odd word order; correcting
  them costs the performance. Script it in AUDIO and place it in TIMELINE at the clock
  reference where it starts. Where captions and audio disagree, follow the audio — the
  caption is post.
- **Negatives go inline.** No Seedance endpoint accepts `negative_prompt`.
- **State counts.** Dialogue scenes attract onlookers, and removing them from a start
  frame does not stop it. "Exactly two other people, and no more."
- **Negate the push-in.** It is a default and stops for nothing else.
- **Name the involuntary movement**: breathing that creases the shirt, blinks, a swallow,
  a weight shift. Ask it of everyone in frame, or the extras go still between scripted
  beats.
- **Ask for unretouched skin.** The beauty prior applies to video as well as stills.
- **Forbid in-frame text and logos.** Any glyph comes back garbled, and a wrong wordmark
  reads as fake faster than a blank surface.

## Blocks

In this order. Each answers one question and repeats nothing.

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
    TIMELINE          one line per change, with a clock reference

## Timeline

The blocks above state what holds for the whole take. Anything that changes needs a time,
or the model picks one state and holds it for the duration.

    TIMELINE
    0.0-0.6  <track>: state at the top of the take
    0.6      <track>: what changes, and in which direction
    0.6-1.8  <track>: the state it holds through the next beat
    1.8      <track>: the next change

**Say what holds, not only what moves.** A timeline of changes alone reads as permission
to change everything unlisted. Close it with what must be identical at the first frame
and the last — the wrap, the count, the shot size, who holds what.

**Time the transitions, not the instants.** Give the moment a thing starts, changes or
reverses; leave the state between them free. A pose per instant is the freeze above at
finer resolution.

No endpoint here documents a per-timestamp parameter, so the timeline is prose. Check
before writing it: a multi-prompt or per-segment input turns it from persuasion into
instruction.
