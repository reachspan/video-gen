# Minesweeping a clip

How to read the sweep artifacts, and why they cover the whole clip. This is the
reference; **`prompts/judge.md` is the entry point** and owns the procedure — what
to run, who runs it, and how the answers combine.

    python tools/sweep.py plan   out.mp4 ref.mp4    # the checklist for this clip
    python tools/sweep.py strips out.mp4 sweep/     # temporal coverage
    python tools/sweep.py tiles  out.mp4 sweep/     # spatial coverage
    python tools/vq.py measure   ref.mp4 out.mp4    # where to look first

`plan.md` ends with **work packages**: pitfalls bundled by the artifact they need,
one fresh agent each, run in parallel. The bundling is what makes them independent
— no two packages open the same evidence, so none blocks another.

## The problem this solves

An inspection that jumps to whatever looks suspicious keeps missing the same
things, and cannot say what it skipped. Two limits make it hard to be exhaustive:

- **A clip has too many frames to look at.** Scrubbing finds what happens to catch
  the eye at the moment you pause.
- **A full frame arrives downscaled.** Text, logos, fingers and contact shadows are
  below the resolution at which a whole 720x1280 frame reaches a model, which is
  how a defect gets missed and equally how one gets invented.

So the clip is converted into a bounded set of views with a coverage property that
can be stated plainly.

## Temporal coverage: slit-scans

A slit-scan takes one row or column of pixels from **every** frame and stacks them
along a time axis, so the whole clip becomes a single image. No frame is sampled
away. `sweep.py strips` writes five row positions and five column positions.

Motion becomes shape, which is what makes it useful:

| what you see | what it means |
|---|---|
| an edge that wavers continuously | a living body — breathing, micro-corrections |
| a dead straight horizontal line | that region never moved: `T1`, `T2`, `T3` |
| a slow wander with occasional steps | a hand holding a camera: `T11` |
| a perfectly even band | auto-exposure never ran: `T13` |
| vertical striping | per-frame flicker rather than continuous motion |
| an abrupt vertical discontinuity | a cut, or a regeneration seam |

Read the strips against the reference's strips, never alone. A static background
draws straight lines legitimately; it is the **subject** whose boundaries must
waver.

## Spatial coverage: 4x tiles

`sweep.py tiles` cuts each sampled frame into a 6x4 grid and writes every tile at
4x. Every pixel lands in exactly one tile, and the grid is the same one `vq.py`
scores, so a `permanence_hotspots` entry names the tile to open.

Anything you cannot resolve at 4x is **"cannot tell"**, never "fine". A defect
claimed from a whole-frame view is a hypothesis until it survives its tile.

## What the metrics are for

They point; they do not decide. `vq.py measure` says *where* and *when* something
is unusual relative to the reference, and the verdict is made by looking:

| output | directs attention to |
|---|---|
| `permanence_hotspots` | the exact `(frame, tile)` and pixel box to crop |
| `motion_by_block` | start / middle / end, so `T8` tail collapse is visible |
| `subject_stillness`, `subject_vs_background` | whether the subject ever goes dead |
| `warnings` | when a number should not be trusted at all |

None of them separates generated footage from real on its own — measured against
real phone video, a generated clip sits inside the real range on every one. A
quiet metric is not a pass, and a metric that fires is a place to look. False
positives are the acceptable direction; a metric that fires on everything is
noise and should be cut.

## Rules for whoever is looking

- **Record a verdict for every item, including the ones you cleared.** An item with
  no verdict has not been swept, and that is the difference between an exhaustive
  pass and an opportunistic one.
- Three outcomes per item — `defect`, `clear`, `cannot tell`. The third is a real
  answer; reporting it is what keeps the second honest.
- Look at the strips before the tiles. They are cheap and they cover the whole
  duration, so they tell you where in time to spend the expensive attention.
- Inspect the last block before the first. Degradation is end-loaded.
- Open the tiles as written. They are already at 4x; re-cropping the full frame
  reintroduces the downscaling the sweep exists to avoid.

`prompts/judge.md` covers dispatching the packages and consolidating what comes
back.
