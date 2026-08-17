Index. Open the matching file; it owns the step.

## Which prompt to follow

| what the user wants | read |
|---|---|
| a reference video turned into a reusable spec and prompt | `prompts/compile.md` |
| an existing recreation changed — swap the character, the setting, a prop | `prompts/compile.md` |
| a face or identity reference image for a character | `prompts/face-gen.md` |
| a reference photograph for a prop, tool or product | `prompts/prop-ref.md` |
| a prompt turned into a clip: which references to attach, and the call | `prompts/generation.md` |
| a generated clip checked, judged, or "is this good enough to ship" | `prompts/judge.md` |
| one defect repaired without re-rolling the whole shot | `prompts/surgery.md` |
| exposure, shake or grain brought closer to the reference | `prompts/post.md` |
| a prompt written or revised: which register a constraint goes in, the blocks, the timeline | `docs/prompt-language.md` |
| to know what tends to go wrong in this format | `docs/pitfalls.md` |
| to read the artifacts and the metrics, or to know what a delivered file carries besides the picture | `docs/evidence.md` |

If the request covers several steps, this is the order:

    compile.md ─┬─→ gate.py ─→ generation.md ─→ judge.md ─┬─→ surgery.md
    face-gen.md ┤                                         └─→ post.md
    prop-ref.md ┘

`face-gen.md` and `prop-ref.md` run before `generation.md`, not after `compile.md` in
particular: every main character needs an image, and every prop worth pinning needs a
photograph, before a take can be bought. `face-gen.md` generates its image and is a paid
call; `prop-ref.md` finds a photograph of a real object and is free.

`generation.md` produces one clip per run. Call it repeatedly for the same prompt.

`judge.md` closes the loop. It decides whether a clip ships, and if it does not, which
of the other files the fix belongs in.

## Each instruction lives in one place

This matters when editing as much as when reading. Copies drift, and two files giving
slightly different orders is worse than one file being a little thin.

- **`prompts/` hold the procedures** — what to run, in what order, who runs it, what
  they are allowed to see, and what the answer means.
- **`docs/` are reference material.** `prompt-language.md` gives the language a prompt is
  written in; `pitfalls.md` lists what goes wrong; `evidence.md` explains what the
  artifacts and the metrics show. None of them tells you what to do, and none points back
  into `prompts/` — that would make the reading order circular. `prompt-language.md` is
  cited from every step that writes or revises a prompt, so it stays one copy.
- **Tools print their own instructions.** `sweep.py plan` writes the per-pitfall
  procedure and the brief each sweep agent works from, because that text has to make
  sense to an agent with no other context. `judge.md` says who gets it and does not
  repeat it. Every other tool's docstring gives usage and points at `evidence.md`
  rather than restating what its numbers mean.

The blockquoted blocks inside the prompts are text to hand to a subagent word for word,
not instructions for whoever is reading. They repeat things on purpose, because their
reader has no other context.

## Tools, one job each

    vg gate       tools/gate.py      prompt against intent, before generating
    vg vq         tools/vq.py        signal measurement against a reference clip
    vg sweep      tools/sweep.py     inspection artifacts and the per-pitfall checklist
    vg post       tools/post.py      deterministic fixes: exposure, shake, grain
    vg selftest   tools/selftest.py  injection tests for the metrics
    vg ig-dl      utils/ig-dl        reference clip downloader
                  tools/vid.py       shared video I/O and sampling

The tools measure things and build evidence. Only `judge.md` decides anything.

**Prices and model names change.** Ask the CLI — `higgsfield model list`, `model get`,
`generate cost` — instead of trusting a number written down anywhere, including here.

## Environment

`vg` runs the bundled tools with the bundled interpreter, wherever this is installed:

    vg vq measure ref.mp4 out.mp4
    vg doctor      every dependency, and whether the CLI is logged in
    vg setup       build the environment; needed once, on a first run

Installed as a plugin it is already on `PATH`. From a checkout, call `bin/vg` or put
`bin/` on `PATH`.

`VQ_JOBS` caps worker processes for `vq.py` and `selftest.py`. Each holds a few hundred
MB of decoded frames, so raise it only if there is memory to spare.

## Where files go

    targets/<id>.mp4    the original reference, and nothing else
    output/<id>/        everything a run produces

Keeping references separate is what lets a run be thrown away and repeated without
fetching anything again. Inside `output/<id>/`:

    spec.json                      the intent spec                   compile.md
    prompt.v<n>.txt                each prompt revision              compile.md
    ref.<name>.png                 one identity still or prop photo  face-gen.md / prop-ref.md
    ref.<name>.source.txt          where a sourced photograph came from  prop-ref.md
    seg.mp4                        the reference segment, if one was cut
    take.v<n>.t<k>.mp4             the takes                         generation.md
    take.v<n>.t<k>.selected.mp4    the delivered take                SKILL.md
    measure.json plan.md           the evidence                      judge.md
    sweep/ sweep_ref/              the artifacts, candidate and control  judge.md
    blind/                         the shuffled pair and its key     judge.md
    report.md                      the decision, and what went unresolved

Both directories are gitignored: working state, not published output.
