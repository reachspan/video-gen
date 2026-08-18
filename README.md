# video-gen

Take a short video you like, recreate it with AI generation — with a different person
in it, or a different setting — and check honestly whether the result holds up.

Built for 9:16 phone-shot social video: short-form, one speaker, handheld.

Ships as a Claude Code plugin with one command. Give it a link, and it compiles the
reference into a spec, casts it, generates, judges the result blind, and either ships a
take or tells you why it could not.

## Install

```bash
claude plugin marketplace add reachspan/video-gen
claude plugin install video-gen@reachspan
```

Or point Claude Code at a checkout, which is also how you develop it:

```bash
claude --plugin-dir /path/to/video-gen
```

Then, once per machine:

    vg setup      builds the Python environment
    vg doctor     checks every dependency and says what is missing

### Requirements

`vg setup` handles the Python side. The rest are system dependencies a plugin cannot
install for you, and `vg doctor` reports each one:

| what | why | how |
|---|---|---|
| Python 3.13 | the measurement tools | preinstalled on most systems; `uv` is used if present |
| `opencv-python-headless scikit-image numpy scipy av` | the measurement tools | `vg setup` |
| `ffmpeg` and `ffprobe` | every crop, contact sheet and re-encode | your package manager |
| `higgsfield` CLI | all generation goes through it | `curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh \| sh`, or `brew install higgsfield-ai/tap/higgsfield`, or `npm i -g @higgsfield/cli` |
| a Higgsfield account with credits | generation is paid, per take | `higgsfield auth login` |

**The login is interactive and browser-based** — there is no API-key or environment
variable mode, so an agent cannot complete it for you. Do it once before the first run;
`vg doctor` tells you if the session has expired.

## Use

    /video-gen:recreate <url-or-path> [instructions] [--max-credits N] [--model NAME]

```
/video-gen:recreate https://www.instagram.com/reel/ABC123/
/video-gen:recreate ./clip.mp4 keep the original cast, move it to a garage
/video-gen:recreate ABC123 --max-credits 400 --model veo3_1
```

It takes an Instagram reel, another video URL, or a local file. **It runs end to end
without stopping to ask** — interrupt it if you want it steered. Defaults:

- **150 Higgsfield credits**, then it stops and reports. Everything billed counts —
  takes, patches and casting stills alike. `--max-credits N` to change it.
- **Seedance 2.5 at 480p, 9:16** for video — 480p is where the budget is set, not a
  ceiling. `--model NAME` for anything else in `higgsfield model list --video`, and ask
  for a resolution in the instruction ("do it at 720p") to override that; whatever the
  model offers is available, and a resolution you name is taken as given.
- **Every main character is recast** with a generated face, unless you say otherwise.
- **Everything lands in `output/<id>/`.** The delivered take is
  `take.v<n>.t<k>.selected.mp4`. `targets/` holds the original reference and
  nothing else, so a run can be deleted and repeated without downloading anything again.

The command is not model-invocable: it spends credits, so it only runs when you type it.

## What it does

1. Compiles the reference into a spec and a prompt.
2. Checks the prompt against the spec. Free.
3. Casts, then generates a take.
4. Judges it blind, then frame by frame. Ships or says why not.
5. Fixes what it can — a signal mismatch locally, a bad span on its own — or starts over if the premise is broken.

## What to expect

Budget for rejects; several takes is normal. Quality falls off at the tail, so the run
generates longer than the finished cut. Measurements compare a take to the reference;
they do not say whether a clip is real.

## Downloading a reference on its own

```bash
vg ig-dl <url|shortcode>... [-o DIR] [--cookies FILE] [--json]
```

Reels, posts and carousels. Stdlib only, no dependencies. Saved paths go to stdout as
they land; `--json` adds owner, caption, duration and timestamp on stderr. Use
`--cookies` with a Netscape-format file for private or age-gated posts.

Instagram rotates the internal `doc_id` this depends on. When the built-in ones go
stale the tool says so; pull a fresh one from a browser DevTools capture of a reel
page load and prepend it to `DOC_IDS`.

