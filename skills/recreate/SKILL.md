---
name: recreate
description: Recreate a reference video end to end — download it, compile it into a spec, cast it, generate takes and judge them — without stopping to ask. Takes a URL or a file path.
argument-hint: "<url-or-path> [instructions] [--max-iterations N]"
disable-model-invocation: true
---

# recreate

One reference video in, one judged recreation out. **This runs to completion without
asking anything.** The user interrupts if they want it steered; silence is not consent
to stop and check in.

    $ARGUMENTS

The first token is the reference — an Instagram URL or shortcode, another video URL, or
a local file path. Everything after it is instruction. `--max-iterations N` overrides
the generation budget.

`${CLAUDE_PLUGIN_ROOT}/AGENT.md` routes to the procedure for each step and defines the
file layout. Read each procedure when you reach its step; they own their own detail and
this file does not repeat it. What this file owns is the loop, the budget, and every
place the procedures would otherwise stop and ask.

**Two roots, and never mix them.** Every procedure and document named anywhere in this
pipeline — `prompts/compile.md`, `docs/pitfalls.md` and the rest — lives under
`${CLAUDE_PLUGIN_ROOT}` and is read-only. Every file a run reads or writes —
`targets/`, `output/` — is relative to the directory the user is working in. Read from
the plugin, write to the project.

## Budget

**Three video generations, total, by default.** Override only on explicit instruction —
`--max-iterations 5`, or "keep going until it's right", or a number in the prose.

What counts against it:

- a take from `generation.md` — counts, including one that comes back dead
- a surgery patch — counts; it is a video generation like any other
- a face or prop still — does **not** count, but cap stills at 3 per subject
- anything `post.py` does — does not count, it is free and deterministic

Stop when a take ships or the budget is gone, whichever comes first. A run that spends
the budget without shipping still delivers: the best take, the report, and what it
would have tried next.

## Casting

**With no instruction beyond the reference, recast every main character** with a
synthetic identity from `face-gen.md`. That is the default and it does not need
confirming. It follows that the run is re-casting, so `generation.md` §1 says leave the
reference clip off — the prompt carries the camera and the room instead.

Given instructions, do what they say. Keep the original cast only if asked to; then the
reference clip becomes available again on `generation.md`'s terms.

## Autonomy

Every procedure this calls was written for someone who can stop and ask. None of them
can here. Where one says to ask, this is the answer:

| where | it says | do this instead |
|---|---|---|
| `compile.md` §6 | ask when a change contradicts a `required` element's `function` | keep the element, apply the rest of the change, and record the conflict in `report.md` |
| `face-gen.md` "Steering from the user" | edit the prompt and regenerate on request | accept the first still that clears the inspection checklist; re-roll at most 3 times, then take the best and note it |
| `generation.md` §6 | whoever called it decides whether to buy another | the loop below decides, against the budget |
| `judge.md` step 4 | ship or not, and which fix | the loop below acts on it without confirming |

Two things still stop the run, because neither is a judgement call:

- **preflight fails** — a missing dependency or an expired login. Nothing has been spent
  yet and nothing can be. Report exactly what is missing and stop.
- **the reference cannot be fetched or read.** Same: report and stop.

Never stop for anything else. If a step is ambiguous, choose the reading the spec
supports, write down that you chose it, and keep going.

## 0. Preflight, before spending anything

    vg doctor

Every line must read `OK`. It checks the interpreter and its packages, `ffmpeg` and
`ffprobe`, the `higgsfield` CLI, and that the account is authenticated with credits on
it. On a first run `vg setup` builds the environment; run it if `doctor` says to.

If authentication is what is missing, `higgsfield auth login` is interactive and opens a
browser — you cannot complete it. Stop and tell the user to run it. There is no API-key
mode to fall back on.

Read the credit balance `doctor` prints. If it will not cover the budget at the price
`generate cost` quotes in step 5, say so before starting rather than halfway through.

## 1. Get the reference

Derive an **id** from the input and use it everywhere: an Instagram shortcode as-is, a
URL's last meaningful path segment, or a local file's basename without extension. Reduce
it to letters, digits, `-` and `_`.

    mkdir -p targets output/<id>

