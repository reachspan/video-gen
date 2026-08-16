#!/usr/bin/env python3
"""Camera-realism measurement.

  vq.py measure REF CAND...   metrics; first file is the reference
  vq.py viz OUT.png VIDEO...  motion rendered as stills

JSON on stdout, comparison table on stderr. Metrics are only meaningful
relative to a reference measured in the same run.

Excluded because they measure nothing at platform bitrates: lateral chromatic
aberration (chroma subsampling removes it), grain advection (handheld motion is
sub-pixel), raw temporal residual correlation (dominated by static texture),
vignetting (scene content dominates lens falloff).
"""
import json, sys
import cv2
import numpy as np
from scipy import ndimage
from skimage.metrics import structural_similarity as ssim
from vid import read, write, probe, luma, keyframes

SPATIAL, TEMPORAL = 24, 48


def blocks(img, gy, gx):
    """Reshape into a (gy, gx) grid of tiles, trimming any remainder."""
    h, w = img.shape
    bh, bw = h // gy, w // gx
    return img[:bh * gy, :bw * gx].reshape(gy, bh, gx, bw).swapaxes(1, 2)


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

    # optics: a lens is sharpest on axis; a renderer is sharpest on the subject
    mean = Y.mean(0)
    gy, gx = 6, 4
    tiles = blocks(mean, gy, gx)
    lap = np.array([[ndimage.gaussian_laplace(tiles[i, j], 1.0).std()
                     for j in range(gx)] for i in range(gy)])
    sd = tiles.std(axis=(2, 3))
    fld = np.where(sd > 3, lap / np.maximum(sd, 1e-6), np.nan)
    yy, xx = np.mgrid[0:gy, 0:gx]
    rad = np.hypot((yy + .5) / gy - .5, (xx + .5) / gx - .5)
    ok = ~np.isnan(fld)
    m["sharpness_radial_corr"] = round(float(np.corrcoef(rad[ok], fld[ok])[0, 1]), 3)
    m["sharpness_centre_vs_corner"] = round(float(
        np.nanmean(fld[2:4, 1:3]) / np.nanmean(
            [fld[0, 0], fld[0, -1], fld[-1, 0], fld[-1, -1]])), 3)

    P = np.abs(np.fft.fftshift(np.fft.fft2(Y[0] - Y[0].mean()))) ** 2
    cy, cx = np.array(P.shape) // 2
    ry, rx = np.ogrid[:P.shape[0], :P.shape[1]]
    r = np.hypot(ry - cy, rx - cx).astype(int)
    rp = np.bincount(r.ravel(), P.ravel()) / np.maximum(np.bincount(r.ravel()), 1)
    k = np.arange(3, min(len(rp), P.shape[0] // 2))
    m["fft_slope"] = round(float(np.polyfit(np.log(k), np.log(rp[k] + 1e-12), 1)[0]), 3)

    # camera: a hand is a damped mass, so its spectrum is 1/f, never white
    G = read(path, TEMPORAL, gray=True).astype(np.float32)
    sh, energy, ssims = [], [], []
    for i in range(len(G) - 1):
        (dx, dy), _ = cv2.phaseCorrelate(G[i], G[i + 1])
        sh.append((dy, dx))
        energy.append(float(np.abs(G[i + 1] - G[i]).mean()))
        ssims.append(float(ssim(G[i], G[i + 1], data_range=255)))
    sh = np.array(sh)
    d = np.hypot(sh[:, 0], sh[:, 1])
    S = np.abs(np.fft.rfft((d - d.mean()) * np.hanning(len(d)))) ** 2
    kk = np.arange(1, len(S))
    m["shake_spectral_slope"] = round(float(
        np.polyfit(np.log(kk), np.log(S[1:] + 1e-12), 1)[0]), 3)
    m["shake_peakiness"] = round(float(S[1:].max() / (np.median(S[1:]) + 1e-12)), 1)
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
        "pct_above_240", "clip_to_shoulder", "sharpness_radial_corr",
        "sharpness_centre_vs_corner", "fft_slope", "shake_spectral_slope",
        "shake_peakiness", "motion_mean", "motion_cv", "ssim_min",
        "permanence_mean_ncc", "permanence_worst_ncc"]


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
