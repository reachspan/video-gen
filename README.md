# video-gen

Agent-facing video tooling: download reference reels, recreate them with AI
generation, and measure how close the result is to camera-captured footage.

## ig-dl

Download Instagram reels, posts and carousels. Single file, stdlib only, no dependencies.

```bash
./ig-dl <url|shortcode>... [-o DIR] [--cookies FILE] [--json]
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

    tools/vid.py     video I/O (PyAV decode/encode, probe, luma)
    tools/vq.py      measurement: 18 metrics + motion rendered as stills
    tools/post.py    algorithmic post: exposure, shake, grain
    tools/gate.py    semantic pre-flight checks on a prompt
    prompts/judge.md blind-judge prompts, run with the original as control
    targets/         per-reel intent spec and prompt
    docs/pitfalls.md tells ranked for this format
    docs/forensics.json  24 forensic tells, 16 remediation techniques

### Setup

    uv venv --python 3.13 .venv
    uv pip install --python .venv/bin/python opencv-python-headless scikit-image numpy scipy av pillow
    export PYTHONPATH=tools

### Loop

    # 1. free checks, before spending credits
    python tools/gate.py targets/X.intent.json targets/X.v3.txt

    # 2. generate
    higgsfield generate create seedance_2_0 --prompt "$(cat targets/X.v3.txt)" \
      --image char.png --video ref.mp4 --duration 5 --resolution 720p \
      --aspect_ratio 9:16 --bitrate_mode high --wait

    # 3. measure against the reference
    python tools/vq.py measure ref.mp4 out.mp4
    python tools/vq.py viz motion.png ref.mp4 out.mp4

    # 4. blind judge, shuffled, original as control (see prompts/judge.md)

Metrics mean nothing in isolation: pass reference and candidate to one `measure`
run and read the comparison. Generate ~25% longer than needed and trim the tail,
where degradation concentrates. Inspect suspected defects as tight crops upscaled
4x — a full frame arrives downsampled and invents anatomy and text faults.

### Cost

Seedance 2.0 720p is 22.5 credits for 5s. Every generative edit path costs more
than a full regeneration (`video_edit` 26.5, `draw_to_video` 26.5, `reframe`
28.5), and none is reproducible, since no Seedance endpoint exposes a seed.
Signal-level fixes belong in `post.py`; only semantic changes justify a regen.
