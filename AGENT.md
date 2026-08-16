# AGENT.md

Routing for an agent working in this repo. Find the row that matches what was asked,
read that file, and follow it. Each one owns its procedure end to end; this file only
points.

## Which prompt to follow

| what the user wants | read |
|---|---|
| a reference video turned into a reusable spec and prompt | `prompts/compile.md` |
| an existing recreation changed — swap the character, the setting, a prop | `prompts/compile.md` |
| a face or identity reference image for a character | `prompts/face-gen.md` |
| a generated clip checked, judged, or "is this good enough to ship" | `prompts/judge.md` |
| one defect repaired without re-rolling the whole shot | `prompts/surgery.md` |
| exposure, shake or grain brought closer to the reference | `prompts/post.md` |
| to know what tends to go wrong in this format | `docs/pitfalls.md` |
| to read what the artifacts and the metrics show | `docs/evidence.md` |

If the request spans several, the order is:

    compile.md ─┬─→ gate.py ─→ generate ─→ judge.md ─┬─→ surgery.md
    face-gen.md ┘                                    └─→ post.md

`judge.md` is where the loop closes: it decides whether a clip ships and, if it does
not, which of the other three the fix belongs to.

## One home per instruction

Follow it when editing as well as when reading. Duplicated instructions drift, and
two files giving slightly different orders is worse than one file being incomplete.

- **`prompts/` own procedures.** What to run, in what order, who runs it, what they
  are allowed to see, and what the answer means.
- **`docs/` are leaves.** `pitfalls.md` catalogues what goes wrong; `evidence.md`
  explains what the artifacts and metrics show. Neither says what to do, and neither
  points back into `prompts/` — that would make the reading order circular.
- **Tools own their own output.** `sweep.py plan` emits the per-pitfall procedure and
  the brief every sweep agent works from, because that text has to stand alone in a
  fresh agent's context. `judge.md` says who receives it; it does not restate it.

The blockquoted blocks inside the prompts are payloads to hand to a subagent
verbatim, not instructions to whoever is reading. They repeat things on purpose,
because their reader has no other context.

## Tools, one job each

    tools/gate.py     prompt against intent, before generating
    tools/vq.py       signal measurement against a reference clip
    tools/sweep.py    inspection artifacts and the per-pitfall checklist
    tools/post.py     deterministic fixes: exposure, shake, grain
    tools/selftest.py injection tests for the metrics
    tools/vid.py      shared video I/O and sampling
    utils/ig-dl       reference clip downloader

The tools measure and build evidence. Only `judge.md` decides anything.

**Prices and model names change.** Ask the CLI (`higgsfield model list`, `model get`,
`generate cost`) rather than trusting a figure written down anywhere, including here.

## Environment

Run from the repo root, using the venv:

    .venv/bin/python tools/vq.py measure ref.mp4 out.mp4

`VQ_JOBS` caps worker processes for `vq.py` and `selftest.py`; each holds a few
hundred MB of decoded frames, so raise it only if there is memory to spare.

`targets/` holds working specs and prompts. It is gitignored: working state, not
published output.
