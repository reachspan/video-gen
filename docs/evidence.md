# Evidence — what the artifacts and the metrics show

Reference for reading what `tools/sweep.py` and `tools/vq.py` produce. It explains
what each view covers and what each number means; it does not say what to run, in
what order, or how to decide. That belongs to whoever is driving the check.

Safe to hand to a blind inspector: nothing here says what the clip was supposed to
contain.

    python tools/sweep.py strips CLIP DIR      temporal coverage
    python tools/sweep.py tiles  CLIP DIR      spatial coverage
    python tools/sweep.py plan   CLIP [REF]    the per-pitfall checklist for this clip
    python tools/vq.py   measure REF CAND      distance from the reference

## The problem the artifacts solve

An inspection that jumps to whatever looks suspicious keeps missing the same things,
and cannot say what it skipped. Two limits make exhaustiveness hard:

- **A clip has too many frames to look at.** Scrubbing finds whatever happens to
  catch the eye at the moment you pause.
- **A full frame arrives downscaled.** Text, logos, fingers and contact shadows sit
  below the resolution at which a whole 720×1280 frame reaches a model — which is how
  a defect gets missed, and equally how one gets invented.

So the clip is converted into a bounded set of views whose coverage can be stated
plainly.

## Temporal coverage: slit-scans

A slit-scan takes one row or column of pixels from **every** frame and stacks them
along a time axis, so the whole clip becomes a single image. No frame is sampled
away. `sweep.py strips` writes five row positions and five column positions.

Motion becomes shape, which is what makes it readable:

| what you see | what it means |
|---|---|
| an edge that wavers continuously | a living body — breathing, micro-corrections |
| a dead straight horizontal line | that region never moved: `T1`, `T2`, `T3` |
| a slow wander with occasional steps | a hand holding a camera: `T11` |
| a perfectly even band | auto-exposure never ran: `T13` |
| vertical striping | per-frame flicker rather than continuous motion |
| an abrupt vertical discontinuity | a cut, or a regeneration seam |

A strip is read against the reference's strip or it is read against nothing. A static
background draws straight lines legitimately; it is the **subject** whose boundaries
have to waver.

## Spatial coverage: 4x tiles

`sweep.py tiles` cuts each sampled frame into a 6×4 grid and writes every tile at 4x.
Every pixel lands in exactly one tile, and the grid is the same one `vq.py` scores, so
a `permanence_hotspots` entry names the tile to open. Tiles are named
`f<frame>_t<row><col>`, so the frame edges are columns 0 and 3 and rows 0 and 5.

A few sampled frames would leave a brief defect free to fall between them — a
wordmark that garbles for half a second, a grip that breaks and recovers. So each tile
additionally gets its **own worst moment**, found by scanning every frame and scoring
`|2·f(t) − f(t−k) − f(t+k)|`: steady drift and steady motion cancel, and what survives
is the moment a region stops behaving like itself. Those land as
`odd_t<ij>_f<frame>.jpg`. The number of images stays fixed; the search behind them
covers the whole clip.

**What can still slip through:** a defect that is small, brief, *and* not the most
anomalous moment in its own tile. That makes the coverage bounded, repeatable and
honest about where it looked — not infallible.

## No metric here is a detector

Everything `vq.py` measures was calibrated against 14 real 4s segments from six phone
cameras. **A generated clip lands inside the real range on every one of them.** Real
footage varies more between cameras, scenes, operators and bitrates than generated
footage differs from real.

So a metric that fires is a place to look, and a metric that stays quiet is not a
pass. A clip is not real because it scored well.

Grain **magnitude** is deliberately not measured. It tracks the encoder rather than
the content — the same clip transcoded from 6993 to 651 kbps loses a quarter of it,
and across real footage it correlates with bitrate at r≈0.86 — so a raw generator
output measured against platform-delivered footage would read that difference as
grain. A number that moves with the encoding ladder says nothing about generation
quality.

**Absolute values are not portable.** They move with frame count, sampling offset and
estimator. Pass reference and candidate to one `vq.py measure` run and read the
comparison; only the direction and the ratio between them carry meaning.

