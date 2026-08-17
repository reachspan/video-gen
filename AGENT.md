# AGENT.md

Where to look when working in this repo. Find the row that matches what was asked, read
that file, and do what it says. Each file gives the full procedure for its own step;
this one only points at them.

## Which prompt to follow

| what the user wants | read |
|---|---|
| a reference video turned into a reusable spec and prompt | `prompts/compile.md` |
| an existing recreation changed — swap the character, the setting, a prop | `prompts/compile.md` |
| a face or identity reference image for a character | `prompts/face-gen.md` |
| a prompt turned into a clip: which references to attach, and the call | `prompts/generation.md` |
| a generated clip checked, judged, or "is this good enough to ship" | `prompts/judge.md` |
| one defect repaired without re-rolling the whole shot | `prompts/surgery.md` |
| exposure, shake or grain brought closer to the reference | `prompts/post.md` |
| to know what tends to go wrong in this format | `docs/pitfalls.md` |
| to read the artifacts and the metrics, or to know what a delivered file carries besides the picture | `docs/evidence.md` |

If the request covers several steps, this is the order:

    compile.md ─┬─→ gate.py ─→ generation.md ─→ judge.md ─┬─→ surgery.md
    face-gen.md ┘                                         └─→ post.md

`face-gen.md` runs before `generation.md`, not after `compile.md` in particular: every
main character needs an image before a take can be bought.

`generation.md` produces one clip per run. Generation is a numbers game, so expect to
call it repeatedly for the same prompt.

`judge.md` closes the loop. It decides whether a clip ships, and if it does not, which
of the other files the fix belongs in.

## Each instruction lives in one place

This matters when editing as much as when reading. Copies drift, and two files giving
slightly different orders is worse than one file being a little thin.

- **`prompts/` hold the procedures** — what to run, in what order, who runs it, what
  they are allowed to see, and what the answer means.
- **`docs/` are reference material.** `pitfalls.md` lists what goes wrong; `evidence.md`
  explains what the artifacts and the metrics show. Neither tells you what to do, and
  neither points back into `prompts/` — that would make the reading order circular.
- **Tools print their own instructions.** `sweep.py plan` writes the per-pitfall
  procedure and the brief each sweep agent works from, because that text has to make
  sense to an agent with no other context. `judge.md` says who gets it and does not
  repeat it. Every other tool's docstring gives usage and points at `evidence.md`
  rather than restating what its numbers mean.

The blockquoted blocks inside the prompts are text to hand to a subagent word for word,
not instructions for whoever is reading. They repeat things on purpose, because their
reader has no other context.

## Tools, one job each

    tools/gate.py     prompt against intent, before generating
    tools/vq.py       signal measurement against a reference clip
    tools/sweep.py    inspection artifacts and the per-pitfall checklist
    tools/post.py     deterministic fixes: exposure, shake, grain
    tools/selftest.py injection tests for the metrics
    tools/vid.py      shared video I/O and sampling
    utils/ig-dl       reference clip downloader

The tools measure things and build evidence. Only `judge.md` decides anything.

**Prices and model names change.** Ask the CLI — `higgsfield model list`, `model get`,
`generate cost` — instead of trusting a number written down anywhere, including here.

## Environment

Run from the repo root, using the venv:

    .venv/bin/python tools/vq.py measure ref.mp4 out.mp4

`VQ_JOBS` caps worker processes for `vq.py` and `selftest.py`. Each holds a few hundred
MB of decoded frames, so raise it only if there is memory to spare.

`targets/` holds the specs, prompts, reference images and takes for whatever is being
worked on. It is gitignored: working state, not published output.