Then fetch, by input kind:

    vg ig-dl <url|shortcode> -o targets/     # instagram reels, posts, carousels
    curl -L -o targets/<id>.mp4 '<url>'      # a direct video URL
    cp <path> targets/<id>.mp4               # a local file

For any other kind of page, use whatever downloader is on the system; `yt-dlp -o
'targets/<id>.%(ext)s'` if it is there. If nothing can fetch it, stop — that is the
second of the two stopping conditions.

**`targets/` holds the original and nothing else.** Every file the run produces goes
under `output/<id>/`, laid out as `AGENT.md` describes. Never write a spec, a prompt, a
still or a take into `targets/`.

Confirm what landed before compiling it:

    ffprobe -v error -show_entries stream=codec_type,width,height,r_frame_rate,duration \
      -of default=noprint_wrappers=1 targets/<id>.mp4

If the reference is long, pick the segment worth recreating and record it in the spec's
`segment`. Compile that span, not the whole file.

## 2. Compile

Follow `${CLAUDE_PLUGIN_ROOT}/prompts/compile.md` in full, including the red-team pass in §4 — it
is free, it runs on the reference rather than on a generation, and it is the step that
stops a misread from costing the whole budget. Write `spec.json` and `prompt.v1.txt`
into `output/<id>/`.

## 3. Cast

For each main character the spec names, follow `${CLAUDE_PLUGIN_ROOT}/prompts/face-gen.md`
and write the still to `output/<id>/ref.<name>.png`. Reuse one file per character for
every take; do not regenerate a character between iterations, or two takes cannot be
cut together.

A prop the spec marks `required` whose geometry matters gets a still too, on
`generation.md` §1's terms.

## 4. Gate

    vg gate output/<id>/spec.json output/<id>/prompt.v<n>.txt

`G1` checks that every required element survived into the prompt; `G2` and `G3` check
that no clause contradicts the premise, the affect or the composition. Revise the prompt
and re-run until it passes. This is free — never spend a generation on a prompt that has
not passed it.

## 5. The loop

Up to the budget, once per iteration:

1. **Generate** one take per `${CLAUDE_PLUGIN_ROOT}/prompts/generation.md`,
   into `output/<id>/take.v<n>.t<k>.mp4`. Cost it first. Attach the identity stills;
   attach the reference clip only if §1's terms are met, which recasting rules out.
2. **Check the container** — `generation.md` §5. A take at the wrong length, silent, or
   without the scripted line is dead. Record why, spend the next iteration, do not judge
   it.
3. **Judge** per `${CLAUDE_PLUGIN_ROOT}/prompts/judge.md`, in its order. Meaning first
   and blind: if the candidate loses the premise where the reference holds it, do not
   build the sweep artifacts — revise the spec and the prompt, and spend the next
   iteration.
4. **Act on the verdict**, per `judge.md` step 4:
   - **ships** → done. Run `vg post chain` anyway; it is free and it is worth running on
     a clip that already ships. Re-measure, and keep the post pass only if nothing
     visible broke.
   - **signal mismatch only** → `${CLAUDE_PLUGIN_ROOT}/prompts/post.md`. Free, so fix and
     re-judge without spending an iteration.
   - **a defect in one span, the rest usable** → `${CLAUDE_PLUGIN_ROOT}/prompts/surgery.md`.
     Costs an iteration.
   - **premise or domain broken** → back to `compile.md`, revise, regenerate whole.
     Costs an iteration.

Carry what you learned into the next prompt revision rather than re-rolling the same
one: a clause that failed twice becomes a reference image, per `generation.md` §1.

## 6. Report

Write `output/<id>/report.md` and summarise it in the reply. It must say:

- the ship / do-not-ship call, and the take it refers to
- every iteration: what was generated, what it cost, what the verdict was, what changed
- what the blind readers said, against what they said about the reference
- **what was not resolved** — every `cannot_tell` that could have carried severity 4.
  A report that lists only defects is indistinguishable from one that did not look
- every place this file's autonomy table was used, and what was chosen
- what the next iteration would have tried, if the budget ran out

Then print the path to the take that ships, or to the best one if none does.
