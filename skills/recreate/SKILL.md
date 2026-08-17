---
name: recreate
description: Recreate a reference video end to end — download it, compile it into a spec, cast it, generate takes and judge them — without stopping to ask. Takes a URL or a file path.
argument-hint: "<url-or-path> [instructions] [--max-credits N] [--model NAME]"
disable-model-invocation: true
---

One reference in, one judged recreation out. Runs to completion without asking.
The user interrupts if they want it steered.

    $ARGUMENTS

First token = reference (Instagram URL or shortcode, other video URL, or local path).
Rest = instruction. `--max-credits N` and `--model NAME` override defaults.

Read each procedure when you reach it (`${CLAUDE_PLUGIN_ROOT}/…`). This file owns
the loop, the budget, the model default, and the answers where a procedure would
stop and ask.

Two roots. Procedures and docs live under `${CLAUDE_PLUGIN_ROOT}` and are read-only.
`targets/` and `output/` are in the user's cwd. Read from the plugin, write to the
project.

## Budget

**150 Higgsfield credits, total, by default.** Override only on explicit instruction —
`--max-credits 400`, or "spend up to 500", or a number in the prose.

Everything billed counts: takes, surgery patches, casting stills. A dead take still
spent its credits. Free and never counted: the gate, `post.py`, a prop photograph
(`prop-ref.md`), and every `judge.md` inspection.

Price each call with `generate cost` using the same flags as the create
(`generation.md` §3; prices: `AGENT.md`):

    higgsfield generate cost <model> --prompt "$(cat output/<id>/prompt.v2.txt)" \
      <the same flags the call will use, per generation.md §3>

Keep a running total. If the next call would cross the budget, stop and report.
Do not top up or switch models to squeeze one more in unless asked.

Stop when a take ships or the balance cannot cover another call. A run that spends the
budget without shipping still delivers: the best take, the report, and what it would
have tried next.

## Model

**Seedance 2.0 (`seedance_2_0`) for video, unless the user names another** —
`--model NAME`, or "use Kling", or any other model named in the instruction. A named
model wins outright; do not second-guess it or fall back when it costs more.

`generation.md` §3 owns the call. Confirm the model exists and read what it accepts:

    higgsfield model list --video
    higgsfield model get <model>

If the named model does not exist, or `model get` shows it will not take what
`generation.md` §3 asks for, say so, fall back to the default, and record the
substitution in `report.md`. Keep going.

`face-gen.md` picks its own image model; this default is for video only.

## Casting

**With no instruction beyond the reference, recast every main character** with a
synthetic identity from `face-gen.md`. That is the default; do not confirm it.
Given instructions, do what they say, and keep the original cast only if asked.

This decides only whether the run is re-casting. What that means for attachments
is `generation.md` §1.

## Autonomy

This run cannot stop to ask. Where a procedure says to ask, do this instead:

| where | it says | do this instead |
|---|---|---|
| `compile.md` §6 | ask when a change contradicts a `required` element's `function` | keep the element, apply the rest of the change, and record the conflict in `report.md` |
| `face-gen.md` "Steering from the user" | edit the prompt and regenerate on request | accept the first still that clears the inspection checklist; re-roll at most 3 times, then take the best and note it |
| `generation.md` §6 | whoever called it decides whether to buy another | the loop below decides, against the budget |
| `judge.md` step 4 | ship or not, and which fix | the loop below acts on it without confirming |

Stop only for:

- **preflight fails** — missing dependency or expired login. Nothing spent. Report
  and stop.
- **the reference cannot be fetched or read.** Report and stop.

If a step is ambiguous, choose the reading the spec supports, write it down, and
keep going.

## 0. Preflight, before spending anything

    vg doctor

Every line must read `OK`. It checks the interpreter and its packages, `ffmpeg` and
`ffprobe`, the `higgsfield` CLI, and that the account is authenticated. On a first run
`vg setup` builds the environment; run it if `doctor` says to.

If authentication is what is missing, `higgsfield auth login` is interactive and opens a
browser — you cannot complete it. Stop and tell the user to run it. There is no API-key
mode to fall back on.

`doctor` says whether the account is authenticated; it does not report a balance. If the
balance turns out to be lower than the budget, the balance is the real ceiling — say so
and run against that instead.

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

Follow `${CLAUDE_PLUGIN_ROOT}/prompts/compile.md` in full, including §4.
Write `spec.json` and `prompt.v1.txt` into `output/<id>/`.

## 3. Cast

For each main character the spec names, follow `${CLAUDE_PLUGIN_ROOT}/prompts/face-gen.md`
and write the still to `output/<id>/ref.<name>.png`. Reuse that file (`face-gen.md`).

Props: `generation.md` §1 decides which; `${CLAUDE_PLUGIN_ROOT}/prompts/prop-ref.md`
finds the photograph. Free, so an object that clears §1 gets one regardless of budget.

## 4. Gate

    vg gate output/<id>/spec.json output/<id>/prompt.v<n>.txt

Follow `compile.md` §7 until it passes.

## 5. The loop

While the balance can cover another take:

1. **Generate** one take per `${CLAUDE_PLUGIN_ROOT}/prompts/generation.md`, with the
   model from **Model** above, into `output/<id>/take.v<n>.t<k>.mp4`. Cost it first and
   check the quote against what is left. What gets attached is §1's decision; tell it
   whether the run is re-casting and let it choose.
2. **Check the take** per `generation.md` §5–6. Dead → record why and loop. Charge
   it to the budget like any other.
3. **Judge** per `${CLAUDE_PLUGIN_ROOT}/prompts/judge.md`, in its order — step 1 is
   a hard gate. If it stops there, revise the spec and the prompt, and loop.
4. **Act on the verdict**, per `judge.md` step 4:
   - **ships** → done. Run `vg post chain` into `take.v<n>.t<k>.post.mp4`; it is
     free and worth running on a clip that already ships. Re-measure, and keep the
     post pass only if nothing visible broke.
   - **signal mismatch only** → `${CLAUDE_PLUGIN_ROOT}/prompts/post.md`. Free, so fix and
     re-judge without spending anything.
   - **a defect in one span, the rest usable** → `${CLAUDE_PLUGIN_ROOT}/prompts/surgery.md`.
     A patch is a paid call; price it against what is left before starting it.
   - **premise or domain broken** → back to `compile.md`, revise, regenerate whole.

Carry what you learned into the next prompt revision rather than re-rolling the same
one; `generation.md` §1 says what to do with a clause that has failed twice.

Write the revision in the register `${CLAUDE_PLUGIN_ROOT}/docs/prompt-language.md` names.

When a take ships and `vg post chain` is kept, that post file is the delivered clip.
Otherwise the delivered clip is the shipped take, or the best take if none shipped.

## 6. Select

Rename the delivered clip to `take.v<n>.t<k>.selected.mp4` (same `v` and `t` as
the take, even if the file you kept is the `.post.` pass). Leave every other take
as `take.v<n>.t<k>.mp4`. One `.selected.` file, always.

## 7. Report

Write `output/<id>/report.md` and summarise it in the reply. It must say:

- the ship / do-not-ship call, and the `.selected.` take it refers to
- every call: what was generated, what it cost, what the verdict was, what changed
- **credits spent against the budget**, as a running total and a final figure
- what the blind readers said, against what they said about the reference
- **what was not resolved** — every `cannot_tell` that could have carried severity 4
  (`judge.md` step 4)
- every place this file's autonomy table was used, and what was chosen
- what it would have tried next, if the budget ran out

Then print the path to `output/<id>/take.v<n>.t<k>.selected.mp4`.
