#!/usr/bin/env python3
"""Camera-realism measurement.

  vq.py measure REF CAND...   metrics; first file is the reference
  vq.py viz OUT.png VIDEO...  motion rendered as stills

JSON on stdout, comparison table on stderr. Metrics are only meaningful
relative to a reference measured in the same run.

Every metric here is validated two ways: it responds to its own injected defect
(tools/selftest.py) and it separates generated output from real footage by more
than real footage varies from itself.

Excluded for measuring nothing at platform bitrates: lateral chromatic aberration,
grain advection, raw temporal residual correlation, vignetting.

Excluded for failing calibration - real segments of one camera disagree with each
other as much as they disagree with generated output: sharpness radial falloff and
centre/corner ratio (sign flips with subject placement), shake spectral slope and
peakiness, radial FFT slope.
"""
import json, sys
import cv2
import numpy as np
from scipy import ndimage
from skimage.metrics import structural_similarity as ssim
from vid import read, probe, luma, keyframes

SPATIAL, TEMPORAL = 24, 48


def measure(path):
    m = {"file": path.split("/")[-1]}
    p = probe(path)
    kf = keyframes(path)
    m |= {"fps": round(p["fps"], 2), "kbps": p["kbps"],
          "gop": (kf[1] - kf[0]) if len(kf) > 1 else None}

    F = read(path, SPATIAL)
    Y = luma(F)

    # grain: real sensors peak in the low-mids, not the deep shadows.
    # Flatness is ranked WITHIN each luma band. A single global gradient
    # threshold selects almost only shadow, starving the bright bands to a
    # handful of pixels and turning their MAD into numerical noise.
    res = Y - ndimage.gaussian_filter(Y, (0, 1, 1))
    grad = ndimage.gaussian_gradient_magnitude(Y, (0, 1.5, 1.5))
    mad = lambda x: float(1.4826 * np.median(np.abs(x - np.median(x)))) if x.size else 0.0
    m["noise_sigma_flat"] = round(mad(res[grad < np.percentile(grad, 40)]), 4)

    prof = []
    for lo, hi in ((0, 64), (64, 128), (128, 192), (192, 256)):
        inband = (Y >= lo) & (Y < hi)
        if inband.sum() < 20000:
            prof.append(None)
            continue
        g, r = grad[inband], res[inband]
        prof.append(round(mad(r[g < np.percentile(g, 40)]), 3))
    m["noise_by_luma"] = prof
    v = [x for x in prof if x]
    m["noise_luma_ratio"] = round(max(v) / min(v), 2) if len(v) > 1 else None

    # exposure: sensors rail, renderers roll off
    h = np.bincount(Y.astype(np.uint8).ravel(), minlength=256).astype(float)
    t = h.sum()
    m["clip_high_pct"] = round(float(h[254:].sum() / t * 100), 3)
    m["clip_low_pct"] = round(float(h[:2].sum() / t * 100), 3)
    m["pct_above_240"] = round(float(h[240:].sum() / t * 100), 3)
    m["clip_to_shoulder"] = round(float(h[254:].sum() / (h[235:250].sum() + 1e-9)), 3)

    # camera motion and temporal stability
    G = read(path, TEMPORAL, gray=True).astype(np.float32)
    sh, energy, ssims = [], [], []
    for i in range(len(G) - 1):
        (dx, dy), _ = cv2.phaseCorrelate(G[i], G[i + 1])
        sh.append((dy, dx))
        energy.append(float(np.abs(G[i + 1] - G[i]).mean()))
        ssims.append(float(ssim(G[i], G[i + 1], data_range=255)))
    sh = np.array(sh)
    m["displacement_px"] = round(float(np.median(np.hypot(sh[:, 0], sh[:, 1]))), 3)
    e = np.array(energy)
    m["motion_mean"] = round(float(e.mean()), 3)
    m["motion_cv"] = round(float(e.std() / (e.mean() + 1e-9)), 3)
    m["ssim_min"] = round(float(np.min(ssims)), 4)

    # object permanence: background tiles, motion compensated, against frame 0
    h_, w_ = G.shape[1:]
    bg = np.ones((h_, w_), bool)
    bg[int(h_ * .15):int(h_ * .95), int(w_ * .20):int(w_ * .80)] = False
    cy_, cx_ = np.cumsum(sh[:, 0]), np.cumsum(sh[:, 1])
    sims = []
    for t_ in range(1, len(G)):
        M = np.float32([[1, 0, cx_[t_ - 1]], [0, 1, cy_[t_ - 1]]])
        al = cv2.warpAffine(G[t_], M, (w_, h_), borderMode=cv2.BORDER_REPLICATE)
        for i in range(6):
            for j in range(4):
                ys = slice(i * h_ // 6, (i + 1) * h_ // 6)
                xs = slice(j * w_ // 4, (j + 1) * w_ // 4)
                if not bg[ys, xs].any():
                    continue
                a, b = G[0][ys, xs].ravel(), al[ys, xs].ravel()
                if a.std() > 3 and b.std() > 3:
                    sims.append(float(np.corrcoef(a, b)[0, 1]))
    m["permanence_mean_ncc"] = round(float(np.mean(sims)), 4) if sims else None
    m["permanence_worst_ncc"] = round(float(np.min(sims)), 4) if sims else None
    return m


KEYS = ["fps", "kbps", "gop", "noise_sigma_flat", "noise_luma_ratio", "clip_high_pct",
        "clip_low_pct", "pct_above_240", "clip_to_shoulder", "displacement_px",
        "motion_mean", "motion_cv", "ssim_min", "permanence_mean_ncc",
        "permanence_worst_ncc"]


def viz(out, paths):
    rows, rep = [], {}
    for p in paths:
        F = read(p)[::3]
        F = np.stack([cv2.resize(f, (300, int(300 * f.shape[0] / f.shape[1])))
                      for f in F])
        Y = luma(F)
        dev = np.abs(Y - Y[0]).max(0)          # anything black here never moved
        con = np.abs(np.diff(Y, axis=0)).mean(0)
        n = lambda a, g: np.clip(a * g, 0, 255).astype(np.uint8)
        rows.append(np.concatenate([F[0], np.stack([n(dev, 3.0)] * 3, -1),
                                    np.stack([n(con, 12.0)] * 3, -1)], axis=1))
        s = np.abs(np.diff(Y, axis=0)).mean((1, 2))
        rep[p.split("/")[-1]] = {
            "motion_p10_50_90": [round(float(np.percentile(s, q)), 2) for q in (10, 50, 90)],
            "burstiness_cv": round(float(s.std() / (s.mean() + 1e-9)), 3)}
    W = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0))) for r in rows]
    cv2.imwrite(out, cv2.cvtColor(np.concatenate(rows, 0), cv2.COLOR_RGB2BGR))
    return rep


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "viz":
        print(json.dumps(viz(sys.argv[2], sys.argv[3:]), indent=1))
    else:
        rs = [measure(p) for p in sys.argv[2:]]
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
