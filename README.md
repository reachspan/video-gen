# video-gen

Agent-facing video tooling: download reference reels, recreate them with AI
generation, and measure how close the result is to camera-captured footage.

## ig-dl

Download Instagram reels, posts and carousels. Single file, stdlib only, no dependencies.

```bash
utils/ig-dl <url|shortcode>... [-o DIR] [--cookies FILE] [--json]
```

- **stdout** — saved paths, one per line, flushed as they land
- **stderr** — errors, and `--json` metadata (owner, caption, duration, views, timestamp)
- **exit 1** if any URL failed; remaining URLs in the batch still download

Accepts `/p/`, `/reel/`, `/reels/` and `/tv/` URLs or a bare shortcode. Carousels save as
`<code>_1.jpg`, `<code>_2.mp4`; single posts as `<code>.mp4`. Use `--cookies` with a
Netscape-format file for private or age-gated posts.

Instagram rotates the GraphQL `doc_id` this depends on. When all the built-in ones go stale
the tool says so explicitly; pull a fresh `doc_id` from a browser DevTools capture of a reel
page load and prepend it to `DOC_IDS`.

## Evaluation suite

    prompts/judge.md ENTRY POINT — the quality-check procedure, start here
    prompts/compile.md  reference video → intent spec + prompt, and how to swap parts
    prompts/face-gen.md building a character reference image that reads as real
    prompts/surgery.md  repairing a localized defect without re-rolling the shot
    utils/ig-dl      reference-clip downloader
    tools/vid.py     video I/O (PyAV decode/encode, probe, sampling)
    tools/vq.py      measurement: reference-relative signal metrics
    tools/sweep.py   inspection sweep: slit-scans, 4x tiles, per-pitfall checklist
    tools/post.py    algorithmic post: exposure, shake, grain
    tools/gate.py    semantic pre-flight checks on a prompt
    tools/selftest.py  injection tests for the metrics
    docs/pitfalls.md tells ranked for this format
    docs/minesweep.md  how to read the sweep artifacts
    docs/forensics.json  24 forensic tells, 16 remediation techniques

Each piece has one job and no other: `compile.md` writes the spec, `face-gen.md`
builds identity, `gate.py` reads the prompt, `vq.py` measures signal, `sweep.py`
builds what gets looked at, `surgery.md` repairs a span. `judge.md` runs the check
and decides — nothing else decides anything.

### Setup

    uv venv --python 3.13 .venv
    uv pip install --python .venv/bin/python opencv-python-headless scikit-image numpy scipy av pillow

### Loop

    # 1. free checks, before spending credits
    python tools/gate.py targets/X.intent.json targets/X.v<n>.txt

    # 2. generate
    higgsfield generate create <model> --prompt "$(cat targets/X.v<n>.txt)" \
      --image char.png --video ref.mp4 --duration 5 --resolution 720p \
      --aspect_ratio 9:16 --wait

    # 3. measure against the reference
    python tools/vq.py measure ref.mp4 out.mp4
    python tools/vq.py viz motion.png ref.mp4 out.mp4

    # 4. sweep every pitfall, red team in parallel, blind judges, decide
    #    — the whole procedure lives in prompts/judge.md
    python tools/sweep.py plan   out.mp4 ref.mp4
    python tools/sweep.py strips out.mp4 sweep/
    python tools/sweep.py tiles  out.mp4 sweep/

Metrics mean nothing in isolation: pass reference and candidate to one `measure`
run and read the comparison. They measure *distance from this reference*, not
realism in the abstract — measured against a corpus of real phone video, none of
them separates generated output from real footage on its own. See
`docs/pitfalls.md`. Generate ~25% longer than needed and trim the tail,
where degradation concentrates. Inspect suspected defects as tight crops upscaled
4x — a full frame arrives downsampled and invents anatomy and text faults.

### Cost

Generative edit paths have consistently cost more than a full regeneration, and
none is reproducible while no endpoint exposes a seed. Signal-level fixes belong
in `post.py`, which is free; only semantic changes justify a regeneration.

Price before committing to a run rather than working from remembered figures —
models and rates turn over quickly:

    higgsfield model list --video
    higgsfield generate cost <model> --prompt "x" --duration 5 --resolution 720p
