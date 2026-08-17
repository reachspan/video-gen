Find a photograph of a real object. One image per object, reused unchanged.

    output/<id>/ref.<name>.png          the photograph, cropped and ready to attach
    output/<id>/ref.<name>.source.txt   where it came from, and what it supplies

Which objects: `generation.md` §1. Free.

## Why a photograph

A generated prop image is a generation: incomplete (`T16`), wrong scale (`T15`),
almost-right wordmark (`T9`). Attaching it specifies those faults into the take.
The video model reproduces the reference faithfully, so a wrong object described
precisely is worse than a right object described loosely.

Identity is the exception (`face-gen.md`): an invented face has no ground truth.
An object that exists does — a photograph is right; a rendering is only plausible.

## What to look for

Search for the specific make and model where the reference clip identifies one, and for
the generic article where it does not. Roughly in order of how usable what they return
tends to be:

- **Manufacturer and distributor product pages.** Plain background, flat light, the
  whole object, several angles — most of what an object reference wants, already met.
- **Trade suppliers and spare-parts catalogues**, for anything a general retailer
  photographs badly or does not carry. They keep the variant distinctions a practitioner
  reads and a consumer listing flattens, and `S4` is exactly the reader who notices.
- **Marketplace and auction listings**, when the spec wants a used one. An ugly amateur
  photograph of a worn example is right here and a catalogue shot is not.
- **Image search**, for scale and for context: the thing in a hand, or in use. That is
  what settles size, and size is the one property a product shot cannot tell you.

Take the variant decision yourself rather than deferring it. Where the clip does not
resolve the make, pick what the spec's `function` supports — the tool that would
actually do the job described — and record the choice in `report.md`.

## What makes one usable

The video model takes lighting, framing and camera behaviour from elsewhere. This image
supplies the object, so everything else in the frame is contamination:

- **The right variant.** The most common failure and the only one that survives
  everything downstream. Wrong size class, wrong fitting, wrong era, the consumer model
  where the trade one belongs: all of it reads as wrong to anyone who owns one, and none
  of it reads as wrong to you.
- **Plain background, flat even light.** Anything baked in fights the lighting the video
  prompt asks for. A hard key or a coloured gradient in a product shot is set dressing.
- **The whole object, uncropped.** A part of a thing attached as a reference is how a
  take comes back with a part of a thing in it.
- **The condition the spec asks for.** New and boxed fights a premise that needs worn and
  greasy. If the only good photograph is a pristine one, say so in the `REFERENCES`
  clause rather than pretending it is not there.
- **A hand in frame where size is load-bearing** (`T15`). Scale is judged against a body,
  and an object photographed alone on white establishes none. Prefer a photograph of the
  thing held or in use, even a worse one, when the spec's `must_be_true` depends on how
  big it is.
- **Nothing you cannot crop out.** Logos, part numbers and moulded lettering will be
  reproduced garbled in the take. Prefer an angle where the mark is not visible, crop it
  away, or negate it explicitly in the `REFERENCES` clause.
- **No overlay of any kind.** Watermarks, price flashes, retailer badges, corner logos,
  drop shadows onto a fake floor. These are text and furniture, and the model will treat
  them as part of the object.

## Prepare it

Crop to the object and convert to PNG. Nothing else — no upscaling, no relighting, no
background removal that leaves a hard matte edge where the object used to meet the world:

    ffmpeg -v error -i raw.webp -vf "crop=W:H:X:Y" output/<id>/ref.drill.png

If several photographs each carry part of the answer — one for the variant, one for the
scale — attach the best single one rather than compositing them. Reference slots are
capped (`generation.md` §1), and a composite is a picture of two objects.

## Inspect before attaching

Open it as a tight crop upscaled 4x (`docs/evidence.md`):

    ffmpeg -i output/<id>/ref.drill.png -vf "crop=400:400:X:Y,scale=1600:1600:flags=lanczos" crop.jpg

Check, in this order:

1. **Is it the right thing?** Against the spec's `what` for that element, not against
   your memory of the clip. This is the check the rest of the pipeline cannot make for
   you: every downstream reader compares the take to the spec, and none of them compares
   the reference to the world.
2. **Is anything in the frame that is not the object** — a second product, a hand model's
   watch, a size chart, a reflection carrying the studio.
3. **Text**, at 4x, including moulded and etched lettering that a thumbnail hides.
4. **Is it one photograph of one object**, not a multi-pack, an exploded diagram, a
   render, or a marketing composite with the thing shown twice.

A render found in a catalogue is still a render and inherits the problem this file
exists to avoid. Prefer a photograph; if only a render exists, treat it as the fallback
below.

## When no photograph exists

Some objects are invented, discontinued or simply unphotographed. Generate one with
`face-gen.md`'s model and its plainness rules — flat light, plain background, whole
object, no text — and then inspect it against `T15`, `T16` and `T9` specifically, since
those are what a generated object gets wrong and what a photograph would have settled.

It is a paid call, so it counts against the budget like any other generation. Treat it
as the exception it is rather than the quiet default.

## Handing off

What lands beside the spec is the image and a note saying where it came from — the URL,
what variant it is, and which of the properties above it supplies. A reference that turns
out to be the wrong variant is otherwise untraceable: the take is wrong, every reader
agrees it is wrong, and nothing points back at the picture that made it wrong.

`generation.md` §2 writes the `REFERENCES` clause that says what to take from it and what
to ignore. Reuse the exact same file for every take, for the same reason a character
does: two clips of a scene with two different objects in them cannot be cut together.
