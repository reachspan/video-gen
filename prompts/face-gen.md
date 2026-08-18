Produce a still of a face that reads as a real person. One image, reused unchanged
for every shot of that character.

Text identity drifts, and beauty bias is worst there: an unspecified fifty-year-old
comes back as an attractive thirty-two, because the prior for "man" is a good-looking
man. The still is what stops that. It pins a specific person — who may sit anywhere
on the beauty spectrum — and shortens the video prompt, leaving room for premise,
blocking, performance.

## Model

`nano_banana_pro` unless you have a reason. `nano_banana_2_lite` if the run is tight,
at some cost in fidelity.

Confirm it still exists:

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

### Pin a person, not a type

The default output is a type: symmetrical, young, clear-skinned, well-proportioned.
Real faces sit anywhere on the beauty spectrum. The prior to fight is the type and
the finish, not attractiveness. A good-looking twenty-eight-year-old with visible
pores is a success. A weathered fifty-year-old retouched into a handsome thirty-two
is a failure. A catalogue of defects — a broken nose, a chipped tooth, a heavy
build — on every face is the same type, inverted.

Write from the brief. If the spec names an age, a life and a build, those are the
constraints. If it does not, pick a specific person — one age, one life, one build,
one place on the beauty spectrum — and stay there. Do not default to weathered or
to handsome.

What has to be written, because the model will not do it unasked:

- **Skin as a surface, not a finish.** Visible pores, natural texture, a living
  sheen. Say **no beauty retouch, no skin smoothing, no airbrushing, no plastic
  sheen.** Do not pile on blackheads, broken capillaries or razor rash unless the
  brief's life would produce them.
- **Age as stated.** Match the age you asked for. Neck and hands age before faces,
  so if the brief is fifty, ask for that. Do not add a slackening jawline,
  under-eye bags or grey stubble to a face whose age would not show them.
- **Features from this person, not from a list.** Slight natural asymmetry is
  photographic and fine to mention as a quality of the picture. A broken nose, an
  uneven smile, a chipped tooth, a heavy build — only if this character has them.
- **Build.** The default body is athletic. If the brief is silent, pick an
  unremarkable civilian build, not an athletic one and not a heavy one.
- **Teeth.** The default is a bright even set. Unremarkable real teeth — slight
  unevenness of colour or alignment — unless the brief asks for more.

State an occupation and a life, not just a look. "A man who has laid cable for
twenty-five years" and "a woman who presents the weather on regional television"
each pull a different face. The life is how you choose a point on the spectrum,
not a reason to weather every face.

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

Open every candidate as a tight crop upscaled 4x (`docs/evidence.md`).

    ffmpeg -i face.png -vf "crop=400:400:X:Y,scale=1600:1600:flags=lanczos" crop.jpg

Check, in this order:

1. **Did a type win?** Compare against the age, life and looks you asked for.
   Two failures: the face is younger or smoother than the brief (airbrushed, even
   if the features are right), or it is a pile of irregularities the brief did
   not ask for. A good-looking face with visible pores is a pass. Either type
   survives everything downstream.
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
