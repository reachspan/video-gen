# Pitfalls — AI video tells, ranked for 9:16 handheld talking-head

Distilled from ~190 researched entries across 8 axes, deduped and filtered to what
matters for **this** format: 4–10s vertical, one seated speaker, held prop, natural
window light, delivered through a platform re-encode.

Severity is **for this format**, not in general.

## No metric here is a detector

Everything measurable in `tools/vq.py` was calibrated against 14 real 4s segments
from six phone cameras. **The generated clip lands inside the real range on every
one of them.** Real footage varies more between cameras, scenes, operators and
bitrates than generated footage differs from real.

Grain **magnitude** is deliberately not measured. It tracks the encoder rather than
the content — the same clip transcoded from 6993 to 651 kbps loses a quarter of it,
and across real footage it correlates with bitrate at r≈0.86 — so a raw generator
output measured against platform-delivered footage reads that difference as grain.
A number that moves with the encoding ladder says nothing about generation quality.

So the signal metrics answer one question — *how far is this candidate from this
particular reference* — and that is what makes them useful for matching, and
useless as a verdict. A clip is not real because it scored well.

The tells below that a **person** can see are the ones that carry weight. Rank
effort accordingly: the human-visible list first, the measurable list last.

Every pitfall here has a sweep procedure that covers the whole clip rather than
whatever caught the eye — `docs/minesweep.md`, driven by `tools/sweep.py`. False
positives are the acceptable direction; a metric that fires on everything is noise
and gets cut.

---

## Tier 1 — human-visible, highest severity

| id | tell | cheapest check |
|---|---|---|
| `T1` | **Statue torso.** Only mouth/head animate; body frozen. Top "AI presenter" signature. | `subject_vs_background`; a column slit-scan draws straight lines where nothing moved |
| `T2` | **No breathing.** Shoulder line holds constant height. | a column slit-scan through the shoulder: count oscillations, expect 12–20/min |
| `T3` | **No physiological jitter.** Head glassy-smooth, no micro-corrections. | `subject_stillness`; a slit-scan through the head during a pause |
| `T4` | **Mask face.** Mouth articulates, upper face static; no brow flash on emphasis. | watch muted: can you tell which word is stressed? |
| `T5` | **Mannequin gaze.** Eyes welded to lens, no counter-rotation on head motion, never reposition. | do the eyes ever move independently of the skull? |
| `T6` | **Thin-prop topology collapse.** Cables re-route between frames, change length, pass through fingers. | trace the prop end-to-end on frames 1 / mid / last |
| `T7` | **Contactless hold.** No fingertip flattening, no deformation, no contact shadow. | zoom 400% on the grip; look for blanching + a dark contact line |
| `T8` | **End-loaded collapse.** Clean early, degrades in the final 1–2s. ~85% clean at 5s vs ~55% at 10s. | `motion_by_block`; inspect the last block *first* |
| `T9` | **Garbled / drifting text.** Any in-frame glyph, and any logo on a real-world object. | zoom 400%, read every string aloud |
| `T10` | **Art-directed background.** Every object legible, relevant, attractively placed; no incidental ugliness. | list objects: would a set dresser have chosen each? |
| `T11` | **Framing too perfect.** Dead-centre, level horizon, no operator error. | plot head position: real drifts then gets corrected |
| `T12` | **Cinema bokeh on a phone framing.** Blur disc >1.5% of frame height is not a phone. | measure a background point highlight |
| `T13` | **AE/WB never move.** Exposure flat for the whole clip. | plot per-frame mean luma; real shows wander + one step response |
| `T14` | **Beauty bias / age flattening.** Ordinary 50-year-old returns as attractive 32. Worst under text-only identity. | 5 seeds side by side: more similar than 5 real people? |
| `T15` | **Object scale and placement.** Held and intruding objects come back oversized and drifted toward frame centre. | measure the object against the head; a cordless drill is ~1 head long |

