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
        p = os.path.join(outdir, f"strip_row_{y:04d}.png")
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        made.append(p)
    for k in range(1, NSTRIP + 1):
        x = w * k // (NSTRIP + 1)
        img = F[:, :, x, :]                                  # (n, h, 3)
        img = cv2.resize(np.transpose(img, (1, 0, 2)), (max(n * 3, 480), h),
                         interpolation=cv2.INTER_NEAREST)
        p = os.path.join(outdir, f"strip_col_{x:04d}.png")
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        made.append(p)
    return made


def tiles(path, outdir, nframes=3):
    """Every region of the frame at 4x, on frames spread across the clip."""
    os.makedirs(outdir, exist_ok=True)
    n = count(path)
    idx = spread(n, nframes)
    got = read_at(path, idx)
    made = []
    for f in idx:
        im = got[f]
        h, w = im.shape[:2]
        th, tw = h // ROWS, w // COLS
        for i in range(ROWS):
            for j in range(COLS):
                c = im[i * th:(i + 1) * th, j * tw:(j + 1) * tw]
                c = cv2.resize(c, (tw * ZOOM, th * ZOOM),
                               interpolation=cv2.INTER_LANCZOS4)
                p = os.path.join(outdir, f"f{f:04d}_t{i}{j}.png")
                cv2.imwrite(p, cv2.cvtColor(c, cv2.COLOR_RGB2BGR))
                made.append(p)
    return made


# Pitfalls bundled into work packages. One package is one subagent: the grouping
# follows the artifact each needs, so a package is a coherent job and no two
# packages fight over the same evidence.
PACKAGES = [
    ("motion-and-life", ["T1", "T2", "T3", "T11", "T13"],
     "strip_* (all of them). You are judging whether the body is alive and "
     "whether a hand held the camera."),
    ("face-and-gaze", ["T4", "T5"],
     "tiles covering the head, every sampled frame."),
    ("hands-and-props", ["T6", "T7"],
     "tiles covering the hands and anything held, every sampled frame, plus the "
     "permanence_hotspots boxes."),
    ("text-and-branding", ["T9"],
     "EVERY tile, every sampled frame. Nothing is exempt: a wordmark can sit in "
     "any corner of the frame."),
    ("scene-and-optics", ["T10", "T12"],
     "tiles outside the subject box, every sampled frame."),
    ("tail", ["T8"],
     "tiles at the LAST sampled frame and the right-hand end of every strip, "
     "plus motion_by_block."),
]

PLAN = [
    ("T1", "Statue torso", "subject_stillness",
     "strip_col_* through the torso. A living body wavers; a frozen one draws "
     "straight horizontal lines. Check every column strip, not just the centre."),
    ("T2", "No breathing", "-",
     "strip_col_* crossing the shoulder line. Count the slow oscillations over "
     "the clip and divide by its duration: expect 12-20 per minute. A flat edge "
     "is a held breath, which nobody does for a whole take."),
    ("T3", "No physiological jitter", "subject_stillness",
     "strip_col_* through the head during a pause in the action. Real heads never "
     "hold a line even when 'still'."),
    ("T4", "Mask face", "-",
     "tiles on the face across the clip: does anything above the eyes move? Watch "
     "muted and try to name the stressed word."),
    ("T5", "Mannequin gaze", "-",
     "tiles on the eye region at each sampled frame. Look for saccades and for "
     "counter-rotation when the head turns."),
    ("T6", "Thin-prop topology", "permanence_hotspots",
     "tiles covering the prop at every sampled frame; trace it end to end in each "
     "and confirm the count of strands and the route between hands is the same."),
    ("T7", "Contactless hold", "-",
     "tiles on the grip. Look for fingertip flattening, skin blanching and a dark "
     "contact line. Absence of all three is the tell."),
    ("T8", "End-loaded collapse", "motion_by_block",
     "the LAST block first: tiles at the final sampled frame, and the right-hand "
     "end of every strip. Compare the last motion_by_block entry with the first."),
    ("T9", "Garbled text", "-",
     "every tile of the tiles sweep, at each sampled frame. Read every string "
     "aloud; a logo that is legible in one frame and mush in the next is the "
     "failure, so compare the same tile across frames."),
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
]


def plan(path, ref=None):
    n = count(path)
    p = probe(path)
    idx = spread(n, 3)
    out = [f"# Minesweep — {os.path.basename(path)}",
           "",
           f"{n} frames at {p['fps']:.2f} fps ({n / p['fps']:.1f}s). "
           f"Tile grid {ROWS}x{COLS} at {ZOOM}x. Sampled frames: {idx}.",
           "",
           "    python tools/sweep.py strips %s sweep/" % path,
           "    python tools/sweep.py tiles  %s sweep/" % path,
           f"    python tools/vq.py measure {ref or 'REF'} {path}",
           "",
           "Coverage: the strips include every frame; the tiles include every "
           "pixel of each sampled frame. Work the list in order and record a "
           "verdict for each, including the ones you cleared - an item with no "
           "verdict has not been swept.",
           "",
           "| id | pitfall | signal | how to sweep it |",
           "|---|---|---|---|"]
    for pid, name, sig, how in PLAN:
        out.append(f"| `{pid}` | {name} | {sig} | {how} |")
    out += ["",
            "Metrics only point. Every verdict here is made by looking; a metric "
            "that fires is a place to look, and a metric that stays quiet is not "
            "a pass. Anything you cannot resolve at 4x is 'cannot tell', never "
            "'fine'.",
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
    out += ["",
            "Each returns JSON: {package, findings: [{pitfall, verdict: "
            "defect|clear|cannot_tell, where, evidence, severity_1_5}]}, with an "
            "entry for EVERY pitfall in the package."]
    return "\n".join(out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "strips":
        print("\n".join(strips(sys.argv[2], sys.argv[3])))
    elif cmd == "tiles":
        print("\n".join(tiles(sys.argv[2], sys.argv[3])))
    elif cmd == "plan":
        print(plan(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
    else:
        sys.exit(__doc__)
