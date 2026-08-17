# Pitfalls — a catalogue of what goes wrong

Filtered to **this** format: vertical short-form video, one seated speaker, a held
prop, natural window light, delivered through a platform re-encode.

**This file is a catalogue.** It names each failure and says how it reads on screen.
It does not say how to sweep for one, who sweeps it, or what to do when one turns up.
The procedure for every id — which artifact to open and what to do with it — is
emitted per clip by `python tools/sweep.py plan`.

**What earns an entry.** The target is a clip that could have been filmed, so an entry
has to name a rule of physics, physiology or trade practice that the picture breaks,
and say what would falsify it. A tell drawn from how generated footage is *made*,
rather than from how the world *works*, belongs on the do-not-chase list instead.

Severity is for this format, not in general. Tier 0 fails silently and kills the
clip outright; Tier 1 is what a person can see; the vendor defaults in Tier 2 are
where those tells come from.

---

## Tier 0 — semantic failure

No measurement in this repo sees any of these. A clip can be flawless in every tile
and every metric while being one of them, and they fail together: a shot that has
lost its premise usually also has a prop doing nothing and a performance pulling the
wrong way. They are caught by a viewer who has not been told what the shot was meant
to be — which is why they are checked first, and checked blind.

| id | tell | how it reads |
|---|---|---|
| `S1` | **Premise gone.** Every element present, no point. | a viewer can describe what is happening but not what the video is *for* |
| `S2` | **Prop without function.** The object is there and does nothing. | the thing in the hands can be named but not explained; swapping it for anything else would change nothing |
| `S3` | **Affect inverted.** Pleasant, energetic delivery on a premise that needs flat, tired or resigned. | the performance is competent and contradicts the joke |
| `S4` | **Domain implausible.** A practitioner of the depicted trade would wince. | wrong tool for the task, wrong grip, missing protective gear, a workspace nobody works in, an action that would accomplish nothing |
| `S5` | **Framing lost the subject.** Shot size or subject share drifted from what the shot is about. | the load-bearing detail is now too small to read, or an edge element has been cropped out entirely |

---

## Tier 1 — human-visible

These apply to **every person in frame**, not only whoever is speaking. Someone
cropped to a forearm cannot be checked for gaze or breathing — record those sub-tests
as not applicable and judge the rest. A secondary figure that holds still reads as
plainly as a frozen speaker, and is easier to produce by accident.

| id | tell | how it reads |
|---|---|---|
| `T1` | **Statue torso.** Only mouth and head animate, body frozen. The top "AI presenter" signature. | a torso or shoulder edge holding a dead straight line for the whole clip while the face moves |
| `T2` | **No breathing.** The shoulder line never rises or falls. | a flat collar edge. A real one wavers continuously; at 12–20 breaths a minute a short clip holds well under two full cycles, so on anything that brief the signature is the tell and a *rate* is not recoverable |
| `T3` | **No physiological jitter.** The head is glassy-smooth, with no micro-corrections. | a head that holds a line during a pause. Real heads never do, even when "still" |
| `T4` | **Mask face.** The mouth articulates, the upper face is static; no brow flash on emphasis. | watched muted, nothing tells you which word was stressed |
| `T5` | **Mannequin gaze.** Eyes welded to the lens: no saccades, no repositioning, no counter-rotation when the head turns. | the eyes never move independently of the skull |
| `T6` | **Thin-prop topology collapse.** Cables and straps re-route between frames, change length, pass through fingers. | the strand traced end to end on one frame does not survive to the next |
| `T7` | **Contactless hold.** The hand and the object occupy the same space without interacting. | no fingertip flattening, no skin blanching, no dark contact line. The absence of all three at once is the tell |
| `T8` | **End-loaded collapse.** Clean early, degrades in the final 1–2s. ~85% clean at 5s against ~55% at 10s. | whatever is wrong is worst at the tail, which is why the tail is read first |
| `T9` | **Garbled or drifting text.** Any in-frame glyph, and any logo on a real-world object. | a wordmark legible in one frame and mush in the next. A wrong wordmark reads as fake faster than a blank surface |
| `T10` | **Art-directed background.** Every object legible, relevant and attractively placed. | no incidental ugliness. Real rooms are full of irrelevant objects nobody chose |
| `T11` | **Framing too perfect.** Dead-centre subject, level horizon, no operator error. | head position that never drifts. Real handheld wanders and then gets corrected |
| `T12` | **Cinema bokeh on a phone framing.** | a background point highlight blurring to a disc wider than ~1.5% of frame height, which no phone lens produces at this shot size |
| `T13` | **AE/WB never move.** | exposure perfectly flat for the whole clip. Real footage wanders and shows at least one step response |
| `T14` | **Beauty bias / age flattening.** An ordinary 50-year-old comes back as an attractive 32. Worst under text-only identity. | only visible across generations: several seeds resemble each other more than several real people would |
| `T15` | **Object scale and placement.** Held objects return at the wrong size in either direction — often one part of an object rather than all of it — and edge intrusions reach too far in. | the object read against a body landmark (head height, hand breadth) does not match its real dimension; or something entering at an edge has its deepest point well inside the frame |
| `T16` | **Incomplete assembly.** An object or a body that never resolves into one whole working thing. | parts missing that it could not function without, joins that do not close, counts that do not add up — a limb that cannot be traced from hand back to a shoulder or to the edge it enters from, a tool with no grip or power source, a fitting fastened to nothing. It is a per-frame fault, so it survives every frame-to-frame check unchanged |