**`T9` and `T15` are the two that keep landing**, and they land together on the same
object: a held tool comes back oversized, pushed toward frame centre, and wearing a
garbled near-miss of a real trademark. Both are prompt problems — specify tools as
unbranded and worn, and anchor scale to something else in frame, in the same clause.

Neither is detectable by any metric. They are found by reading tiles at 4x, which is
why the sweep exists.

---

## Tier 2 — Seedance-specific defaults (vendor/practitioner reported)

| default | effect here |
|---|---|
| **Stern resting face**; mood adjectives lose | **helps** — our target affect is flat and resigned |
| **Drifty push-in** unless locked | hurts — it's a creep, not handheld jitter |
| **Crowd creep** — dialogue scenes add onlookers; start-frame removal does *not* stop it | specify the count and negate extras |
| **Spontaneous narration** | must negate explicitly |
| **Floaty, overlit look** | a look to fight for its own sake, not because it is detectable |
| **No `seed`, no `negative_prompt`** | zero reproducibility; A/B needs N per arm, not pairs |
| **Dubbing fails on a visible mouth** | audio is locked at generation time |
| **64:1 reject ratio** on real production | the planning number |

---

## Tier 3 — measured differences from the reference

Axes where a generated clip measurably departs from its reference. Useful as
**match targets** and as places to look, not as evidence of fakery.

| axis | observed | check | fix |
|---|---|---|---|
| Camera motion | generated moves *more* than this reference (0.45 vs 0.28px median inter-frame), but real footage spans 0.25–10.8px, so magnitude alone says nothing | `vq.py` → `displacement_px`, `motion_mean` | `post.py shake` adds only the deficit, so an already-mobile clip is untouched |
| Highlight behaviour | generated clips less than this reference | `vq.py` → `clip_high_pct`, `clip_low_pct` | prompting does not move it, and pushing harder moves it the wrong way. `post.py exposure` |
| Liveliness | whether the subject ever falls quiet relative to its own typical motion, and how much more it moves than its backdrop | `vq.py` → `subject_stillness`, `subject_vs_background` | no algorithmic fix; a subject that goes dead between beats needs regenerating. These aggregates are coarse — the slit-scans are the sensitive instrument, so confirm there before acting |
| Grain profile shape | `noise_luma_slope` is near-constant per camera: +0.560 ±0.001 across three unrelated segments of one, negative across every segment of another. It survives a 10x bitrate change with a ~10% shift, because normalising by mean noise cancels what the encoder does. Generated reads +0.38 against a +0.56 reference | `vq.py` → `noise_luma_slope`, `noise_by_luma` | tests whether two clips share a capture pipeline; it does not test whether either is real |
| Object permanence | background tiles drift and morph under motion compensation | `vq.py` → `permanence_worst_ncc`, `permanence_hotspots` | shorter clips; fewer background objects; keep the subject from sweeping across detail |
| Colour permanence | a patch can stay structurally correlated while changing colour | `vq.py` → `permanence_chroma_worst` | same as above; check the hotspot box by eye before acting |
| Adjacent-frame stability | one-off discontinuities show as an `ssim_min` dip | `vq.py` → `ssim_min` | shorter takes; fewer simultaneous moving elements |

Read `permanence_worst_ncc`, not the mean. An object blanked for half a clip moves
the worst-tile figure several hundred percent; the mean only registers wholesale
collapse, needing a ~20px global warp to shift 5%. `permanence_hotspots` names the
worst `(frame, tile)` cells with a pixel box, so a suspect region can be cropped
and looked at instead of merely scored — `sweep.py tiles` writes the same grid.

Check `warnings` before reading any permanence number. On a fast-moving camera a
large share of alignment steps get rejected and few background tiles survive the
subject mask, and the tool says so rather than returning a confident figure.

A hotspot is a place to look, never a verdict. The subject mask is derived per
clip, but hands and props that reach the frame edges can still land outside it,
and a moving hand legitimately scores low. Confirm every hotspot by eye at 4x —
see `docs/minesweep.md`.

