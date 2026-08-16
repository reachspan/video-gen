# Pitfalls — AI video tells, ranked for 9:16 handheld talking-head

Distilled from ~190 researched entries across 8 axes, deduped and filtered to what
matters for **this** format: 4–10s vertical, one seated speaker, held prop, natural
window light, delivered through a platform re-encode.

Severity is **for this format**, not in general. `M` = I measured it on our own
reference/output; those beat literature.

---

## Tier 1 — measured on our own footage

These are not predictions. `tools/vq.py` separated real from generated on each.

| id | tell | check | fix |
|---|---|---|---|
| `M1` | **Fake handheld.** Generated shake is white noise (slope −0.29); a real hand is 1/f (−1.68) with discrete corrections. Peakiness 20.6 vs 1.9. | `vq.py` → `shake_spectral_slope`, `shake_peakiness` | post only. Sum: <1 Hz postural drift, 0.25 Hz breathing, 1–3.5 Hz tremor (most amplitude), Poisson-timed impulses. Never a sinusoid. |
| `M2` | **No lens.** Sharpness follows the *subject*, not the optical axis. Real −0.31 radial / centre 1.36× corners; generated +0.27 / 0.60. | `vq.py` → `sharpness_radial_corr` | post only. Radial falloff + slight barrel. Cannot be prompted. |
| `M3` | **Impossible dynamic range.** Window and interior both correctly exposed. Real clips 0.17% at 255; generated 0.04%. | `vq.py` → `clip_high_pct`, `pct_above_240`, `clip_to_shoulder` | prompt hard ("blows out to pure white, no detail"), then force a genuine clipped population in post. |
| `M4` | **Object impermanence.** Background patches degrade under motion compensation: worst-NCC 0.33 real vs 0.25 generated. | `vq.py` → `permanence_worst_ncc` | shorter clips; fewer background objects; keep the subject from sweeping across detail. |
| `M5` | **Motion too uniform.** Real handheld is bursty (`motion_cv` 0.41); generated 0.36 and smoother. | `vq.py` → `motion_cv` | script discrete events; add post shake with real impulse content. |

**Grain magnitude** is the one axis where generated output overshoots rather than
falls short: it measures noisier than the reference in every luma band. `post.py grain`
adds noise, so it is the wrong tool here — the gap wants closing from the other side.

---

## Tier 2 — highest severity, not yet measured

| id | tell | cheapest check |
|---|---|---|
| `T1` | **Statue torso.** Only mouth/head animate; body frozen. Top "AI presenter" signature. | difference-blend vs frame 1; whatever stays black never moved |
| `T2` | **No breathing.** Shoulder line holds constant height. | crop a shoulder strip, scrub; expect 12–20 cycles/min |
| `T3` | **No physiological jitter.** Head glassy-smooth, no micro-corrections. | flip two frames 3 apart during a "still" moment |
| `T4` | **Mask face.** Mouth articulates, upper face static; no brow flash on emphasis. | watch muted: can you tell which word is stressed? |
| `T5` | **Mannequin gaze.** Eyes welded to lens, no counter-rotation on head motion, never reposition. | do the eyes ever move independently of the skull? |
| `T6` | **Cinema bokeh on a phone framing.** Blur disc >1.5% of frame height is not a phone. | measure a background point highlight |
| `T7` | **AE/WB never move.** Exposure flat for the whole clip. | plot per-frame mean luma; real shows wander + one step response |
| `T8` | **Beauty bias / age flattening.** Ordinary 50-year-old returns as attractive 32. Worst under text-only identity. | 5 seeds side by side: more similar than 5 real people? |
| `T9` | **Thin-prop topology collapse.** Cables re-route between frames, change length, pass through fingers. **Our prop is a cable coil.** | trace the cable end-to-end on frames 1 / mid / last |
| `T10` | **Contactless hold.** No fingertip flattening, no deformation, no contact shadow. | zoom 400% on the grip; look for blanching + a dark contact line |
| `T11` | **End-loaded collapse.** Clean early, degrades in the final 1–2s. ~85% clean at 5s vs ~55% at 10s. | inspect the last 2s *first* |
| `T12` | **Framing too perfect.** Dead-centre, level horizon, no operator error. | plot head position: real drifts then gets corrected |
| `T13` | **Art-directed background.** Every object legible, relevant, attractively placed; no incidental ugliness. | list objects: would a set dresser have chosen each? |
| `T14` | **Garbled / drifting text.** Any in-frame glyph. | zoom 400%, read every string aloud |

---

## Tier 3 — Seedance-specific defaults (vendor/practitioner reported)

| default | effect here |
|---|---|
| **Stern resting face**; mood adjectives lose | **helps** — our target affect is flat and resigned |
| **Drifty push-in** unless locked | hurts — it's a creep, not handheld jitter |
| **Crowd creep** — dialogue scenes add onlookers; start-frame removal does *not* stop it | we want exactly two edge figures; specify the count and negate extras |
| **Spontaneous narration** | must negate explicitly |
| **Floaty, overlit look** | corroborates `M3` independently |
| **No `seed`, no `negative_prompt`** | zero reproducibility; A/B needs N per arm, not pairs |
| **Dubbing fails on a visible mouth** | audio is locked at generation time |
| **64:1 reject ratio** on real production | the planning number |

