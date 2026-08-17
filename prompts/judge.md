This file decides whether a take ships.

Run the candidate and the reference through the same steps and read the difference.
Blind readers watch both, shuffled. The sweep builds both clips' artifacts.

Measurements (`vg vq`, sweep artifacts) are auxiliary diagnostics: they show where
the candidate departs from the reference. They are not sufficient discriminators —
a generated clip can land inside the real range on every metric (`docs/evidence.md`).
The bar is what the reference already scores, not perfection.

`pitfalls.md` names the tells. `vg sweep plan` is the per-clip procedure.

    1  meaning     does it still mean what the reference meant?    blind   → fail: stop here
    2  notice      does a fresh viewer clock it as generated?     blind   → spawned with 1, read at 4
    3  defects     what is wrong, and exactly where?              4x, whole-clip coverage
    4  decision    ship or not; if not, which fix

**Meaning first, and it is a hard gate.** A lost premise is fixed by revising the spec
and regenerating whole — which discards every step 3 artifact. No measurement here can
see it, so a viewer has to.

Do not hunt located defects in steps 1 or 2. That is step 3, at 4x, with stated
coverage. A reader hunting the same tells on a downsampled whole clip invents some
and misses more.

---

## Setup — the blind pair

Steps 1 and 2 run on the same two files, so prepare them once.

**Normalise before shuffling.** A raw generator output and a platform-delivered
reference differ several-fold in bitrate and file size, and these readers are told to
run `ffmpeg` — so `ls` or `ffprobe` hands them the answer and the control stops being
a control. Re-encode both to one bitrate and strip metadata:

```bash
python3 - <<'EOF'
import random, json, subprocess, pathlib
files = ["ref.mp4", "out.mp4"]                    # extend as needed
names = ["clip_a.mp4", "clip_b.mp4"]
random.shuffle(files)
pathlib.Path("blind").mkdir(exist_ok=True)
for src, dst in zip(files, names):
    subprocess.run(["ffmpeg", "-v", "error", "-i", src,
                    "-c:v", "libx264", "-b:v", "2000k", "-pix_fmt", "yuv420p",
                    "-map_metadata", "-1", "-an",
                    f"blind/{dst}", "-y"], check=True)
json.dump(dict(zip(names, files)), open("blind/KEY.json", "w"))   # do not read yet
EOF
```

The re-encode costs a little grain, which is fine: nothing in steps 1 or 2 reads grain
magnitude.

Three readings, two clips: spawn **six fresh agents at once**, one reading per clip.
Open `KEY.json` only when every answer is in.

Give a reader nothing but its own prompt and its own file. No spec, no prompt text, no
conversation, no sight of another reader's answers. A reader told what the shot is
meant to contain will confirm it is there.

---

## Step 1 — meaning

Two readings. The **viewer** says what the video is and what it is for; the
**practitioner** says whether the activity depicted is how that job is actually done.
Between them they cover `S1`–`S5`.

### The viewer — `S1`, `S2`, `S3`

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
> 2. Is the person holding or using anything? What is it, and why?
> 3. Is anything else in the frame that seems significant? Check the frame edges.
> 4. What is the point of this video — what is it for, and what effect is it going
>    for?
> 5. How would you describe the person's mood and demeanour in three words?
>
> If you cannot answer any question from the video, say "cannot tell" rather than
> inferring. Return JSON: {happening, prop_and_why, edges, purpose, mood}.

Open the spec only once the answers are in, then check: (4) recovers `premise`
unprompted, (2) recovers each required prop's `function` rather than merely naming the
object, (3) finds the `required` elements at the frame edges, and (5) is consistent
with `performance.affect`.

### The practitioner — `S4`, `S5`

Generic by design. A reader told the domain up front will confirm it; let it infer the
domain from the video, then critique from inside that domain.

> You are shown a short vertical video. Watch it and answer in two steps.
>
> First: what setting is this, and what occupation, hobby or activity does the person
> appear to be engaged in? Name it as specifically as the video supports.
>
> Second: assume you are an experienced practitioner of exactly that thing, with years
> on the job. What in this video would make you wince, squint, or say "that's not how
> you'd do it"? Consider the tools and equipment and whether they are the ones actually
> used; whether they are held, worn and operated correctly; whether they are the right
> size for the task and the person; clothing and protective gear; the state of the
> workspace; branding and labelling on anything visible; and whether the activity shown
> would accomplish anything.
>
> Judge the choices, not the rendering. A smeared label, a hand that changes shape
> between frames, an object that flickers — those are not what this question is about,
> and reporting them costs you the one you were asked for. What is asked is whether
> the thing depicted is how the job is actually done.
>
> Inspect at magnification before reporting any detail of an object, logo or text —
> a whole frame arrives downsampled and you will invent faults that are not there:
> `ffmpeg -ss 2 -i clip.mp4 -vf "crop=250:290:30:640,scale=1000:1160" -frames:v 1 r.jpg`
> If you cannot resolve it at 4x, say "cannot tell" instead of reporting it.
>
> Rate each issue 1-5, where 5 = a practitioner would immediately know this was staged
> by someone who has never done the job, and 1 = a harmless quirk. Return JSON:
> {domain, issues: [{what, severity_1_5, verified_at_4x: true|false}], verdict}.

Passes when no issue at severity 4+ is `verified_at_4x`. Read `domain` as a check in
its own right: if the practitioner cannot name the setting the shot was supposed to
establish, the set dressing has failed regardless of the issue list.

### The gate

