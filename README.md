# video-gen

Take a short video you like, recreate it with AI generation — with a different person
in it, or a different setting — and check honestly whether the result holds up.

Built for 9:16 phone-shot social video: a few seconds, one speaker, handheld.

## What you get

- **`utils/ig-dl`** — download a reference reel to work from.
- **A written spec of the reference**, separating what the clip *means* from how it
  happens to look, so you can change the person or the place without breaking the
  thing that made it work.
- **An inspection pass** that looks at every frame and every region of the result
  rather than whatever catches the eye, and reports what it could not resolve as well
  as what it found.

An agent drives all of it. `AGENT.md` tells the agent which procedure to follow; you
can just describe what you want.

## Downloading a reference

```bash
utils/ig-dl <url|shortcode>... [-o DIR] [--cookies FILE] [--json]
```

Reels, posts and carousels. Single file, stdlib only, no dependencies. Saved paths go
to stdout as they land; `--json` adds owner, caption, duration and timestamp on
stderr. Use `--cookies` with a Netscape-format file for private or age-gated posts.

Instagram rotates the internal `doc_id` this depends on. When the built-in ones go
stale the tool says so; pull a fresh one from a browser DevTools capture of a reel
page load and prepend it to `DOC_IDS`.

## The loop

1. **Compile** the reference into a spec and a prompt.
2. **Check the prompt** against the spec before spending anything — free, and it
   catches the mistakes that would otherwise cost a whole generation.
3. **Generate.**
4. **Sweep and judge** the result: measurements point at where to look, then agents
   inspect the clip in parallel and return a ship / do-not-ship call with reasons.
5. **Fix** — a signal mismatch is corrected locally for free, a bad span is
   regenerated on its own, and only a broken premise needs starting over.

Ask for any step by name, or for the whole thing.

## What to expect

Generation is a numbers game: professional work discards on the order of sixty
attempts per keeper, so budget for rejects rather than for one clean run. Clips
degrade toward the end, so it is normal to generate longer than needed and trim.

No measurement here can tell you whether a clip is real or generated — real footage
varies more between cameras and shooting styles than generated footage differs from
real. The measurements say where a result departs from its reference; the judgement
is made by looking. `docs/pitfalls.md` lists what tends to go wrong and how each gets
checked.

## Setup

    uv venv --python 3.13 .venv
    uv pip install --python .venv/bin/python opencv-python-headless scikit-image numpy scipy av pillow

Generation runs through the [Higgsfield](https://higgsfield.ai) CLI, which needs its
own account and credits. `ffmpeg` must be on the path.