---

## Anti-pitfalls — do NOT chase these

Cost real effort, and acting on them makes output *worse*.

- **Blink asymmetry** — clinically, healthy blinking is symmetric. Adding offset reads as facial palsy.
- **L/R catchlight mismatch** — a StyleGAN-era artifact, solved in diffusion. Spend effort on catchlight *motion* instead.
- **Adding chromatic aberration** — measured **0 ppm on the real reference**: 4:2:0 subsampling destroys it. Adding CA moves us *away* from the target.
- **Extra limbs / six fingers** — malformed geometry outnumbers extra parts ~8:1. Count fingers and you'll miss the real failure.
- **rPPG pulse signal** — invisible to viewers, destroyed by compression. Irrelevant unless facing a forensic detector.
- **VBench `temporal_flickering`** — saturated; separated fixtures by 1.02× where min-SSIM separated them by 2.3×.

---

## Dead metrics — measured, do not re-add

Recorded so nobody rediscovers them. All die because the target is *real video that
survived a platform encode*, not a pristine camera.

| metric | why dead |
|---|---|
| lateral chromatic aberration | 0 ppm on real reference — chroma subsampling |
| temporal noise independence | 0.87 on real — measures static texture, not sensor noise |
| grain advection gain | 0.014 — inter-frame motion is 0.03 px, nothing to advect |
| vignetting | scene content swamps lens falloff (bright windows at frame edges) |
| non-rigid residual | needs sub-pixel compensation; integer shifts give ratios >1 on *both* |

---

## Reference baselines

Not recorded here. Absolute values move with frame count, sampling offset and
estimator, so a pasted number goes stale and then flags healthy clips. Pass the
reference and the candidate to `vq.py measure` in one run and read the comparison;
only the sign and the ratio between them carry meaning.

---

## The semantic axis

Every metric above measures whether footage looks *camera-captured*. None can tell
whether the shot means anything. A clip can pass most of them while being narratively
incoherent, and unmeasured axes — premise, performance, composition — fail silently
and together.

Gates live in `tools/gate.py` (pre-generation, free) and `prompts/judge.md`
(post-generation, blind, original as control). **Run them first: a clip that fails
semantically is not worth measuring.**

Blind-judge calibration: the source reel returns *real, 0.85* and its premise is
recovered unprompted. That is the bar a candidate has to clear.

---

## Post-production chain

`M1`–`M3` cannot be prompted away. Full detail in `scratchpad/forensics.json`
(24 tells, 16 techniques). **Order matters and several plausible orderings are wrong:**

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

**Highest-value single item: forced highlight clipping** (`M3`). Visible to a casual
viewer, immune to compression, trivially measurable. Targets `0.35%` at/above 254 and
`0.80%` at/below 1 — note the asymmetry, roughly **twice as much crushed black as blown
white**. Prompt for it *and* verify per clip; the model's aesthetic prior resists it.

**Grain rises with brightness.** Reference profile, flatness ranked within each luma
band: shadow 0.411 → midlow 0.839 → midhigh 0.636 → highlight **1.538**. Shot noise
scales as √signal, so *absolute* noise is largest in the highlights; the "noise lives
in the shadows" intuition describes *relative* noise (SNR) and does not apply to this
metric. Rank flatness per band — a single global gradient threshold selects almost
only shadow and leaves the bright bands unmeasurable.

**Shake** (`M1`): 1/f^1.6 body sway + a separately band-passed 4–13 Hz tremor at
~20–25% of sway amplitude + discrete correction events every 3–5s, each stepped
~0.7× sway RMS and smoothed over 3–8 frames. A sinusoid is a spectral delta and reads
as fake.

**Governing constraint:** at 720×1280 / ~1 Mbps we sit near 0.036 bits/pixel. PRNU is
gone beyond QP 28 and >70% of macroblocks are skip-coded — copied, not encoded. This is
*why* the dead-metrics list above is dead, confirmed independently.

---

## Open — verify before shipping

- **Provenance.** Output carries a signed C2PA manifest — `trainedAlgorithmicMedia`,
  `BytePlus_ModelArk`, model name, a log id tying it to a specific generation, and an
  X.509 signature. `ffprobe`/`exiftool` do **not** surface it (neither parses C2PA uuid
  boxes), so absence in those tools is not evidence of absence. That IPTC value is a
  labelling trigger on Meta, TikTok and YouTube. Note also that **Meta embeds its own
  invisible watermark server-side during transcode**, so a published Reel cannot be
  made unmarked regardless of what the file arrives with — treat platform AI labelling
  as a given and optimise for craft quality, not for defeating it.
- **EU AI Act Art. 50** — deliberately not researched; do not reconstruct from memory.
  Check consolidated Regulation (EU) 2024/1689 directly.
- **Higgsfield 1080p for Seedance 2.5** — CLI advertises it; ByteDance's table says 2.5
  caps at 720p. One source is wrong; untested.
- **Generate high, degrade down.** The playbook recommends generating at 1080p and
  degrading, rather than generating at the 720p target. Untested here; conflicts with
  our current 720p-to-match-reference choice.
