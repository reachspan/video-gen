# Blind judge prompts

Spawn a FRESH agent per judge. Never reuse a judge that has seen the intent spec,
the prompt, or this conversation — a judge that knows the answer will find it.

## Resolution discipline — read before writing any judge prompt

Images are resized on the way into a model's context. A full 720x1280 frame, or a
large crop of one, arrives downsampled, and **anatomy and small-text defects get
invented at low resolution**. Fine detail must be delivered as a tight crop of a
small region, upscaled, one region per image:

    ffmpeg -ss 2 -i clip.mp4 -vf "crop=250:290:30:640,scale=1000:1160:flags=lanczos" \
      -frames:v 1 -q:v 2 region.jpg

Every judge prompt must instruct this explicitly. Treat any defect claimed from a
whole-frame view as a hypothesis to re-check at 4x before acting on it. Hands,
fingers, tool branding and text have all produced false positives this way.

Always run each judge on the **original as a control** in the same batch, with the
files shuffled and unlabelled. If a judge recovers the premise from the original
but not from the candidate, that is a clean differential. If it recovers neither,
the judge or the framing is at fault, not the candidate.

---

## J1 — semantic reconstruction (catches the v1 class of failure)

> You are shown a short vertical video. Watch it and answer plainly, from the video
> alone. Do not guess at what it might be intended to be.
>
> Inspect at magnification. A whole frame arrives downsampled in your context and
> you will invent defects that are not there. For anything involving hands, faces,
> text or small objects, crop a tight region and upscale it before looking:
> `ffmpeg -ss 2 -i clip.mp4 -vf "crop=250:290:30:640,scale=1000:1160" -frames:v 1 r.jpg`
> If you cannot resolve a detail at 4x, say "cannot tell" rather than reporting it.
>
> 1. What is physically happening in this shot?
> 2. The person is holding something. What is it, and why are they holding it?
> 3. Is anything else in the frame that seems significant? Check the frame edges.
> 4. What is the point of this video — what is it for, and is it trying to be funny?
> 5. How would you describe the person's mood and demeanour in three words?
>
> If you cannot answer any question from the video, say "cannot tell" rather than
> inferring. Return JSON: {happening, prop_and_why, edges, purpose, mood}.

**Pass condition:** the answer to (4) recovers coercion/duress/hostage-parody
without prompting, and (5) is not positive-valence.

---

## J2 — is it camera-captured (adversarial)

> You are shown a short vertical video. Your job is to decide whether it was filmed
> on a real camera or generated. Default to "generated" if you are uncertain — a
> confident wrong "real" is the expensive error.
>
> Look specifically at: whether sharpness falls off toward the frame corners the way
> a lens behaves; whether the bright window clips to featureless white the way a
> sensor does; whether the camera drifts and gets corrected like a hand, or jitters
> randomly; whether background objects stay put; hands, and whether fingers keep the
> same count and the grip stays consistent; whether anything morphs when occluded.
>
> Return JSON: {verdict: real|generated, confidence: 0-1, strongest_evidence: [...]}.

**Pass condition:** verdict "real", or "generated" with confidence < 0.6 and no
evidence item that a post pass cannot fix.

---

## J3 — trade plausibility

> You are shown a short vertical video of someone at a building site or workshop.
> Assume you are a working electrician or builder. What in this video would make you
> wince or look twice? Consider tools, wiring, materials, workwear, and whether the
> work shown makes sense. Return JSON: {issues: [{what, severity_1_5}], verdict}.

**Pass condition:** no issue at severity 4+.

---

## Running them

Shuffle and strip labels first, and keep the key out of your own context until
after the verdicts are in:

```bash
python3 - <<'EOF'
import random, json, shutil, pathlib
files = ["dl/orig_4s.mp4", "gen/v2.mp4"]          # extend as needed
names = ["clip_a.mp4", "clip_b.mp4"]
random.shuffle(files)
pathlib.Path("blind").mkdir(exist_ok=True)
for src, dst in zip(files, names):
    shutil.copy(src, f"blind/{dst}")
json.dump(dict(zip(names, files)), open("blind/KEY.json", "w"))   # do not read yet
EOF
```

Then hand `blind/clip_a.mp4` and `blind/clip_b.mp4` to separate fresh agents, collect
verdicts, and only then open `KEY.json`.