Compare each reading against the same reading of the reference, never against an
absolute standard.

- **The original passes and the candidate does not** → **stop here.** Name which of
  `S1`–`S5` failed and hand it back to `compile.md`: the spec or the prompt is wrong
  and the shot needs regenerating whole. Do not build the step 3 artifacts — they
  would describe a clip that is about to be replaced.
- **Both fail the same way** → the reading or the framing is at fault, not the
  candidate. Fix that and re-run before reading anything into the result.
- **Both pass** → continue. Note where the candidate came out thinner than the
  original even if it cleared; that is where a regeneration would be aimed next.

---

## Step 2 — notice

One reading, the **skeptic**, on both clips, spawned in the same batch as step 1.

Not a defect hunt — those are step 3 packages at 4x. A reader given that list at
whole-frame resolution returns worse answers about the same things. Give it no list.
What it uniquely provides is the reaction of someone who has not been told what to
look for, which is the reaction the clip will actually get.

> You are shown a short vertical video. Decide whether it was filmed on a real camera
> or generated, from watching it — not from hunting for artifacts. Default to
> "generated" if you are uncertain: a confident wrong "real" is the expensive error.
>
> Say what drove your answer, in the order it occurred to you rather than in order of
> how damning it sounds. If nothing in particular drove it, say so — "it just looks
> like a phone video" is a real answer, and so is "something is off and I cannot name
> it".
>
> Do **not** treat corner sharpness falloff or highlight clipping as evidence either
> way: both were measured across real phone footage and vary more between real clips
> than between real and generated ones. Do **not** count fingers — malformed geometry
> outnumbers extra parts about 8 to 1, so a finger count is a distraction.
>
> Return JSON: {verdict: real|generated, confidence: 0-1, what_drove_it: [...]}.

**No pass mark, and it does not gate.** The skeptic is told to default to "generated",
so it calls real footage generated often enough that the absolute rate is noise.
What carries is the difference between the two clips.

Used twice, adjudicates nothing either time: `what_drove_it` orders step 3; the
differential is read against the table in step 4.

---

## Step 3 — defects

Only reached if step 1 passed. Build both clips' evidence, then dispatch the sweep.

    vg vq measure   ref.mp4 out.mp4 > measure.json
    vg sweep plan   out.mp4 ref.mp4 > plan.md
    vg sweep strips out.mp4 sweep/
    vg sweep tiles  out.mp4 sweep/
    vg sweep strips ref.mp4 sweep_ref/     # the control
    vg sweep tiles  ref.mp4 sweep_ref/

**The reference's artifacts are not optional.** A slit-scan is read against the
reference's slit-scan or it is read against nothing.

Read `warnings` in `measure.json` before quoting any number from it, and read
`docs/evidence.md` if you have not: it says which numbers survive which conditions,
and it is what stops a warned metric from being reported as a finding.

`plan.md` ends with a table of **work packages**. Spawn **one fresh agent per package,
all at once**. Packages are cut by evidence rather than by theme, so every tile is read
by exactly one agent, which answers every question that applies to it — including
reading any text it contains. That is what keeps them genuinely parallel: a package
defined by theme needs tiles the other packages already hold, and sets the pace for
the whole run.

Give each agent exactly this, and nothing else:

- its package name, its pitfall ids, and their rows from `plan.md`, including the
  rules `plan.md` states for every package — those travel with the rows, so do not
  restate them here
- the paths to its artifacts, the reference's matching artifacts, and `measure.json`
- `docs/evidence.md`

Order the packages by the skeptic's `what_drove_it` when it named anything specific:
spawn them all regardless, but read those reports first.

Do **not** give a sweep agent the intent spec, the prompt, any reader's answers from
steps 1 and 2, or this file. An agent told what the shot is meant to contain will
confirm it is there, and one told what the skeptic thought it saw will find that
instead of looking.

Every finding carries a frame number and a tile or pixel box. `where` is a list, so a
pitfall recurring across tiles or frames records each occurrence — and a finding
without a location cannot be re-opened by anyone who did not make it.

---

## Step 4 — decision

Collect every package into one table: id, verdict, where, severity. Step 1 already had
its say at the gate; what arrives here unspent is the skeptic. Worst first:

- **Any `defect` at severity 4+** → do not ship, and name the class of fix. A semantic
  failure (`S1`–`S5`) is a prompt problem: revise the spec per `compile.md` and
  regenerate whole per `generation.md`. A signal mismatch is `post.md`, and it is free.
  A defect that occupies
  part of the runtime and leaves the rest usable is `surgery.md`.
- **`cannot_tell` on a pitfall that could carry severity 4** → resolve it before
  deciding. Re-crop tighter, or say plainly in the report that it went unresolved.
- **Everything else clear** → ship, and record what was swept.

Then read the skeptic against that table — as a check on the sweep, not on the clip:

- **It separated the two clips, and everything in `what_drove_it` appears in the table
  as a located finding.** Consistent; fix by severity as above.
- **It separated them and named something the table does not contain.** The sweep
  missed what a viewer noticed first. Go back and look before writing a verdict — this
  is the one result that invalidates a clean table instead of confirming it. The same
  applies when it named nothing at all and simply said something was off: a fresh
  reader's unnamed unease against a table full of `clear` is a reason to re-open, not
  to overrule them.
- **It could not separate them**, either way round → the axis is uninformative on this
  pair. Record that and decide on the table alone. It is not a pass and not a failure.

The report must name what was **not** resolved. A sweep that reports only defects is
indistinguishable from one that did not look.
