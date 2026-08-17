---
name: recreate
description: Recreate a reference video end to end — download it, compile it into a spec, cast it, generate takes and judge them — without stopping to ask. Takes a URL or a file path.
argument-hint: "<url-or-path> [instructions] [--max-credits N] [--model NAME]"
disable-model-invocation: true
---

# recreate

One reference video in, one judged recreation out. **This runs to completion without
asking anything.** The user interrupts if they want it steered; silence is not consent
to stop and check in.

    $ARGUMENTS

The first token is the reference — an Instagram URL or shortcode, another video URL, or
a local file path. Everything after it is instruction. `--max-credits N` overrides the
spend budget and `--model NAME` the video model.

`${CLAUDE_PLUGIN_ROOT}/AGENT.md` routes to the procedure for each step and defines the
file layout. Read each procedure when you reach its step; they own their own detail and
this file does not repeat it. What this file owns is the loop, the budget, the model
default, and every place the procedures would otherwise stop and ask.

**Two roots, and never mix them.** Every procedure and document named anywhere in this
pipeline — `prompts/compile.md`, `docs/pitfalls.md` and the rest — lives under
`${CLAUDE_PLUGIN_ROOT}` and is read-only. Every file a run reads or writes —
`targets/`, `output/` — is relative to the directory the user is working in. Read from
the plugin, write to the project.

## Budget

**150 Higgsfield credits, total, by default.** Override only on explicit instruction —
`--max-credits 400`, or "spend up to 500", or a number in the prose.

Everything billed counts against it, because everything billed comes out of the same
balance: takes, surgery patches, and the face and prop stills alike. A take that comes
back dead still spent its credits. What is free stays free and never counts — the gate,
`post.py`, and every inspection step in `judge.md`.

**Price each call before making it, and never from a number written down here or
anywhere else.** `generate cost` takes the same flags as `generate create`, so price the
call you are about to make rather than a simplified version of it:

    higgsfield generate cost <model> --prompt "$(cat output/<id>/prompt.v2.txt)" \
      <the same flags the call will use, per generation.md §3>

Keep a running total, and check the quote against what is left **before** each call. If
the next call would cross the budget, stop and report rather than starting it and
finding out. Do not top up, and do not switch to a cheaper model to squeeze one more in
unless the user asked for that.

For rough planning only, and stale on arrival: when this was written a take priced
around 36 credits and a still 2–7, so 150 buys roughly four takes and their casting.
The prices move and so do the settings behind them. Ask; do not assume.

Stop when a take ships or the balance cannot cover another call. A run that spends the
budget without shipping still delivers: the best take, the report, and what it would
have tried next.

## Model

**Seedance 2.0 (`seedance_2_0`) for video, unless the user names another** —
`--model NAME`, or "use Kling", or any other model named in the instruction. A named
model wins outright; do not second-guess it or fall back when it costs more.

`generation.md` §3 owns everything else about the call, and its rule holds here: the
lineup turns over, so confirm the model exists and read what it accepts rather than
trusting this page.

    higgsfield model list --video
    higgsfield model get <model>

If the named model does not exist, or `model get` shows it will not take what
`generation.md` §3 asks for, say so, fall back to the default, and record the
substitution in `report.md`. That is a judgement the spec can settle, so it is not a
reason to stop.

`face-gen.md` picks its own image model; this default is for video only.

## Casting

**With no instruction beyond the reference, recast every main character** with a
synthetic identity from `face-gen.md`. That is the default and it does not need
confirming. Given instructions, do what they say, and keep the original cast only if
asked to.

Whether the run is re-casting is the only thing this decides. What that means for which
references get attached is `generation.md` §1's call, and it is made there.

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

Read the credit balance `doctor` prints. If it is below the budget, the balance is the
real ceiling — say so up front and run against that instead.

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

Props may want a still too. `generation.md` §1 says which ones and why; take that
decision from there rather than guessing here.

## 4. Gate

    vg gate output/<id>/spec.json output/<id>/prompt.v<n>.txt

`G1` checks that every required element survived into the prompt; `G2` and `G3` check
that no clause contradicts the premise, the affect or the composition. Revise the prompt
and re-run until it passes. This is free — never spend credits on a prompt that has not
passed it.

## 5. The loop

While the balance can cover another take:

1. **Generate** one take per `${CLAUDE_PLUGIN_ROOT}/prompts/generation.md`, with the
   model from **Model** above, into `output/<id>/take.v<n>.t<k>.mp4`. Cost it first and
   check the quote against what is left. What gets attached is §1's decision; tell it
   whether the run is re-casting and let it choose.
2. **Check the take** — `generation.md` §5 and §6. They say what to confirm and what
   counts as dead; take the verdict from there. If it is dead, record why and loop. A
   dead take still spent its credits, so charge it to the budget like any other.
3. **Judge** per `${CLAUDE_PLUGIN_ROOT}/prompts/judge.md`, in its order — its first
   step is a hard gate and decides whether the rest of it runs at all. If the run stops
   there, revise the spec and the prompt, and loop.
4. **Act on the verdict**, per `judge.md` step 4:
   - **ships** → done. Run `vg post chain` anyway; it is free and it is worth running on
     a clip that already ships. Re-measure, and keep the post pass only if nothing
     visible broke.
   - **signal mismatch only** → `${CLAUDE_PLUGIN_ROOT}/prompts/post.md`. Free, so fix and
     re-judge without spending anything.
   - **a defect in one span, the rest usable** → `${CLAUDE_PLUGIN_ROOT}/prompts/surgery.md`.
     A patch is a paid call; price it against what is left before starting it.
   - **premise or domain broken** → back to `compile.md`, revise, regenerate whole.

Carry what you learned into the next prompt revision rather than re-rolling the same
one; `generation.md` §1 says what to do with a clause that has failed twice.

## 6. Report

Write `output/<id>/report.md` and summarise it in the reply. It must say:

- the ship / do-not-ship call, and the take it refers to
- every call: what was generated, what it cost, what the verdict was, what changed
- **credits spent against the budget**, as a running total and a final figure
- what the blind readers said, against what they said about the reference
- **what was not resolved** — every `cannot_tell` that could have carried severity 4.
  A report that lists only defects is indistinguishable from one that did not look
- every place this file's autonomy table was used, and what was chosen
- what it would have tried next, if the budget ran out

Then print the path to the take that ships, or to the best one if none does.
