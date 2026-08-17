#!/usr/bin/env python3
"""Systematic inspection sweep.

  sweep.py strips CLIP OUTDIR      slit-scans: the whole duration in one image each
  sweep.py tiles CLIP OUTDIR       4x crops tiling the frame, at sampled frames
  sweep.py plan CLIP [REF]         per-pitfall checklist, as markdown

An inspection that jumps to whatever looks suspicious will keep missing the same
things. These commands turn a clip into a bounded set of views that between them
cover every frame and every region, so a red-team pass can be exhaustive and can
say what it has actually looked at.

Two coverage axes, handled differently:

TIME. A slit-scan takes one row or column of pixels from every frame and stacks
them side by side, so a whole clip becomes a single image. Nothing is sampled
away: every frame contributes. Motion becomes shape - a subject that breathes
gives a wavering edge, one that freezes gives a dead straight line, and a jump cut
gives a vertical discontinuity.

SPACE. Small defects - text, logos, fingers, contact shadows - are invisible in a
downscaled full frame, so the frame is cut into tiles and each is written at 4x.
Every pixel lands in exactly one tile, and the tile grid matches the one vq.py
scores, so a permanence hotspot names the tile to open.

Tiles are written for a few frames spread across the clip AND for each tile's own
worst moment, found by scanning every frame. A brief defect between the sampled
frames would otherwise be missed entirely; this keeps the number of images fixed
while the search behind them covers the whole clip.

What can still slip through: a defect that is small, brief, and not the most
anomalous moment in its own tile. Nothing here makes the sweep infallible - it
makes it bounded, repeatable, and honest about where it looked.
"""
import json, os, sys
import cv2
import numpy as np
from vid import read, count, spread, blocks, read_at, probe

ROWS, COLS = 6, 4          # matches the vq.py permanence grid
ZOOM = 4
NSTRIP = 5                 # slit positions per axis


def strips(path, outdir):
    """Slit-scans across the full duration, at several positions on each axis."""
    os.makedirs(outdir, exist_ok=True)
    F = read(path)
    n, h, w = F.shape[:3]
    made = []
    for k in range(1, NSTRIP + 1):
        y = h * k // (NSTRIP + 1)
        img = F[:, y, :, :]                                  # (n, w, 3)
        img = cv2.resize(np.transpose(img, (1, 0, 2)), (max(n * 3, 480), w),
                         interpolation=cv2.INTER_NEAREST)
        p = os.path.join(outdir, f"strip_row_{y:04d}.jpg")
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        made.append(p)
    for k in range(1, NSTRIP + 1):
        x = w * k // (NSTRIP + 1)
        img = F[:, :, x, :]                                  # (n, h, 3)
        img = cv2.resize(np.transpose(img, (1, 0, 2)), (max(n * 3, 480), h),
                         interpolation=cv2.INTER_NEAREST)
        p = os.path.join(outdir, f"strip_col_{x:04d}.jpg")
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        made.append(p)
    return made


