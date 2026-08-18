#!/usr/bin/env python3
"""Signal measurement against a reference clip.

  vq.py measure REF CAND...   metrics; first file is the reference

JSON on stdout, comparison table on stderr.

These measure DISTANCE FROM A REFERENCE, not realism. Read a value only against a
reference measured in the same run. `docs/evidence.md` says what each number
means, which ones survive which conditions, and why a quiet metric is not a pass.

Removed after measurement, do not re-add: lateral chromatic aberration, grain
advection, raw temporal residual correlation and vignetting, none of which
survive platform bitrates; sharpness radial falloff, centre/corner ratio, shake
spectral slope and peakiness, radial FFT slope and noise band max/min ratio, on
all of which real footage disagrees with itself as much as with generated output.
"""
import json, sys
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from vid import (probe, luma, luma_profile, count, spread, blocks, read_at,
                 pairs, to_gray, pmap, CENTRES, BLOCKLEN)

# Photometric stats and the subject mask share NSAMPLE frames spread across the
# whole clip. Adjacent-frame metrics cannot use a spread, so they read the
# contiguous blocks vid.blocks() lays out.
NSAMPLE = 24
# Permanence needs a bounded horizon. Compared against the first frame of a whole
# 4s clip the worst tile saturates on real footage, because over four seconds
# something always moves; ~0.8s is long enough for drift to show and short enough
# that ordinary motion does not swamp it.
PBLOCK, PBLOCKLEN = 3, 24


