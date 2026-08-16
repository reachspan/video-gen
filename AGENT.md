# AGENT.md

Routing for an agent working in this repo. Find the row that matches what was asked,
read that file, and follow it. Each one owns its procedure end to end.

## Which prompt to follow

| what the user wants | read |
|---|---|
| a reference video turned into a reusable spec and prompt | `prompts/compile.md` |
| an existing recreation changed — swap the character, the setting, a prop | `prompts/compile.md` |
| a face or identity reference image for a character | `prompts/face-gen.md` |
| a generated clip checked, judged, or "is this good enough to ship" | `prompts/judge.md` |
| one defect repaired without re-rolling the whole shot | `prompts/surgery.md` |
| exposure, shake or grain brought closer to the reference | `tools/post.py` |
| to know what tends to go wrong in this format | `docs/pitfalls.md` |
| to understand what the inspection artifacts show | `docs/minesweep.md` |

If the request spans several, the order is:

    compile.md ─┬─→ gate.py ─→ generate ─→ judge.md ─┬─→ surgery.md
    face-gen.md ┘                                    └─→ post.py

## Rules that hold everywhere

- **Metrics point; they do not decide.** Nothing in `vq.py` separates generated
  footage from real — measured against real phone video, a generated clip sits inside
  the real range on every metric. A metric that fires is a place to look. A quiet
  metric is not a pass.
- **Inspect at 4x.** A full frame arrives downsampled, which is how a defect gets
  missed and equally how one gets invented. Anything you cannot resolve at 4x is
  `cannot_tell` — a real answer, and better than a guess in either direction.
- **Record a verdict for everything you were asked to check, including what you
  cleared.** An item with no verdict has not been checked.
- **Never show a red-team or blind judge the intent spec or the prompt.** An agent
  told what the shot should contain will confirm it is there.
- **Run `gate.py` before spending credits.** It is free and it catches the class of
  failure that costs a whole generation.
- **Prices and model names change.** Ask the CLI (`higgsfield model list`,
  `model get`, `generate cost`) rather than trusting a figure written down anywhere,
  including here.

## Tools, one job each

    tools/gate.py     prompt against intent, before generating
    tools/vq.py       signal measurement against a reference clip
    tools/sweep.py    inspection artifacts and the per-pitfall checklist
    tools/post.py     deterministic fixes: exposure, shake, grain
    tools/selftest.py injection tests for the metrics
    tools/vid.py      shared video I/O and sampling
    utils/ig-dl       reference clip downloader

Only `judge.md` decides anything. The tools measure and build evidence; the prompts
under `prompts/` carry the procedures.

## Environment

Run from the repo root, using the venv:

    .venv/bin/python tools/vq.py measure ref.mp4 out.mp4

`VQ_JOBS` caps worker processes for `vq.py` and `selftest.py`; each holds a few
hundred MB of decoded frames, so raise it only if there is memory to spare.

`targets/` holds working specs and prompts. It is gitignored: working state, not
published output.