def _crop(im, i, j, out):
    h, w = im.shape[:2]
    th, tw = h // ROWS, w // COLS
    c = im[i * th:(i + 1) * th, j * tw:(j + 1) * tw]
    c = cv2.resize(c, (tw * ZOOM, th * ZOOM), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(out, cv2.cvtColor(c, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 95])
    return out


def odd_frames(path, k=3):
    """For each tile, the frame where it departs most from its own neighbours.

    Sampling a few frames leaves a defect that appears briefly - a wordmark that
    garbles for half a second, a grip that breaks and recovers - free to fall
    between them. Every frame is scanned here, cheaply and at reduced scale, and
    each tile reports its own worst moment, so the number of images to look at
    stays fixed while the search covers the whole clip.

    The score is a second difference in time, |2*f(t) - f(t-k) - f(t+k)|. Steady
    drift and steady motion cancel; what survives is the moment a region stops
    behaving like itself, which is the shape a transient defect has. Comparing
    each frame against a whole-clip average instead just rediscovers the ends of
    the clip on anything that drifts.
    """
    F = read(path)
    small = np.stack([cv2.cvtColor(cv2.resize(f, (F.shape[2] // 4, F.shape[1] // 4)),
                                   cv2.COLOR_RGB2GRAY) for f in F]).astype(np.float32)
    n, h, w = small.shape
    th, tw = h // ROWS, w // COLS
    out = {}
    if n < 2 * k + 1:
        return out
    for i in range(ROWS):
        for j in range(COLS):
            t = small[:, i * th:(i + 1) * th, j * tw:(j + 1) * tw]
            dev = np.abs(2 * t[k:n - k] - t[:n - 2 * k] - t[2 * k:]).mean((1, 2))
            out[(i, j)] = int(np.argmax(dev)) + k
    return out


def tiles(path, outdir, nframes=3):
    """Every region of the frame at 4x: on frames spread across the clip, plus
    each tile at its own most anomalous frame."""
    os.makedirs(outdir, exist_ok=True)
    n = count(path)
    idx = spread(n, nframes)
    odd = odd_frames(path)
    got = read_at(path, sorted(set(idx) | set(odd.values())))
    made = []
    for f in idx:
        for i in range(ROWS):
            for j in range(COLS):
                made.append(_crop(got[f], i, j,
                                  os.path.join(outdir, f"f{f:04d}_t{i}{j}.jpg")))
    for (i, j), f in sorted(odd.items()):
        if f not in idx:
            made.append(_crop(got[f], i, j,
                              os.path.join(outdir, f"odd_t{i}{j}_f{f:04d}.jpg")))
    return made


# Pitfalls bundled into work packages, one package per subagent. Packages are cut
# by EVIDENCE, not by theme: every tile is read by exactly one agent, which answers
# every question that applies to it. A theme-shaped package that needs every tile
# would duplicate the others and set the pace for the whole run.
PACKAGES = [
    ("motion-and-life", ["T1", "T2", "T3", "T8", "T11", "T13"],
     "strip_* — all of them, candidate and reference — plus motion_by_block. No "
     "tiles. You are judging whether every body in frame is alive, whether a hand "
     "held the camera, and whether the tail degrades. The edge columns carry the "
     "secondary figures and count the same as the centre ones."),
    ("face-and-gaze", ["T4", "T5", "T9"],
     "tiles covering every head in frame, sampled and odd_* alike."),
    ("hands-and-props", ["T6", "T7", "T15", "T16", "T9"],
     "tiles covering the hands and anything held, by any person in frame, sampled "
     "and odd_* alike, plus the permanence_hotspots boxes."),
    ("scene-and-optics", ["T10", "T12", "T9"],
     "tiles outside the subject box, sampled and odd_* alike. If subject_box "
     "covers most of the frame there may be very few; say how many you had, and "
     "judge those."),
    ("remaining-tiles", ["T9"],
     "every tile no other package claimed. This is the coverage backstop — a "
     "wordmark can sit in any corner of the frame."),
]

PLAN = [
    ("T1", "Statue torso", "subject_stillness",
     "strip_col_* through every torso in frame. A living body wavers; a frozen one "
     "draws straight horizontal lines. Check every column strip, not just the "
     "centre: the edge columns cross the secondary figures, and one of those "
     "holding still is the same defect as the speaker holding still."),
    ("T2", "No breathing", "-",
     "strip_col_* crossing the shoulder or collar line of anyone whose chest is in "
     "frame. Judge the SIGNATURE, not "
     "a rate: a real chest edge rises and falls continuously, a generated one "
     "holds a dead flat line. At 12-20 breaths a minute a short clip contains "
     "well under two full cycles, so on anything that brief a rate is not "
     "recoverable and must not be "
     "reported as one; a sustained flat edge is still a defect, and a wavering "
     "one still clears."),
    ("T3", "No physiological jitter", "subject_stillness",
     "strip_col_* through every head in frame during a pause in the action. Real "
     "heads never hold a line even when 'still'."),
    ("T4", "Mask face", "-",
     "tiles on the face, sampled and odd_* alike: does anything above the eyes "
     "move? Watch muted and try to name the stressed word."),
    ("T5", "Mannequin gaze", "-",
     "tiles on the eye region, sampled and odd_* alike. Look for saccades, for "
     "blinks, and for the eyes repositioning independently of the skull. Counter-"
     "rotation only applies if the head actually turns: if it never yaws, record "
     "that sub-test as not applicable and judge on the rest rather than calling "
     "the whole pitfall cannot_tell."),
    ("T6", "Thin-prop topology", "permanence_hotspots",
     "tiles covering the prop, sampled and odd_* alike; trace it end to end in "
     "each and confirm the strand count and the route between hands hold. odd_* "
     "is where a brief re-route shows."),
    ("T7", "Contactless hold", "-",
     "tiles on every grip in frame, sampled and odd_* alike, including the ones "
     "held by a hand entering at an edge. Look for fingertip flattening, skin "
     "blanching and a dark contact line. Absence of all three is the tell."),
    ("T8", "End-loaded collapse", "motion_by_block",
     "the right-hand end of every strip, and the last motion_by_block entry "
     "against the first. Every package also starts at the final sampled frame of "
     "its own region, since degradation is end-loaded."),
    ("T9", "Garbled text", "-",
     "EVERY tile, sampled and odd_* alike. Read every string aloud; a logo "
     "legible in one frame and mush in the next is the failure, so compare a "
     "tile against its own odd_* frame."),
    ("T10", "Art-directed background", "-",
     "tiles outside the subject box. List what is there and ask whether a set "
     "dresser chose it. Real rooms contain irrelevant ugly objects."),
    ("T11", "Framing too perfect", "displacement_px",
     "strip_row_* near the head. Operator drift shows as slow wander with "
     "occasional corrections; a straight line means the camera was never held."),
    ("T12", "Cinema bokeh", "-",
     "tiles on a background point highlight. A blur disc wider than ~1.5% of "
     "frame height is not a phone lens."),
    ("T13", "AE/WB never move", "-",
     "strips carry exposure as brightness along the time axis. A real clip drifts "
     "and steps; a perfectly even strip means auto-exposure never ran."),
    ("T14", "Beauty bias", "-",
     "cross-clip, not in-clip: put several generations side by side and ask "
     "whether they look more alike than several real people would."),
    ("T15", "Object scale and placement", "-",
     "tiles on every held or intruding object. TWO measurements, both stated as "
     "ratios rather than impressions. (1) Size, against a body landmark the "
     "viewer already knows: head height, or hand breadth at ~1 head wide. Look up "
     "the object's real dimension and compare. Wrong in either direction counts — "
     "a foreshortened object is as wrong as an oversized one, and often it is one "
     "part that is wrong while the rest is right. (2) Intrusion depth, for "
     "anything entering from a frame edge: measure to the DEEPEST point of the "
     "whole assembly, including any protruding part, not the body's bounding box. "
     "A body that sits at the edge does not make an edge intrusion if its tip "
     "reaches the middle of the frame."),
    ("T16", "Incomplete assembly", "-",
     "tiles covering every person and every held object, sampled and odd_* alike. "
     "Take each one as a whole thing and try to complete it: trace every hand back "
     "along a forearm to a shoulder or to the edge it enters from; name the parts a "
     "tool would need in order to work and say which are present; ask what holds "
     "each fitting up. Count whatever should be countable — limbs, strands, "
     "conductors, fasteners — and say whether the totals can belong to one object. "
     "Judge each tile ON ITS OWN before comparing it with any other: this fault is "
     "the same in every frame, so it passes a cross-frame check untouched, and "
     "T6 will not catch it."),
]


def plan(path, ref=None):
    n = count(path)
    p = probe(path)
    idx = spread(n, 3)
    out = [f"# Sweep plan — {os.path.basename(path)}",
           "",
           f"{n} frames at {p['fps']:.2f} fps ({n / p['fps']:.1f}s). "
           f"Tile grid {ROWS}x{COLS} at {ZOOM}x. Sampled frames: {idx}.",
           "",
           "    python tools/sweep.py strips %s sweep/" % path,
           "    python tools/sweep.py tiles  %s sweep/" % path,
           f"    python tools/vq.py measure {ref or 'REF'} {path}",
           "",
           "Coverage: the strips include every frame; the tiles include every "
           "pixel of each sampled frame, plus each tile at its own worst moment, "
           "found by scanning all frames (`odd_*`).",
           "",
           "| id | pitfall | signal | how to sweep it |",
           "|---|---|---|---|"]
    for pid, name, sig, how in PLAN:
        out.append(f"| `{pid}` | {name} | {sig} | {how} |")
    out += ["",
            "## Rules for every package",
            "",
            "1. Work your list in order and record a verdict for EVERY id in it, "
            "including the ones you cleared. An id with no verdict has not been "
            "swept, and that is the difference between an exhaustive pass and an "
            "opportunistic one.",
            "2. Three outcomes only - `defect`, `clear`, `cannot_tell`. The third "
            "is a real answer and it is expected; reporting it is what keeps "
            "`clear` honest. Anything you cannot resolve at 4x is `cannot_tell`, "
            "never `clear`.",
            "3. Open the tiles as written. They are already at 4x; re-cropping "
            "the full frame reintroduces the downscaling this sweep exists to "
            "avoid, and a whole-frame view invents defects as readily as it "
            "hides them. For anything smaller than a hand, confirm it in the "
            "tile before reporting it.",
            "4. Start at the final sampled frame of your region and work "
            "backwards. Degradation is end-loaded, so the tail is where a defect "
            "is most likely to be waiting.",
            "5. Read the strips before the tiles, and read both against the "
            "reference's. They are cheap and cover the whole duration, so they "
            "say where in time to spend the expensive attention - and a static "
            "background draws straight lines legitimately, so 'straight' means "
            "something only next to a clip where it wavers.",
            "6. Metrics only point. Every verdict is made by looking; a metric "
            "that fires is a place to look, and a metric that stays quiet is not "
            "a pass.",
            "7. If a sub-test inside a pitfall has nothing to bite on - "
            "counter-rotation when the head never turns, a breathing rate on a "
            "clip too short to hold two cycles - record that sub-test as not "
            "applicable and judge on the rest. Do not return `cannot_tell` for a "
            "whole pitfall because one of its checks was inapplicable.",
            "",
            "Return JSON: {package, findings: [{pitfall, verdict: "
            "defect|clear|cannot_tell, where: [{frame, tile_or_box}], evidence, "
            "severity_1_5}]}. `where` is a list, so a pitfall recurring across "
            "tiles or frames records each occurrence; every entry carries a "
            "frame number and a tile or pixel box, so a finding can be re-opened "
            "by someone who did not make it.",
            "",
            "## Work packages",
            "",
            "Run these in parallel, one fresh agent each. `T14` is deliberately "
            "absent: it compares several generations and cannot be judged from "
            "one clip.",
            "",
            "| package | pitfalls | evidence to open |",
            "|---|---|---|"]
    for name, ids, ev in PACKAGES:
        out.append(f"| `{name}` | {' '.join(ids)} | {ev} |")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "strips":
        print("\n".join(strips(sys.argv[2], sys.argv[3])))
    elif cmd == "tiles":
        print("\n".join(tiles(sys.argv[2], sys.argv[3])))
    elif cmd == "plan":
        print(plan(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
    else:
        sys.exit(__doc__)