**Absolute values are not portable.** They move with frame count, sampling offset and
estimator. Pass reference and candidate to one `vq.py measure` run and read the
comparison; only the direction and ratio between them carry meaning.

---

## Anti-pitfalls — do NOT chase these

Cost real effort, and acting on them makes output *worse*.

- **Corner sharpness falloff** — real segments of one camera disagree on even the
  *sign*. It follows subject placement, not optics.
- **Highlight clipping as a realism tell** — real phone video ranges from 0.001% to
  0.46% of pixels at 255 depending on whether the scene contains a bright window.
  Scene content, not sensor behaviour.
- **"Grain lives in the shadows"** — and equally "grain rises with brightness". Both
  are true of *some* real cameras. The profile reverses between the two we measured.
- **Blink asymmetry** — clinically, healthy blinking is symmetric. Adding offset reads as facial palsy.
- **L/R catchlight mismatch** — a StyleGAN-era artifact, solved in diffusion. Spend effort on catchlight *motion* instead.
- **Adding chromatic aberration** — measured **0 ppm on the real reference**: 4:2:0 subsampling destroys it. Adding CA moves us *away* from the target.
- **Extra limbs / six fingers** — malformed geometry outnumbers extra parts ~8:1. Count fingers and you'll miss the real failure.
- **rPPG pulse signal** — invisible to viewers, destroyed by compression. Irrelevant unless facing a forensic detector.
- **VBench `temporal_flickering`** — saturated; separated fixtures by 1.02× where min-SSIM separated them by 2.3×.

**Governing constraint:** at 720×1280 / ~1 Mbps we sit near 0.036 bits/pixel. PRNU is
gone beyond QP 28 and >70% of macroblocks are skip-coded — copied, not encoded. Any
tell that lives in per-pixel sensor statistics is destroyed before a viewer sees it.

---

## The semantic axis

Every metric measures signal. None can tell whether the shot means anything. A clip
can pass all of them while being narratively incoherent, and the unmeasured axes —
premise, performance, composition — fail silently and together.

Gates live in `tools/gate.py` (pre-generation, free) and `prompts/judge.md`
(post-generation, blind, original as control). **Run them first: a clip that fails
semantically is not worth measuring.**

Blind-judge calibration: the source reel returns *real, 0.85* and its premise is
recovered unprompted. That is the bar a candidate has to clear.

---

## Post-production chain

Full technique detail in `docs/forensics.json` (24 tells, 16 techniques).
**Order matters and several plausible orderings are wrong:**

1. **Photometric first** — clipping, then AE/WB drift. Must precede grain, or the
   grain gets rescaled and decorrelated from the luma profile it was calibrated to.
2. **Lens geometry** — distortion, vignette, veiling glare. Anchored to the lens, so
   before any frame motion.
3. **Motion** — shake crop + rotate, then rolling-shutter shear, from a *padded* source.
4. **Frame-rate conform + motion blur** in ONE pass, *after* shake so camera motion
   contributes to the blur.
5. **Focus hunt, then frame-locked smudge** — smudge after the shake crop so it stays
   locked to the frame rather than the scene.
6. **Grain LAST**, immediately before encode. Everything above resamples or averages,
   which destroys grain applied earlier.

Match each stage to the reference measured in the same run rather than to a stored
target. Fit grain per luma band and preserve the **sign** of the band-to-band trend;
a chain fitted to one camera's profile will invert it on another.

**Shake:** 1/f^1.6 body sway + a separately band-passed 4–13 Hz tremor at ~20–25% of
sway amplitude + discrete correction events every 3–5s, each stepped ~0.7× sway RMS
and smoothed over 3–8 frames. A sinusoid is a spectral delta and reads as fake.
Derive amplitude from the reference — real handheld inter-frame displacement is a
fraction of a pixel, and a fixed constant overshoots badly.
