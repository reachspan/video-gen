# Surgery — repairing a localized defect

Regenerate a bad span of an otherwise good clip, pinned at both ends by real frames
so it splices back in. For a defect that occupies part of the runtime and leaves the
rest usable.

**Not for:** a semantic failure (wrong premise, wrong performance, missing element) —
that is a prompt problem, so fix the prompt and regenerate whole. **Not for:** a
signal mismatch (exposure, shake, grain) — that is `post.py`, and it is free.

Surgery is for something that is *wrong in a place*: an object that morphs, a prop
that re-routes, a hand that breaks and recovers, a tail that collapses.

## Why patch instead of regenerating

Not primarily cost. **No Seedance endpoint exposes a seed**, so a full regeneration
re-rolls every element of the shot — the framing that was right, the performance that
was right, the set dressing that was right. Documented reject ratio on real
production is 64:1. A patch keeps everything that already works and re-rolls only the
span that does not.

Cost is a secondary argument and it is close:

| | credits |
|---|---|
| `seedance_2_5` 720p, 4s (the minimum patch) | 26 |
| `seedance_2_5` 720p, per second | ~6.5 |
| `seedance_2_0` 720p 5s (full regen) | 22.5 |

A patch is a flat 26 regardless of how long the clip is, so it beats a full 2.5
regeneration above ~4s and loses to a fresh 2.0 generation on a short clip. If the
clip is 5s and the defect is everywhere, regenerate. If the clip is 8s and the defect
is one second of it, patch.

## 1. Localize precisely

You need a frame range, not an impression. Sources, in order of directness:

    python tools/vq.py measure ref.mp4 out.mp4      # permanence_hotspots -> frame + box
    python tools/sweep.py tiles out.mp4 sweep/      # odd_* names the worst frame per tile
    # motion_by_block: which third of the clip degraded

Open the frames at 4x and confirm the defect with your own eyes before spending
anything. Note the first bad frame and the last bad frame.

Check `warnings` in the measurement first. On a clip where alignment mostly failed, a
hotspot is not a location.

## 2. Choose the anchors

The patch is pinned by two real frames from the original. Pick them **outside** the
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

Reuse the original prompt's `GLOBAL STYLE`, `LOCATION`, `LIGHTING` and `CAMERA`
blocks unchanged — the patch has to belong to the same shot. Replace the action
blocks with **only what happens between the two anchors**, and say what must not
change:

> CONTINUITY: the shot is already running. The subject, framing, lighting and camera
> position are fixed by the first and last frames. Nothing enters or leaves the frame.
> The prop stays in the same hands, the same size and the same route throughout. No
> cut, no reframe, no change of shot size.

Negatives go inline: there is no `negative_prompt` on any Seedance endpoint.

## 4. Generate

    higgsfield generate create seedance_2_5 \
      --mode omni_reference \
      --prompt "$(cat patch.txt)" \
      --start-image a.png --end-image b.png \
      --duration 4 --resolution 720p --aspect_ratio 9:16 \
      --bitrate_mode high --generate-audio=false --wait

`start_image` and `end_image` are accepted **only** in `omni_reference` mode.

Set `generate_audio` false. The patch would otherwise arrive with its own invented
audio and you would be splicing an audio seam as well as a picture one; keep the
original track and lay the patched picture under it.

No seed means A/B needs N per arm, not pairs. Budget several attempts.

## 5. Check the patch before splicing

    python tools/vq.py measure out.mp4 patch.mp4

Read it as a match test, not a quality test: the patch should sit close to its parent
clip on exposure and grain profile. `noise_luma_slope` is the useful one — it is a
capture-pipeline fingerprint and barely moves with bitrate, so a patch that disagrees
with the parent on slope will read as a different camera when spliced.

Then look at the first and last frames of the patch against the anchors at 4x. If the
model interpolated rather than continued — a smooth morph between the two anchors
with no real motion in between — reject it and re-prompt with more specific action.

## 6. Grade and splice

Two seams, and generated clips drift in colour between runs, so the patch will not
match its neighbours out of the box.

    python tools/post.py exposure out.mp4 patch.mp4 patch_graded.mp4

Conform frame rate before splicing if it differs (Seedance output is 24fps). Cut on
the anchor frames so each anchor appears once.

## 7. Re-judge the whole clip

A patch is a new generation and can carry new defects, including at the seams. Run
the full check from `judge.md` on the spliced result — not just the patched span.
The tail package matters especially: splicing changes where the clip's end sits.

## Adjacent tools

`seedance_2_5` also offers `video_edit` (one video reference) and `video_extension`
(`extension_mode` `backward` or `forward`) for lengthening rather than repairing.
Neither takes anchor frames, so neither guarantees a splice will line up.
