# Quality check — entry point

**Start here to evaluate a generated clip.** This file owns the procedure: what to
run, in what order, who does it, and how the answers combine into one decision.

What it consumes, and what each of those does NOT do:

| file | job | does NOT |
|---|---|---|
| `tools/gate.py` | prompt vs intent, before generating | look at pixels |
| `tools/vq.py` | signal measurement against a reference | decide anything |
| `tools/sweep.py` | build inspection artifacts, emit the checklist | judge them |
| `docs/pitfalls.md` | catalogue of what goes wrong in this format | say how to sweep |
| `docs/minesweep.md` | how to read the artifacts, and why they cover the clip | list pitfalls |

`AGENT.md` routes between this and the other procedures. Nothing but this file
decides whether a clip ships.

---

## Stage 0 — before spending credits

    python tools/gate.py targets/X.intent.json targets/X.v<n>.txt

A prompt that fails the gate is not worth generating. Nothing below applies yet.

## Stage 1 — build the evidence

    python tools/vq.py measure   ref.mp4 out.mp4 > measure.json
    python tools/sweep.py plan   out.mp4 ref.mp4 > plan.md
    python tools/sweep.py strips out.mp4 sweep/
    python tools/sweep.py tiles  out.mp4 sweep/
    python tools/sweep.py strips ref.mp4 sweep_ref/     # the control
    python tools/sweep.py tiles  ref.mp4 sweep_ref/

**Build the reference's artifacts too.** A slit-scan is read against the reference's
slit-scan or it is read against nothing: a static background draws straight lines
legitimately, so "straight" only means something next to a clip where it wavers.

Read `warnings` in `measure.json` first. A metric carrying a warning is not
evidence, and a hotspot on a clip whose alignment mostly failed is not a location.
`bg_tiles` deserves the same scepticism even when it does not warn — compare the
candidate's count against the reference's, and treat a large shortfall as a reason to
distrust every permanence number, not just a low absolute count.

## Stage 2 — red team, in parallel

`plan.md` ends with a table of **work packages**. Spawn **one fresh agent per
package, all at once**. Packages are cut by evidence rather than by theme, so every
tile is read by exactly one agent, which answers every question that applies to it —
including reading any text it contains. That is what keeps them genuinely parallel:
a package defined by theme rather than by evidence needs tiles the others already
hold, and sets the pace for the whole run.

Give each package the reference's artifacts alongside the candidate's.

Give each agent exactly this, and nothing else:

- its package name, its pitfall ids, and their rows from `plan.md`
- the paths to the artifacts it needs, and `measure.json`
- the resolution rule below

Do **not** give a red-team agent the intent spec or the prompt. An agent told what
the shot is meant to contain will confirm it is there.

> Inspect at magnification. A whole frame arrives downsampled in your context and
> you will invent defects that are not there. The tiles in `sweep/` are already at
> 4x — open those, do not re-crop the full frame. For anything smaller than a hand,
> confirm it in the tile before reporting it.
>
> Report `cannot_tell` when you cannot resolve something at 4x. It is a real answer
> and it is expected; `clear` means you looked and it was fine.
>
> Return an entry for EVERY pitfall in your package, including the ones you cleared.
> JSON: {package, findings: [{pitfall, verdict: defect|clear|cannot_tell, where:
> [{frame, tile_or_box}], evidence, severity_1_5}]}.
>
> Start at the final sampled frame of your region. Degradation is end-loaded, so the
> tail is where a defect is most likely to be waiting.

`where` is a list, so a pitfall that recurs across tiles or frames records each of
them. Every entry must carry a frame number and a tile or pixel box, so a finding can
be re-opened by someone who did not make it.

If a sub-test inside a pitfall has nothing to bite on — counter-rotation when the
head never turns, a breathing rate on a clip too short to contain two cycles — record
that sub-test as not applicable and judge on the rest. Do not return `cannot_tell`
for a whole pitfall because one of its checks was inapplicable.

## Stage 3 — blind judges, also in parallel

These are separate from the red team: they answer whether the clip *works*, not
whether it is flawed. Run each on the candidate **and on the original as a control**,
in the same batch, shuffled and unlabelled. A judge that has seen the intent spec,
the prompt, or this conversation will find the answer it was given.

