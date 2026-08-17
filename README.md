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
- **Seedance 2.0** for video. `--model NAME` for anything else in `higgsfield model
  list --video`.
- **Every main character is recast** with a generated face, unless you say otherwise.
- **Everything lands in `output/<id>/`.** `targets/` holds the original reference and
  nothing else, so a run can be deleted and repeated without downloading anything again.

The command is not model-invocable: it spends credits, so it only runs when you type it.

## What it does

1. **Compile** the reference into a spec and a prompt — separating what the clip *means*
   from how it happens to look, so the person or the place can change without breaking
   the thing that made it work.
2. **Check the prompt** against the spec before spending anything — free, and it catches
   the mistakes that would otherwise cost a whole generation.
3. **Generate** a take. Every main character gets a generated face image first, because
   identity written as text drifts and comes back better-looking than it should; a prop
   that text keeps getting wrong gets a reference image too, which is far cheaper than
   another video attempt. The original clip can go in as a video reference as well — it
   supplies the camera and the room, and costs you the cast, so it is a trade rather
   than a step.
4. **Judge** the result, meaning first: agents who have not been told what the shot was
   supposed to be watch it blind alongside the original and say what they think it is.
   Only a clip that still means something gets the frame-by-frame sweep, where
   measurements point at where to look and agents inspect every region in parallel. Out
   comes a ship / do-not-ship call with reasons.
5. **Fix** — a signal mismatch is corrected locally for free, a bad span is regenerated
   on its own, and only a broken premise needs starting over.

## What to expect

Generation is a numbers game: the reject ratio on professional work is around 64:1
(`docs/pitfalls.md`), so budget for rejects rather than for one clean run. Clips
degrade toward the end, so it is normal to generate longer than needed and trim.

No measurement here can tell you whether a clip is real or generated — real footage
varies more between cameras and shooting styles than generated footage differs from
real. The measurements say where a result departs from its reference; the judgement
is made by looking. `docs/pitfalls.md` catalogues what tends to go wrong, from a lost
premise down to a garbled logo.

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

## Working on it

`AGENT.md` routes to the procedure for each step and defines the file layout;
`skills/recreate/SKILL.md` is the command that drives them end to end. The tools are in
`tools/`, reachable as `vg vq`, `vg sweep`, `vg gate`, `vg post` and `vg selftest`. From
a checkout, call `bin/vg` or put `bin/` on your `PATH`.

    vg selftest <clip.mp4>     inject known defects, confirm the metrics catch them
