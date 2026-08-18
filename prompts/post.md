Match exposure, shake and grain to the reference. For a candidate that is
semantically right and looks wrong in a way that is purely photometric or motion.

If a viewer can name the defect in words, this is the wrong file. Everything here
is deterministic and free — worth running on a clip that already ships.

## Run it

    vg post exposure REF CAND OUT    match clipping statistics to REF
    vg post shake    REF CAND OUT    add the handheld motion deficit
    vg post grain    REF CAND OUT    add grain to REF's luma profile
    vg post chain    REF CAND OUT    all three, in the fixed order

`REF` is the reference clip the candidate is recreating, and it must be the same one
`vq.py measure` was run against. Every stage fits against the reference **measured in
the same run**, never against a stored target: a chain fitted to one camera's profile
will invert it on another.

Each stage adds only the deficit. `shake` on an already-mobile clip adds nothing;
`grain` adds only the per-band shortfall, so a clip already grainier than the
reference in some band is left alone there.

## Why the order is fixed

Several plausible orderings are wrong. The full chain, including the stages `post.py`
does not implement:

1. **Photometric first** — clipping, then AE/WB drift. Must precede grain, or the
   grain gets rescaled and decorrelated from the luma profile it was fitted to.
2. **Lens geometry** — distortion, vignette, veiling glare. Anchored to the lens, so
   it goes before any frame motion.
3. **Motion** — shake crop and rotate, then rolling-shutter shear, from a *padded*
   source.
4. **Frame-rate conform and motion blur** in ONE pass, *after* shake, so camera
   motion contributes to the blur.
5. **Focus hunt, then frame-locked smudge** — smudge after the shake crop so it stays
   locked to the frame rather than to the scene.
6. **Grain LAST**, immediately before the encode. Everything above resamples or
   averages, and that destroys grain applied earlier.

`post.py chain` implements 1, 3 and 6. The rest are hand work, below.

When fitting grain by hand, fit per luma band and preserve the **sign** of the
band-to-band trend. The sign is the part that identifies a capture pipeline; the
magnitude tracks the encoder and says nothing.

## The stages `post.py` does not do

Each was validated as an `ffmpeg` invocation, and each carries a way of being wrong
that costs more than the tell it fixes. Every one of them is optional; none is
optional to *overdo*.

**Lens geometry** (stage 2), before any frame motion:

    lenscorrection=k1=-0.028:k2=0.004:i=bilinear

Negative `k1` barrels. Phone ISPs already correct distortion and lateral CA, so the
main camera after correction is nearly rectilinear — over-applying makes the clip
read as an uncorrected action cam, a different kind of wrong. Vignetting is the
easiest to overdo and reads instantly as a 2013 Instagram filter. Chromatic aberration
is on the do-not-chase list in `docs/pitfalls.md`; do not add it here either.

**Rolling-shutter shear** (stage 3, after shake): derive it from the *same*
trajectory that drives the shake — `shx(t) = C · dx/dt` on horizontal velocity —
because shear uncorrelated with camera motion is worse than no shear. Keep peak
`|shx|` in 0.002–0.008 — a fraction of frame width, so the range is the same at any
resolution; the pixel figure it buys is not. At 720×1280, 0.006 displaces the top
and bottom rows about ±4px, and proportionally less on a shorter frame. Modern
phones correct rolling shutter in the ISP, so a real 2026 capture has *less* skew
than a naive CMOS model predicts.

**Motion blur** (stage 4): interpolate up, average, decimate — that synthesises true
vector blur rather than a directionless smear. At the 24 fps Seedance has delivered, a
180° shutter is 1/48s, so use `fps=96` with `tmix=frames=2`. Read the rate off the
take with `ffprobe` first and rescale both numbers if it differs:

    minterpolate=fps=96:mi_mode=mci:mc_mode=aobmc:vsbmc=1,tmix=frames=2,fps=24

`minterpolate` is the most artifact-prone filter here. On fast hand gestures, at
occlusion boundaries and around the mouth it tears and warps far more damagingly than
the missing blur it fixes — exactly the regions a talking-head viewer is watching.

**Focus hunt** (stage 5), via `sendcmd`, since `gblur`'s sigma is not
expression-capable — a few sigma steps of 0.3–1.4 over a couple of seconds, returning
to zero. **Do not add synthetic depth of field:** Seedance's is measured good
(Laplacian variance 504 torso / 230 face / 51 background / 2.7 foreground — real
graded falloff, not a matte behind a hard outline). What is missing is variation over
time, not blur.

**Frame-locked smudge** (stage 5, after the shake crop): blur a copy and merge it
through a soft blob mask, so it stays fixed to the lens while the frame moves
underneath. That is the point — nothing in a generated clip does it, so it is a
positive signal of physical camera-ness rather than the removal of a negative one.
Keep it away from the face, and keep it weak; over-strength is a vaseline patch.

## Shake, if you build it yourself

1/f^1.6 body sway, plus a separately band-passed 4–13 Hz tremor at ~20–25% of sway
amplitude, plus discrete correction events every 3–5s, each stepped ~0.7× sway RMS
and smoothed over 3–8 frames. A sinusoid is a spectral delta and reads as fake.

Derive the amplitude from the reference. Real handheld inter-frame displacement is a
fraction of a pixel, and a fixed constant overshoots badly — `post.py shake` prints
the target, what is already present, and the difference it is adding, so the numbers
are visible before the clip is written.

Displacement is in pixels, so a taller reference carries a larger target for the
same motion, and a shorter one a smaller target. The two rarely match: the take
is whatever `generation.md` §3 chose, the reference whatever the platform delivered.
`post.py shake` divides by the height ratio and says so when it does; anything
built by hand has to do the same.

Shake crops: the warp is done on a padded frame and the padding is cut off, so the
output is slightly smaller than the input. Conform sizes before splicing anything.

## After

Re-measure, and re-judge if the clip changed materially:

    vg vq measure ref.mp4 out_post.mp4

A post pass moves the signal metrics toward the reference by construction, so a
better score afterwards is not evidence of anything. The check that matters is that
nothing visible broke — a levels stretch can band, and a shake overlay can smear a
region that was already soft.

Every stage re-encodes and drops the C2PA manifest (`docs/evidence.md`).
