# video-gen

Agent-facing video tooling.

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