If a judge recovers the premise from the original but not the candidate, that is a
clean differential. If it recovers neither, the judge or the framing is at fault,
not the candidate.

**Normalise the files before shuffling.** A raw generator output and a
platform-delivered reference differ several-fold in bitrate and file size, and these
judges are told to run `ffmpeg` — so `ls` or `ffprobe` hands them the answer and the
control is not a control. Re-encode both to one bitrate and strip metadata:

```bash
python3 - <<'EOF'
import random, json, subprocess, pathlib
files = ["dl/orig_4s.mp4", "gen/v4.mp4"]          # extend as needed
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

The re-encode costs a little grain, which is fine: no metric here reads grain
magnitude, and these judges are answering semantic and perceptual questions.

Hand `blind/clip_a.mp4` and `blind/clip_b.mp4` to separate fresh agents, collect
verdicts, and only then open `KEY.json`.

### J1 — semantic reconstruction

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

**Pass:** (4) recovers the spec's `premise` unprompted, (2) recovers each required
prop's `function` rather than merely naming the object, and (5) is consistent with
`performance.affect`. Compare against the spec only *after* the answers are in.

### J2 — is it camera-captured (adversarial)

> You are shown a short vertical video. Your job is to decide whether it was filmed
> on a real camera or generated. Default to "generated" if you are uncertain — a
> confident wrong "real" is the expensive error.
>
> Look specifically at: whether the camera drifts and gets corrected like a hand, or
> jitters randomly; whether background objects stay put, keep their shape, and keep
> their colour; hands, and whether fingers keep the same count and the grip stays
> consistent; whether anything morphs when occluded and re-emerges changed; whether
> thin objects (cable, wire, straps) keep a traceable path end to end.
>
> Do **not** treat corner sharpness falloff or highlight clipping as evidence either
> way. Both were measured across real phone footage and vary more between real clips
> than between real and generated ones.
>
> Return JSON: {verdict: real|generated, confidence: 0-1, strongest_evidence: [...]}.

**Pass:** "real", or "generated" with confidence < 0.6 and no evidence item that a
post pass cannot fix.

### J3 — domain plausibility

Generic by design. A judge told the domain up front will confirm it; let it infer
the domain from the video, then critique from inside that domain.

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
> Inspect at magnification before reporting any detail of an object, logo or text —
> a whole frame arrives downsampled and you will invent faults that are not there:
> `ffmpeg -ss 2 -i clip.mp4 -vf "crop=250:290:30:640,scale=1000:1160" -frames:v 1 r.jpg`
> If you cannot resolve it at 4x, say "cannot tell" instead of reporting it.
>
> Rate each issue 1-5, where 5 = a practitioner would immediately know this was staged
> by someone who has never done the job, and 1 = a harmless quirk. Return JSON:
> {domain, issues: [{what, severity_1_5, verified_at_4x: true|false}], verdict}.

**Pass:** no issue at severity 4+ that is `verified_at_4x`. Read `domain` as a check
in its own right: if the judge cannot name the setting the shot is supposed to
establish, the set dressing has failed regardless of the issue list.

## Stage 4 — consolidate

Collect every package and every judge into one table: pitfall or judge, verdict,
where, severity. Then:

- **Any `defect` at severity 4+, or any failed judge** → do not ship. A semantic
  failure (J1, J3) is a prompt problem: revise the spec via `compile.md` and
  regenerate whole. A signal mismatch is `post.py` and costs nothing. A defect that
  occupies part of the runtime and leaves the rest usable is `surgery.md`.
- **`cannot_tell` on a severity-4-capable pitfall** → resolve it before deciding.
  Re-crop tighter, or say plainly in the report that it went unresolved.
- **Everything else clear** → ship, and record what was swept.

The report must name what was **not** resolved. A sweep that reports only defects
is indistinguishable from one that did not look.

Calibration: run the judges on the reference too, and read its scores as the bar.
A candidate is not being asked to be perfect — it is being asked to reach what the
footage it is recreating already scores.
