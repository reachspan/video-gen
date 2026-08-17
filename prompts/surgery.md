Regenerate a bad span of an otherwise good clip, pinned at both ends by real frames
so it splices back in. For something *wrong in a place*: an object that morphs, a
prop that re-routes, a hand that breaks and recovers, a tail that collapses.

## Why patch

With no exposed seed (`docs/pitfalls.md`), a full regeneration re-rolls the framing,
performance and set dressing that were already right. A patch keeps those and
re-rolls only the span that is not.

A patch costs a fixed minimum duration; a full regen scales with clip length.
Patching wins on longer clips and loses on short ones. Price both:

    higgsfield generate cost <model> --prompt "x" --duration <n> --resolution 720p

If the clip is short and the defect is everywhere, regenerate. If the clip is long
and the defect is a second of it, patch.

## 1. Localize precisely

You need a frame range, not an impression. Sources, in order of directness:

    vg vq measure ref.mp4 out.mp4      # permanence_hotspots -> frame + box
    vg sweep tiles out.mp4 sweep/      # odd_* names the worst frame per tile
    # motion_by_block: which third of the clip degraded

Open the frames at 4x and confirm the defect with your own eyes before spending
anything. Note the first bad frame and the last bad frame.

Check `warnings` in the measurement first. On a clip where alignment mostly failed, a
hotspot is not a location.

## 2. Choose the anchors

The patch is pinned by two real frames from the parent clip. Pick them **outside** the
defect, and pick them well:

- A few frames of clearance either side of the bad span, so the model is not asked to
  reproduce the defect at its own boundary.
- **Sharp frames only.** A motion-blurred anchor gives the model a blurred target and
  the patch will start and end soft. Step through candidates and pick clean ones.
- Prefer anchors where the subject is mid-gesture in the *same* configuration at both
  ends, so the span has an obvious path between them.
- The window must be at least 4s. If the defect is shorter, widen it — you will be
  replacing good footage either side, which is the cost of the minimum duration.

Extract them exactly:

    ffmpeg -v error -i out.mp4 -vf "select='eq(n\,START)'" -vsync 0 -frames:v 1 a.png
    ffmpeg -v error -i out.mp4 -vf "select='eq(n\,END)'"   -vsync 0 -frames:v 1 b.png

Inspect both at 4x. An anchor carrying a defect propagates it into the patch.

## 3. Write the patch prompt

Reuse the parent clip's prompt for `GLOBAL STYLE`, `LOCATION`, `LIGHTING` and `CAMERA`
blocks unchanged — the patch has to belong to the same shot. Replace the action
blocks with **only what happens between the two anchors**, and say what must not
change:

> CONTINUITY: the shot is already running. The subject, framing, lighting and camera
> position are fixed by the first and last frames. Nothing enters or leaves the frame.
> The prop stays in the same hands, the same size and the same route throughout. No
> cut, no reframe, no change of shot size.

Negatives inline. Write the patch in the register `docs/prompt-language.md` names.

## 4. Generate

`generation.md` owns the call — model checks, costing, batching, collection. A patch
changes four things about it.

**Anchor frames.** Use a model that accepts a start frame **and** an end frame, and
confirm which modes expose them: anchors have been restricted to a specific reference
mode rather than being available in plain text-to-video.

    higgsfield model get <model>

    higgsfield generate create <model> \
      --mode <the mode that accepts anchors> \
      --prompt "$(cat patch.txt)" \
      --start-image a.png --end-image b.png \
      --duration <minimum> --resolution 720p --aspect_ratio 9:16 --wait

**Audio off** if it defaults on. The patch would otherwise arrive with its own invented
audio and you would be splicing an audio seam as well as a picture one; keep the parent
clip's audio and lay the patched picture under it.

**No reference clip.** The anchors already fix the camera, the framing and the
exposure, and they come from the shot itself rather than from the original.

**Keep the identity and prop references.** The same files the parent take used, unchanged,
or the patched span comes back with a different person in it.

Budget several attempts.

## 5. Check the patch before splicing

    vg vq measure out.mp4 patch.mp4

Read it as a match test, not a quality test: the patch should sit close to its parent
clip on exposure and grain profile. `noise_luma_slope` is the useful one
(`docs/evidence.md`) — a patch that disagrees with the parent on slope will read as a
different camera when spliced.

Then look at the first and last frames of the patch against the anchors at 4x. If the
model interpolated rather than continued — a smooth morph between the two anchors
with no real motion in between — reject it and re-prompt with more specific action.

## 6. Grade and splice

Two seams, and generated clips drift in colour between runs, so the patch will not
match its neighbours out of the box.

    vg post exposure out.mp4 patch.mp4 patch_graded.mp4

Conform frame rate before splicing if it differs (Seedance output is 24fps). Cut on
the anchor frames so each anchor appears once.

## 7. Re-judge the whole clip

A patch is a new generation and can carry new defects, including at the seams. Run
the full check from `judge.md` on the spliced result — not just the patched span.
The tail package matters especially: splicing changes where the clip's end sits.

## Adjacent tools

Video-edit and video-extension modes exist alongside this one, for altering or
lengthening a clip rather than repairing a span of it. Neither takes anchor frames,
so neither guarantees a splice will line up — check what the current model offers,
but prefer anchors whenever the result has to rejoin existing footage.
