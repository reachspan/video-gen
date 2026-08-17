# face-gen — building a character reference image

Produce a still of a face that reads as a real person, to be passed into video
generation as the identity reference. One image, reused unchanged for every shot of
that character.

## Why a reference image at all

Describing a face in the video prompt does not work. Identity drifts across the take,
and text-only identity is where **beauty bias** bites hardest: an ordinary
fifty-year-old comes back as an attractive thirty-two-year-old, every time, because
the model's prior for "man" is a good-looking man.

Pinning identity to an image fixes the drift and shortens the video prompt, which
leaves room for the things only text can carry — premise, blocking, performance.

## Picking a model

**Nano Banana Pro (`nano_banana_pro`), unless there is a reason to change it.** It is the
top tier of the family the lineup points at for character and reference-driven image
work, which is this job rather than text or graphic design. `nano_banana_2_lite` is the
cheaper fallback when a run is tight, at some cost in fidelity on a hard brief.

The lineup turns over, so confirm it is still there and read what it takes rather than
trusting this page:

    higgsfield model list --image
    higgsfield model get nano_banana_pro
    higgsfield generate cost nano_banana_pro --prompt "..."

Ask for a portrait aspect ratio, so the head and enough torso both fit in one frame
without cropping either — the reference is useless for wardrobe otherwise. Resolution
beyond the default buys nothing here: this image is read for identity, and the video
model resamples it regardless.

Stills are cheap relative to video — cheap enough to iterate honestly, so generate
several and reject most. Confirm the current price before a long run rather than
assuming.

## Writing the prompt

### Fight the beauty prior explicitly

The default output is symmetrical, young, clear-skinned and well-proportioned.
Ordinary faces are none of those things. Name the specific irregularities you want —
a general instruction to "look ordinary" will not survive:

- **Asymmetry.** One eye slightly lower or smaller, a nose broken and set a little
  off, an uneven smile, one ear higher.
- **Skin as a surface, not a finish.** Visible pores, broken capillaries across the
  nose and cheeks, blackheads, sun damage, uneven tone, razor rash, a shine of sweat.
  Say **no beauty retouch, no skin smoothing, no airbrushing, no plastic sheen.**
- **Age where age actually shows.** Neck and hands age before faces. Ask for a
  slackening jawline, under-eye bags, deep nasolabial folds, thinning or receding
  hair, grey stubble growing in unevenly, sun-damaged forearms.
- **Teeth.** The default is a bright even set. Ask for slight crowding, uneven
  colour, a chip, some wear.
- **Build.** "Heavy build, thick neck, sloping shoulders" — the default body is
  athletic regardless of the face.

State an occupation and a life, not just a look. "A man who has laid cable for
twenty-five years" pulls weathering, build and posture together more reliably than
listing them.

### Make it usable as a reference

The video model takes lighting and camera behaviour from elsewhere. This image
supplies identity, so it should be plain:

- **Flat, even, neutral light.** No hard key, no rim light, no coloured gels, no
  moody shadow. Anything baked in here fights the lighting the video prompt asks for.
- **Front on, neutral expression, eyes to camera**, head straight, nothing cropped.
- **Plain background**, no set dressing to leak into the shot.
- **Include the wardrobe and enough of the torso** for the video prompt to inherit
  it — a video prompt can reasonably say "take the face, head, build, skin and shirt
  from @Image 1", and it can only do that if they are in the frame.
- **Nothing with text on it.** Logos and printed marks on the reference will be
  reproduced garbled in the video; keep the clothing blank.
- Photographic, not stylised. No portrait-lens bokeh, no editorial grade.

## Inspect before using

Open every candidate as a tight crop upscaled 4x — a full frame arrives downsampled
and you will both miss real faults and invent ones that are not there.

    ffmpeg -i face.png -vf "crop=400:400:X:Y,scale=1600:1600:flags=lanczos" crop.jpg

Check, in this order:

1. **Did the beauty prior win?** Compare against the age and life you asked for. If
   the face looks like a model playing the part rather than someone who has lived
   it, reject it. This is the failure that survives everything downstream.
2. **Eyes.** Pupils round and matched, gaze on axis, catchlights consistent with one
   flat source.
3. **Teeth and mouth**, at 4x.
4. **Ears, hairline, jewellery** — the usual sites of quiet geometric nonsense.
5. **Hands**, if in frame.

Read the do-not-chase list in `docs/pitfalls.md` before acting on anything you find.
Several of the most plausible-looking face faults are on it, and correcting one makes
the image worse rather than better.

## Steering from the user

When the user asks for changes, edit the prompt and regenerate rather than accepting
drift — a still is cheap enough that re-rolling beats negotiating. Keep the approved
image as a file and reuse **the exact same file** in every downstream generation;
regenerating "the same" character produces a different person.

For a character appearing across many shots, `higgsfield soul-id` trains a persistent
identity and returns a `reference_id`. Worth it past a handful of shots; a single
image is enough below that.

## Handing off

The output of this is one PNG and the prompt that produced it. Both belong beside the
target spec, so the character can be reproduced or revised later. `compile.md` writes
the character into the video prompt; `generation.md` attaches this exact file. Every
main character needs one; minor figures are worth one if there is budget.
