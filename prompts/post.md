# Post — matching a clip's signal to its reference

For a candidate that is semantically right and looks wrong in a way that is purely
photometric or motion: exposure that never wanders, highlights that never clip, a
camera held too still, grain that does not match the reference's profile.

**Not for:** anything a viewer would describe in words — a wrong premise, a prop that
does nothing, a hand that morphs. Those are `compile.md` and `surgery.md`. Post moves
numbers, and numbers were never the thing that made a clip read as generated.

Everything here is deterministic and free. It is the cheapest of the three fixes, so
it is worth running on a clip that already ships.

## Run it

    python tools/post.py exposure REF CAND OUT    match clipping statistics to REF
    python tools/post.py shake    REF CAND OUT    add the handheld motion deficit
    python tools/post.py grain    REF CAND OUT    add grain to REF's luma profile
    python tools/post.py chain    REF CAND OUT    all three, in the fixed order

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

`post.py chain` implements 1, 3 and 6. The rest are documented in
`docs/forensics.json` (24 tells, 16 techniques) and are hand work.

When fitting grain by hand, fit per luma band and preserve the **sign** of the
band-to-band trend. The sign is the part that identifies a capture pipeline; the
magnitude tracks the encoder and says nothing.

## Shake, if you build it yourself

1/f^1.6 body sway, plus a separately band-passed 4–13 Hz tremor at ~20–25% of sway
amplitude, plus discrete correction events every 3–5s, each stepped ~0.7× sway RMS
and smoothed over 3–8 frames. A sinusoid is a spectral delta and reads as fake.

Derive the amplitude from the reference. Real handheld inter-frame displacement is a
fraction of a pixel, and a fixed constant overshoots badly — `post.py shake` prints
the target, what is already present, and the difference it is adding, so the numbers
are visible before the clip is written.

Shake crops: the warp is done on a padded frame and the padding is cut off, so the
output is slightly smaller than the input. Conform sizes before splicing anything.

## After

Re-measure, and re-judge if the clip changed materially:

    python tools/vq.py measure ref.mp4 out_post.mp4

A post pass moves the signal metrics toward the reference by construction, so a
better score afterwards is not evidence of anything. The check that matters is that
nothing visible broke — a levels stretch can band, and a shake overlay can smear a
region that was already soft.
