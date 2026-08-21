One gated prompt → one take.

    output/<id>/prompt.v<n>.txt      in   — the prompt, gate-passed
    output/<id>/ref.<name>.png       in   — one identity or prop reference per thing
    output/<id>/take.v<n>.t<k>.mp4   out  — the take

**One candidate per run.** Whoever called it decides whether another is worth buying.
Stills: `face-gen.md`. Patches: `surgery.md`. Verdict: `judge.md`.
Require a passed gate (`compile.md` §7).

## 1. What gets attached

Three kinds of reference. Main characters need an identity image; the rest is a choice.

### The original reference clip, when text is not getting there

Not attached by default. Weigh what it buys against what it costs.

It buys the things the prompt describes worst: how the camera is held, how far away it
sits, how the exposure behaves, how the room reads, what sits at the frame edges. A
setting or a staging that several rolls have missed often lands on the first take with
it attached.

It costs the cast. **A video reference wins identity.** Its people, wardrobe and
branding carry over even with an identity image attached and the prompt forbidding them.

Attach it when the setting, staging or camera has failed repeatedly in text, and the
cast is unchanged or every character has an identity image. Leave it off when re-casting.

If the reference is longer than the segment being recreated, cut the segment out first
and attach that, so the camera behaviour it supplies is the behaviour of the seconds
you are actually making:

    ffmpeg -v error -ss 12.0 -to 16.0 -i ref_full.mp4 -c copy output/<id>/seg.mp4

### An image for every main character, always

Any character the shot is about needs an identity image from `face-gen.md` before the
call. A file, not a description. Reuse that file unchanged (`face-gen.md`).

Minor figures — a forearm at the frame edge, someone in the background — are worth an
image if there is budget for one. It supplies build, skin, hands and wardrobe. Optional.

### A photograph of a prop text keeps getting wrong, often

Strongly encouraged, and free: a sourced photograph costs nothing and settles an
ambiguity that text would otherwise leave to the roll. Find one whenever the thing is
easier to show than to describe:

- a prop whose exact geometry matters — a specific tool, a fitting, anything where the
  wrong variant reads as wrong to anyone who owns one
- a prop that must be unbranded and worn rather than new and logoed
- a spatial arrangement — who stands where, what is cropped by which edge
- a costume, or a specific material
- **anything a previous run already failed to get right in text twice.** Two failed
  rolls on the same clause is the signal; do not spend a third.

Check the register before going looking: a clause that failed twice as a pose
(`docs/prompt-language.md`) fails for a reason a picture does not fix.

Find it per `prop-ref.md`. Photograph, not a generated still.

### When they do not all fit

Reference slots are capped, and the cap differs by model and counts start and end
frames against the image budget:

    higgsfield model get <model>            # accepted roles, and the CONSTRAINTS block

Over budget, drop the reference clip first, then prop photographs, then minor
characters. Main-character images are the last thing to go.

## 2. Say what each reference is for

Attaching a reference does not tell the model which parts of it to use. The prompt's
`REFERENCES` block does, and it needs both halves — what to take, and what to ignore.
Write one clause per reference attached:

> @Image 1 is the man. Take the face, head, build, skin and shirt from @Image 1 and
> keep them exactly. Take NOTHING else from it — not its background, not its lighting,
> not its framing.

With the reference clip attached, add its clause too. The second half limits what
carries over:

> @Video 1 is the camera and the room. Take ONLY the camera behaviour, shot size,
> subject distance and exposure from @Video 1 — do NOT take the person from @Video 1,
> do NOT copy any face from it, and do NOT copy any logo, badge, printed mark, sticker
> or lettering from it.

Numbering follows the order the flags are passed, so pass them in the order the block
names them, and keep that order every time this runs. Name each reference by its role as
well as its number — "the face image", "the video reference" — so the block still reads
correctly if the numbering is not honoured.

Say it for the prop photographs too: take the object's shape, size and condition from
the picture, and nothing of its lighting, its background or its framing. A sourced
photograph needs one clause a generated still did not — a real product is photographed
with its branding on it, so name the mark and forbid it explicitly wherever one survived
the crop.

## 3. Pick the model and read what it accepts

    higgsfield model list --video
    higgsfield model get <model>

Read durations, aspect ratios, resolutions, reference caps and modes from `model get`
rather than from anything written down here — they change.

**`mode` is not always a speed control.** On Seedance 2.5 it selects what the call
does — `t2v`, `omni_reference`, `video_edit`, `video_extension` — and `t2v` refuses
reference media, so a run that attaches anything has to pass `--mode omni_reference`.
On Seedance 2.0 the same flag chose `std` or `fast`. Read which it is before writing
the call: an identity image refused by the mode comes back as the wrong person.