**`warnings` comes first.** On a fast-moving camera a large share of alignment steps
get rejected and few background tiles survive the subject mask; the tool says so
rather than returning a confident figure. A metric carrying a warning is not evidence,
and a hotspot on a clip whose alignment mostly failed is not a location. `bg_tiles`
deserves the same scepticism even when it does not warn — a large shortfall against
the reference's count is a reason to distrust every permanence number, not just a low
absolute one.

## What each output points at

| output | directs attention to |
|---|---|
| `permanence_hotspots` | the exact `(frame, tile)` and pixel box to crop |
| `motion_by_block` | start / middle / end, so `T8` tail collapse is visible |
| `subject_stillness`, `subject_vs_background` | whether the subject ever goes dead |
| `ssim_min` | a one-off discontinuity, rather than a gradual drift |
| `warnings` | when a number should not be trusted at all |

Read `permanence_worst_ncc`, not the mean. An object blanked for half a clip moves the
worst-tile figure several hundred percent; the mean only registers wholesale collapse,
needing a ~20px global warp to shift 5%.

A hotspot is a place to look, never a verdict. The subject mask is derived per clip,
but hands and props reaching the frame edges can land outside it, and a moving hand
legitimately scores low.

## What the container carries

Two things sit outside the picture entirely, in the file rather than in the frames.
Neither is a quality measure and neither belongs in a sweep, but a delivered file is
not fully described without them.

**A signed C2PA provenance manifest.** Measured on a real completed job: a ~21KB
`uuid` box at offset 32 of the delivered MP4, carrying `softwareAgent
BytePlus_ModelArk`, the model name, a log id tying the file to a specific generation
request, a tamper-evident hash, an X.509 signature, and `digitalSourceType` set to
the IPTC value `trainedAlgorithmicMedia` — the value platforms auto-label on.

**`ffprobe` and `exiftool` do not parse C2PA boxes**, so both report a clean file.
Byte-scan instead:

    grep -aob 'c2pa' out.mp4 | head        # a low offset means a manifest is present

The manifest is container-bound, not a pixel watermark, so **any** re-encode drops it
— including `post.py`, any concat, and the platform's own ingest transcode. That
makes its removal a side effect of ordinary processing rather than an act, which is
exactly why it is worth knowing where in a chain it dies.

**Encoder fingerprints.** `strings -a out.mp4 | grep -iE 'x264|Lavc|Lavf'` returns
the muxer and the full x264 option string. The x264 record lives in the H.264
bitstream rather than the container, so it survives a remux. This matters if a file
is sent to someone directly; after a platform transcode, container forensics
collapses toward chance regardless of origin.

## Measured axes

Where a generated clip departs from its reference. Useful as **match targets** and as
places to look — not as evidence of fakery.

| axis | observed | metric | what closes the gap |
|---|---|---|---|
| Camera motion | generated moves *more* than this reference (0.45 vs 0.28px median inter-frame), but real footage spans 0.25–10.8px, so magnitude alone says nothing | `displacement_px`, `motion_mean` | `post.py shake` adds only the deficit, so an already-mobile clip is untouched |
| Highlight behaviour | generated clips clip less than this reference | `clip_high_pct`, `clip_low_pct` | prompting does not move it and pushing harder moves it the wrong way; `post.py exposure` does |
| Liveliness | whether the subject ever falls quiet relative to its own typical motion, and how much more it moves than its backdrop | `subject_stillness`, `subject_vs_background` | nothing algorithmic. A subject that goes dead between beats needs regenerating. These aggregates are coarse — the slit-scans are the sensitive instrument, so confirm there first |
| Grain profile shape | `noise_luma_slope` is near-constant per camera: +0.560 ±0.001 across three unrelated segments of one, negative across every segment of another. It survives a 10x bitrate change with a ~10% shift, because normalising by mean noise cancels what the encoder does. Generated reads +0.38 against a +0.56 reference | `noise_luma_slope`, `noise_by_luma` | `post.py grain`. The metric tests whether two clips share a capture pipeline; it does not test whether either is real |
| Object permanence | background tiles drift and morph under motion compensation | `permanence_worst_ncc`, `permanence_hotspots` | shorter clips; fewer background objects; keeping the subject from sweeping across detail |
| Colour permanence | a patch can stay structurally correlated while changing colour | `permanence_chroma_worst` | as above; check the hotspot box by eye before acting |
| Adjacent-frame stability | one-off discontinuities | `ssim_min` | shorter takes; fewer simultaneous moving elements |