def subject_box(A, guard=0.60):
    """Bounding box of the dominant moving mass in a motion-compensated stack.

    Only the LARGEST connected component is taken. Masking every high-variance
    pixel would be self-defeating, since a background object that morphs is both
    what we want to catch and high-variance; taking one contiguous component
    removes the subject while leaving isolated background defects in play.
    """
    h, w = A.shape[1:3]
    var = A.std(0)
    if var.max() < 1e-6:
        return None
    b = (var > np.percentile(var, 75)).astype(np.uint8)
    k = np.ones((9, 9), np.uint8)
    b = cv2.morphologyEx(cv2.morphologyEx(b, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
    nlab, _, stats, _ = cv2.connectedComponentsWithStats(b, 8)
    if nlab < 2:
        return None
    x, y, bw, bh, _ = stats[1:][np.argmax(stats[1:, cv2.CC_STAT_AREA])]
    px, py = int(bw * .08), int(bh * .08)          # a little margin for spill
    x, y = max(0, x - px), max(0, y - py)
    bw, bh = min(w - x, bw + 2 * px), min(h - y, bh + 2 * py)
    if bw * bh > guard * h * w:                    # swallowed the frame; useless
        return None
    return x, y, bw, bh


def measure(path):
    m = {"file": path.split("/")[-1]}
    p = probe(path)
    m |= {"fps": round(p["fps"], 2), "kbps": p["kbps"],
          "width": p["width"], "height": p["height"]}

    n = count(path)
    sidx = spread(n, NSAMPLE)
    bidx = blocks(n)
    pidx = blocks(n, PBLOCK, PBLOCKLEN)
    frames = read_at(path, sidx + [i for b in bidx + pidx for i in b])
    m["sampled"] = {"frames": n, "spread": [sidx[0], sidx[-1]],
                    "blocks": [[b[0], b[-1]] for b in bidx],
                    "perm_blocks": [[b[0], b[-1]] for b in pidx]}

    F = np.stack([frames[i] for i in sidx])
    Y = luma(F)

    prof = luma_profile(F)
    m["noise_by_luma"] = [x if x is None else round(x, 3) for x in prof]
    # Signed trend of noise across the luma range, per 100 levels, normalised by
    # mean noise so it does not move with overall grain magnitude. Unlike the
    # max/min ratio this keeps the ORDER of the bands, which is the part that
    # differs between cameras.
    ok = np.array([x is not None and x > 0 for x in prof])
    if ok.sum() > 1:
        pv = np.array([x for x, k in zip(prof, ok) if k], float)
        s = float(np.polyfit(CENTRES[ok], pv, 1)[0]) * 100 / (pv.mean() + 1e-9)
        m["noise_luma_slope"] = round(s, 3)
    else:
        m["noise_luma_slope"] = None

    # exposure: sensors rail, renderers roll off
    h = np.bincount(Y.astype(np.uint8).ravel(), minlength=256).astype(float)
    t = h.sum()
    m["clip_high_pct"] = round(float(h[254:].sum() / t * 100), 3)
    m["clip_low_pct"] = round(float(h[:2].sum() / t * 100), 3)

    G = {i: to_gray(f) for i, f in frames.items()}
    # Colour is only needed for the photometric sample and for permanence chroma;
    # the motion blocks work on gray alone. Holding every decoded frame in colour
    # costs hundreds of MB per clip, which matters once clips run in parallel.
    keep = set(sidx) | {i for b in pidx for i in b}
    frames = {i: f for i, f in frames.items() if i in keep}

    # Subject region: the dominant moving mass, unioned with a centre box and
    # extended to the bottom edge. A seated talking-head is a contiguous column
    # reaching the frame bottom, and a variance blob finds the head and torso
    # while missing the lap and hands.
    h_, w_ = F.shape[1:3]
    subj = np.zeros((h_, w_), bool)
    subj[int(h_ * .15):int(h_ * .95), int(w_ * .20):int(w_ * .80)] = True
    box = subject_box(np.stack([G[i] for i in sidx]))
    if box:
        x, y, bw, _ = box
        subj[y:, x:x + bw] = True
        m["subject_box"] = [int(x), int(y), int(bw), int(h_ - y)]
    else:
        m["subject_box"] = None

    # camera motion and temporal stability, measured only between genuinely
    # adjacent frames and pooled across blocks that span the clip.
    disp, energy, ssims, live, ratio = [], [], [], [], []
    bgr_n = int((~subj).sum())
    for u, v in pairs(bidx):
        A, B = G[u], G[v]
        (dx, dy), _ = cv2.phaseCorrelate(A, B)
        disp.append(float(np.hypot(dx, dy)))
        energy.append(float(np.abs(B - A).mean()))
        ssims.append(float(ssim(A, B, data_range=255)))
        # Liveliness: motion left INSIDE the subject after the camera's own
        # movement is cancelled. Normalised by the subject's contrast so it
        # does not track exposure or scene brightness.
        Bc = cv2.warpAffine(B, np.float32([[1, 0, -dx], [0, 1, -dy]]),
                            (w_, h_), borderMode=cv2.BORDER_REPLICATE)
        d = np.abs(Bc - A)
        live.append(float(d[subj].mean() / (A[subj].std() + 1e-6)))
        # Global compensation never removes all camera movement - parallax and
        # rolling shutter leak through, and they leak into background and
        # subject alike. Their RATIO cancels that, leaving how much more the
        # subject moves than its own backdrop, which is what a still body
        # loses. Skipped when there is no background left to compare against.
        if bgr_n:
            ratio.append(float(d[subj].mean() / (d[~subj].mean() + 1e-6)))
    m["displacement_px"] = round(float(np.median(disp)), 3)
    e = np.array(energy)
    m["motion_mean"] = round(float(e.mean()), 3)
    m["ssim_min"] = round(float(np.min(ssims)), 4)
    m["motion_by_block"] = [
        round(float(np.mean(energy[k * (BLOCKLEN - 1):(k + 1) * (BLOCKLEN - 1)])), 3)
        for k in range(len(bidx))]

    # A real subject is never perfectly still: breathing and micro-corrections
    # keep residual motion off the floor even between deliberate actions. The
    # ratio of the quietest frames to the typical ones is scale-free, so it does
    # not depend on how animated the performance is - only on whether the subject
    # ever goes dead. A generated subject tends to freeze between scripted beats.
    lv = np.array(live)
    m["subject_stillness"] = round(float(np.percentile(lv, 10)
                                         / (np.median(lv) + 1e-9)), 3)
    m["subject_vs_background"] = (round(float(np.median(ratio)), 3)
                                  if ratio else None)

    # Object permanence over background tiles, kept per (frame, tile) so a
    # failure has a location and not just a score.
    bg = ~subj
    tiles = [(i, j) for i in range(6) for j in range(4)
             if bg[i * h_ // 6:(i + 1) * h_ // 6, j * w_ // 4:(j + 1) * w_ // 4].any()]
    m["bg_tiles"] = len(tiles)

    # Each permanence block is compared against its OWN first frame, aligned by
    # accumulating consecutive shifts rather than correlating across the whole
    # block: short steps stay reliable where a long baseline does not, and a
    # 24-frame block bounds the drift they accumulate.
    # Phase correlation can return a grossly wrong shift on repetitive content, so
    # implausible steps are dropped. The threshold comes from THIS clip's own
    # motion - 8x its median step, plus 2px of slack for near-static clips -
    # because a fixed pixel count would reject real motion on a clip that pans.
    steps = {}
    for blk in pidx:
        prev, acc = G[blk[0]], []
        for t_ in blk[1:]:
            acc.append(cv2.phaseCorrelate(prev, G[t_])[0])
            prev = G[t_]
        steps[blk[0]] = acc
    allmag = [float(np.hypot(*s)) for a in steps.values() for s in a]
    maxstep = 8.0 * float(np.median(allmag)) + 2.0
    m["align_maxstep_px"] = round(maxstep, 2)

    ref_std = float(np.mean([G[b[0]].std() for b in pidx]))
    cells, clamped = [], 0
    for blk in pidx:
        g0, c0 = G[blk[0]], frames[blk[0]]
        LAB0 = cv2.cvtColor(c0, cv2.COLOR_RGB2LAB).astype(np.float32)
        dx = dy = 0.0
        for t_, (sx, sy) in zip(blk[1:], steps[blk[0]]):
            if np.hypot(sx, sy) > maxstep:
                sx = sy = 0.0
                clamped += 1
            dx, dy = dx + sx, dy + sy
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            al = cv2.warpAffine(G[t_], M, (w_, h_),
                                borderMode=cv2.BORDER_REPLICATE)
            lab = cv2.cvtColor(
                cv2.warpAffine(frames[t_], M, (w_, h_),
                               borderMode=cv2.BORDER_REPLICATE),
                cv2.COLOR_RGB2LAB).astype(np.float32)
            for i, j in tiles:
                ys = slice(i * h_ // 6, (i + 1) * h_ // 6)
                xs = slice(j * w_ // 4, (j + 1) * w_ // 4)
                a, b = g0[ys, xs], al[ys, xs]
                # Both thresholds are relative to the clip's own contrast, not to
                # absolute grey levels, which would change meaning on darker or
                # flatter footage.
                if a.std() < 0.10 * ref_std:
                    continue                  # no detail to begin with
                # A tile that loses most of its contrast has lost its content
                # entirely, which is the floor of the scale - ordinary
                # anti-correlated texture must not outrank it.
                ncc = (float(np.corrcoef(a.ravel(), b.ravel())[0, 1])
                       if b.std() > 0.20 * a.std() else -1.0)
                # Lab chroma drift: a patch can stay correlated while changing
                # colour. Euclidean in (a*, b*) stays defined on grey tiles,
                # where a hue angle would be numerical noise.
                d0, d1 = LAB0[ys, xs, 1:], lab[ys, xs, 1:]
                chroma = float(np.hypot(*(d1.mean((0, 1)) - d0.mean((0, 1)))))
                # area drift: fraction of the tile above its own frame-0 median
                thr = float(np.median(a))
                area = abs(float((b > thr).mean()) - float((a > thr).mean()))
                # t_ is already absolute, so the hotspot box can be cropped as-is
                cells.append((ncc, chroma, area, t_, i, j))

    m["align_clamped"] = clamped
    if cells:
        m["permanence_mean_ncc"] = round(float(np.mean([c[0] for c in cells])), 4)
        m["permanence_worst_ncc"] = round(float(np.min([c[0] for c in cells])), 4)
        m["permanence_chroma_worst"] = round(float(np.max([c[1] for c in cells])), 2)
        # Worst offenders as (frame, tile) with a pixel box, so a suspect region
        # can be cropped and looked at. Area drift rides along as context.
        th, tw = h_ // 6, w_ // 4
        m["permanence_hotspots"] = [
            {"frame": c[3], "tile": [c[4], c[5]],
             "box": [c[5] * tw, c[4] * th, tw, th],
             "ncc": round(c[0], 4), "chroma": round(c[1], 2),
             "area": round(c[2], 4)}
            for c in sorted(cells, key=lambda c: c[0])[:5]]
    else:
        m |= {"permanence_mean_ncc": None, "permanence_worst_ncc": None,
              "permanence_chroma_worst": None, "permanence_hotspots": []}

    # Say when a number should not be trusted rather than returning it bare.
    warn = []
    if clamped > 0.15 * max(1, sum(len(b) - 1 for b in pidx)):
        warn.append(f"{clamped} alignment steps rejected as implausible; the "
                    "camera moves too fast here for permanence to mean much")
    if m["bg_tiles"] < 6:
        warn.append(f"only {m['bg_tiles']} background tiles survive the subject "
                    "mask; permanence rests on very little of the frame")
    if m["subject_box"] is None:
        warn.append("no subject region found; fell back to a fixed centre box")
    m["warnings"] = warn
    return m


KEYS = ["fps", "kbps", "noise_luma_slope", "clip_high_pct",
        "clip_low_pct", "displacement_px", "motion_mean", "ssim_min",
        "subject_stillness", "subject_vs_background", "permanence_mean_ncc",
        "permanence_worst_ncc", "permanence_chroma_worst"]


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "measure":
        sys.exit(__doc__)
    paths = sys.argv[2:]
    rs = pmap(measure, paths)
    print(json.dumps(rs, indent=1))
    if len(rs) > 1:
        w = 14
        print("\n%-28s%s" % ("metric", "".join(f"{r['file'][:13]:>{w}}" for r in rs)),
              file=sys.stderr)
        for k in KEYS:
            base, line = rs[0].get(k), "%-28s" % k
            for r in rs:
                val, flag = r.get(k), ""
                if r is not rs[0] and isinstance(val, (int, float)) \
                        and isinstance(base, (int, float)):
                    den = abs(base) if abs(base) > 1e-9 else 1.0
                    flag = " !" if abs(val - base) / den > 0.35 else ""
                line += f"{str(val) + flag:>{w}}"
            print(line, file=sys.stderr)
        # Grain survives in proportion to the bits spent on it, so per-band
        # noise levels are not comparable across a large bitrate gap.
        base_kbps = rs[0].get("kbps") or 0
        odd = [r["file"] for r in rs[1:]
               if base_kbps and r.get("kbps")
               and not 0.5 <= r["kbps"] / base_kbps <= 2.0]
        if odd:
            print(f"\nnote: bitrate differs from the reference by more than 2x "
                  f"({', '.join(odd)}).\n      noise_by_luma is not comparable "
                  f"across that gap; noise_luma_slope is.", file=sys.stderr)
        # displacement_px and motion_mean are pixel counts, so they scale with
        # frame height. Identical motion at different sizes reports in proportion.
        base_h = rs[0].get("height") or 0
        sized = [f"{r['file']} {r['width']}x{r['height']}" for r in rs[1:]
                 if base_h and r.get("height") and abs(r["height"] - base_h) > 1]
        if sized:
            print(f"\nnote: frame size differs from the reference's "
                  f"{rs[0]['width']}x{rs[0]['height']} ({', '.join(sized)}).\n"
                  f"      displacement_px and motion_mean are pixel counts and "
                  f"scale with it; multiply\n      by the height ratio before "
                  f"reading either as a difference in motion.", file=sys.stderr)