Settings this format wants:

- **9:16, and 480p by default.** Whatever `model get` offers is available; 480p is
  where the budget is set, not a limit. Priced at 8s on `seedance_2_5`: 20 credits at
  480p against 52 at 720p — two and a half times the takes for the same money, on a
  format whose planning number is a 64:1 reject ratio (`docs/pitfalls.md`). Re-price
  with `generate cost` rather than trusting those figures.
- **A resolution the user names wins outright**, the same way a named model does
  (`SKILL.md`). "Do it at 1080p", "720p please", a number in the prose: take it,
  price it against the budget, and do not talk them down.
- **Go up unasked when the shot turns on something small** — a wordmark, a contact
  shadow, a thin strand — and record the choice and why in `report.md`.
- **The default is a real trade.** Delivery is 720×1280 (`docs/pitfalls.md`), so
  anything below that is upscaled at ingest: detail is given up, not just spent
  where the re-encode would have destroyed it. Inspection pays too — `judge.md`
  reads 4x tiles cut from the frame, so a smaller frame means a smaller tile, and
  more `cannot_tell` on `T6`, `T7` and `T9` is the cost of the cheaper roll, not a
  clean sweep. Above 720p the trade reverses: the re-encode destroys the extra
  detail, so the higher price buys something the viewer never sees.
- **Longer than the finished clip.** Quality falls off at the tail (`T8`), so ask for a
  couple of seconds of overhead and cut the end off. It is cheaper than re-rolling a
  good take that died in its last second.
- **Audio on.** It is generated with the picture and locked there: dubbing over a
  visible mouth fails, so a take with the wrong words is a dead take, not a fixable one.
  (`surgery.md` turns audio off, because a patch inherits the parent clip's audio.)

## 4. Make the call

Cost it first. `generate cost` takes the same flags as `generate create`, so price the
call you are about to make, not a simplified version. Pass the mode and the
references too: `omni_reference` is refused without at least one reference, so a
stripped-down quote does not just misprice the call, it fails.

    higgsfield generate cost seedance_2_5 \
      --prompt "$(cat output/<id>/prompt.v2.txt)" \
      --image-references output/<id>/ref.man.png \
      --image-references output/<id>/ref.drill.png \
      --mode omni_reference \
      --duration 8 --resolution 480p --aspect_ratio 9:16

    higgsfield generate create seedance_2_5 \
      --prompt "$(cat output/<id>/prompt.v2.txt)" \
      --image-references output/<id>/ref.man.png \
      --image-references output/<id>/ref.drill.png \
      --mode omni_reference \
      --duration 8 --resolution 480p --aspect_ratio 9:16 --wait

The model, resolution and mode above are the §3 defaults; substitute what §3 chose
for this run. Add `--video-references output/<id>/seg.mp4` if §1 says this run wants
it. Drop `--mode omni_reference` only if nothing is attached — on this pipeline that
means no main character, which §1 says does not happen.

**Record the resolution this call used with the take (§6).** Later steps need the
actual size — `judge.md` for the blind pair, `post.md` for the shake target — and
both go wrong quietly if they assume the default.

`--wait` blocks until the job lands and prints the result URL. Without it the call
returns a job id straight away, and `higgsfield generate wait <id>` picks it back up.

There is no seed and no `negative_prompt` on these endpoints, so this call is a roll:
running it again with the same inputs gives a different clip, and nothing recovers the
one you just made.

## 5. Collect and check the container

Download the take beside the spec, and do not overwrite an existing one — a take that
cannot be regenerated and has been overwritten is gone:

    higgsfield generate get <job_id> --json     # the result URL
    curl -L -o output/<id>/take.v2.t1.mp4 '<url>'

Then confirm what actually arrived, before spending anything on looking at it:

    ffprobe -v error -show_entries stream=codec_type,width,height,r_frame_rate,duration \
      -of default=noprint_wrappers=1 output/<id>/take.v2.t1.mp4

Duration, frame rate and the presence of an audio stream are what every later step
assumes. A take that came back at the wrong length or silent is a defective delivery
rather than a bad performance.

## 6. Report the take back

Hand back the file path, the model and parameters used, the references attached,
and what §5 confirmed about the container. That is the whole report.

Do not grade the picture or the performance. Wrong words, a missing element, a
cut, a face that looks off — none of those are this file's to call. What a clip
is worth is `judge.md`'s question, and a first impression is not a cheap version
of the answer.

If the file did not land — no video stream, unreadable, nothing to open — say so.
That is not a take.