---

## Tier 2 — Seedance defaults (vendor and practitioner reported)

Where several Tier 1 tells come from. These are the model's behaviour with no
instruction to the contrary.

| default | effect here |
|---|---|
| **Stern resting face**; mood adjectives lose | **helps** — the target affect is flat and resigned |
| **Drifty push-in** unless locked | hurts — a creep, not handheld jitter |
| **Crowd creep** — dialogue scenes add onlookers; removing them from a start frame does *not* stop it | the count has to be stated and extras negated |
| **Spontaneous narration** | has to be negated explicitly |
| **Floaty, overlit look** | a look worth fighting on its own terms, not because it is detectable |
| **No `seed`, no `negative_prompt`** | zero reproducibility; A/B needs N per arm, not pairs |
| **Dubbing fails on a visible mouth** | audio is locked at generation time |
| **64:1 reject ratio** on real production | the planning number |

---

## Do not chase these

Each costs real effort, and acting on it makes the output *worse*.

- **Corner sharpness falloff** — real segments of one camera disagree on even the
  *sign*. It follows subject placement, not optics.
- **Highlight clipping as a realism tell** — real phone video ranges from 0.001% to
  0.46% of pixels at 255 depending on whether the scene contains a bright window.
  Scene content, not sensor behaviour.
- **"Grain lives in the shadows"** — and equally "grain rises with brightness". Both
  are true of *some* real cameras. The profile reverses between the two measured here.
- **Blink asymmetry** — clinically, healthy blinking is symmetric. Adding an offset
  reads as facial palsy.
- **L/R catchlight mismatch** — a StyleGAN-era artifact, solved in diffusion. Spend
  the effort on catchlight *motion* instead.
- **Chromatic aberration** — measured **0 ppm on the real reference**: 4:2:0
  subsampling destroys it. Adding it moves away from the target.
- **Extra limbs and six fingers** — malformed geometry outnumbers extra parts ~8:1.
  Count fingers and you will miss the real failure.
- **rPPG pulse signal** — invisible to viewers, destroyed by compression. Irrelevant
  unless facing a forensic detector.
- **VBench `temporal_flickering`** — saturated; it separated fixtures by 1.02× where
  min-SSIM separated the same pair by 2.3×.

**Governing constraint:** at 720×1280 / ~1 Mbps this format sits near 0.036
bits/pixel. PRNU is gone beyond QP 28 and >70% of macroblocks are skip-coded —
copied, not encoded. Any tell that lives in per-pixel sensor statistics is destroyed
before a viewer ever sees it.
