#!/usr/bin/env python3
"""Algorithmic post-processing: deterministic signal transforms.

  post.py exposure REF CAND OUT    match clipping statistics to REF
  post.py shake REF CAND OUT       overlay handheld motion, matched to REF
  post.py grain REF CAND OUT       add grain matching REF's luma profile
  post.py chain REF CAND OUT       all three, in order

Order is fixed: photometric, then motion, then grain. Motion resamples and would
decorrelate grain from the luma profile it was fitted to.
"""
import subprocess, sys
import cv2
import numpy as np
from scipy import ndimage
from vid import read, write, probe, luma, count, spread, blocks, read_at

RNG = np.random.default_rng(7)


def sample(path, k):
    """k frames spread across the clip. Reference statistics taken from the first
    k frames instead would be biased toward the head of the shot."""
    idx = spread(count(path), k)
    f = read_at(path, idx)
    return np.stack([f[i] for i in idx])


BANDS = ((0, 64), (64, 128), (128, 192), (192, 256))
CENTRES = np.array([32, 96, 160, 224], float)


def clip_stats(F, chunk=16):
    """Fraction of pixels at each rail, computed in chunks to bound memory."""
    hi = lo = tot = 0
    for i in range(0, len(F), chunk):
        Y = luma(F[i:i + chunk])
        hi += int((Y >= 254).sum()); lo += int((Y <= 1).sum()); tot += Y.size
    return hi / tot * 100, lo / tot * 100


def levels_lut(rimax, romin):
    v = np.arange(256, dtype=np.float32) / 255.0
    return np.rint((np.clip(v / rimax, 0, 1) * (1 - romin) + romin) * 255
                   ).astype(np.uint8)


def apply_lut(F, lut):
    return cv2.LUT(F, lut)


def exposure(ref, cand, out=None):
    """Fit a per-channel levels map so luma clipping matches the reference.

    Solved on RGB because the transform is per-channel while the target statistic
    is luma, which only rails when all three channels do. A global levels map can
    only reach the right regime: response near the target is steep enough that a
    0.002 change in rimax swings clipping several-fold. A masked window-region
    lift is the better approach.
    """
    hi_t, lo_t = clip_stats(sample(ref, 48))
    C = read(cand)
    print(f"reference  high {hi_t:.3f}%  low {lo_t:.3f}%")
    print(f"candidate  high {clip_stats(C)[0]:.3f}%  low {clip_stats(C)[1]:.3f}%")

    # Solve on a random pixel sample: the transform is per-pixel, so a sample
    # estimates the tail fractions without touching the full clip each step.
    flat = C.reshape(-1, 3)
    idx = RNG.choice(len(flat), size=min(len(flat), 2_000_000), replace=False)
    P = flat[idx].reshape(1, -1, 3)

    def tails(rimax, romin):
        Y = luma(apply_lut(P, levels_lut(rimax, romin)))
        return float((Y >= 254).mean() * 100), float((Y <= 1).mean() * 100)

    grid = np.arange(0.90, 1.0005, 0.0005)
    rimax = float(grid[int(np.argmin([abs(tails(m, 0.0)[0] - hi_t) for m in grid]))])
    romin = 0.0
    if tails(rimax, 0.0)[1] > lo_t:
        for r in np.arange(0.0, 0.03, 0.0005):
            if tails(rimax, r)[1] <= lo_t:
                romin = float(r)
                break

    # Dither before quantising: a levels stretch maps 256 inputs onto fewer
    # outputs, and the resulting banding reads as a large false noise spike in
    # whichever luma band it lands in. Chunked to bound memory.
    G = np.empty_like(C)
    for i in range(0, len(C), 16):
        x = C[i:i + 16].astype(np.float32) / 255.0
        y = (np.clip(x / rimax, 0, 1) * (1 - romin) + romin) * 255.0
        y += RNG.uniform(-0.5, 0.5, y.shape).astype(np.float32)
        G[i:i + 16] = np.clip(np.rint(y), 0, 255).astype(np.uint8)
    print(f"solved     rimax={rimax:.4f} romin={romin:.4f}")
    print(f"graded     high {clip_stats(G)[0]:.3f}%  low {clip_stats(G)[1]:.3f}%")
    if out:
        write(G, out, probe(cand)["fps"])
    return G


def shake_path(n, fps, amp):
    """1/f sway + 4-13 Hz tremor + discrete corrections, per axis."""
    f = np.fft.rfftfreq(n, 1 / fps)
    def series():
        s = np.zeros_like(f); s[1:] = f[1:] ** -0.8
        sway = np.fft.irfft(s * np.exp(1j * RNG.uniform(0, 2 * np.pi, len(f))), n)
        band = ((f >= 4) & (f <= 13)).astype(float)
        trem = np.fft.irfft(band * np.exp(1j * RNG.uniform(0, 2 * np.pi, len(f))), n)
        t = sway / (sway.std() + 1e-9) + 0.22 * trem / (trem.std() + 1e-9)
        for _ in range(max(1, int(n / fps / 4))):
            step = np.zeros(n); step[RNG.integers(0, n):] = 0.7 * RNG.choice([-1, 1])
            t += ndimage.gaussian_filter1d(step, 2.5)
        return t / (t.std() + 1e-9)
    return amp * series(), amp * series(), 0.06 * amp * series()


def displacement(path, nblocks=3, blocklen=16):
    """Per-frame global translation magnitude, in pixels.

    Read in contiguous blocks spread across the clip: the pairs must be adjacent
    for phase correlation to mean anything, but taking them all from the opening
    seconds measures how the shot starts, not how it moves.
    """
    idx = blocks(count(path), nblocks, blocklen)
    f = read_at(path, [i for b in idx for i in b])
    d = []
    for b in idx:
        for u, v in zip(b, b[1:]):
            A = cv2.cvtColor(f[u], cv2.COLOR_RGB2GRAY).astype(np.float32)
            B = cv2.cvtColor(f[v], cv2.COLOR_RGB2GRAY).astype(np.float32)
            d.append(np.hypot(*cv2.phaseCorrelate(A, B)[0]))
    return np.array(d)


def shake(cand, out=None, amp=None, ref=None):
    """Overlay handheld motion. Amplitude is derived from a reference clip when
    given; a fixed constant overshoots badly, since real handheld inter-frame
    displacement is a fraction of a pixel."""
    C = read(cand)
    fps = probe(cand)["fps"]
    n, h, w = C.shape[:3]
    if amp is None:
        have = float(np.median(displacement(cand)))
        want = float(np.median(displacement(ref))) if ref else have
        amp = max(0.0, want - have)
        print(f"target {want:.3f}px  present {have:.3f}px  adding {amp:.3f}px")
    dx, dy, rot = shake_path(n, fps, amp)
    pad = int(np.ceil(max(np.abs(dx).max(), np.abs(dy).max()))) + 2
    G = np.empty_like(C)
    for i, fr in enumerate(C):
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot[i], 1.0)
        M[:, 2] += (dx[i], dy[i])
        G[i] = cv2.warpAffine(fr, M, (w, h), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)
    G = G[:, pad:h - pad, pad:w - pad]
    print(f"shake      amp={amp:.1f}px crop={pad}px frames={n}")
    if out:
        write(G, out, fps)
    return G


def luma_profile(F):
    """Noise level in flat regions, per luma band.

    Flatness is ranked within each band; a global gradient threshold selects
    almost only shadow and leaves the bright bands with too few pixels to measure.
    """
    Y = luma(F)
    res = Y - ndimage.gaussian_filter(Y, (0, 1, 1))
    g = ndimage.gaussian_gradient_magnitude(Y, (0, 1.5, 1.5))
    p = []
    for lo, hi in BANDS:
        inband = (Y >= lo) & (Y < hi)
        if inband.sum() < 20000:
            p.append(0.0)
            continue
        gb, rb = g[inband], res[inband]
        v = rb[gb < np.percentile(gb, 40)]
        p.append(float(1.4826 * np.median(np.abs(v - np.median(v)))) if v.size else 0.0)
    return p


def grain(ref, cand, out=None):
    """Add noise weighted by the reference's per-luma-band profile."""
    want, C = luma_profile(sample(ref, 32)), read(cand)
    have = luma_profile(C)
    print(f"reference  {[round(v, 3) for v in want]}")
    print(f"candidate  {[round(v, 3) for v in have]}")
    w = np.interp(luma(C), CENTRES, np.maximum(np.subtract(want, have), 0))
    z = RNG.normal(0, 1, C.shape[:3]).astype(np.float32)
    z = ndimage.gaussian_filter(z, (0, 0.5, 0.5))
    z /= z.std() + 1e-9
    G = np.clip(C.astype(np.float32) + (z * w)[..., None], 0, 255).astype(np.uint8)
    print(f"grained    {[round(v, 3) for v in luma_profile(G)]}")
    if out:
        write(G, out, probe(cand)["fps"])
    return G


def chain(ref, cand, out):
    a, b = out + ".e.mp4", out + ".s.mp4"
    exposure(ref, cand, a)
    shake(a, b, ref=ref)
    grain(ref, b, out)
    subprocess.run(["rm", "-f", a, b])


if __name__ == "__main__":
    c, a = sys.argv[1], sys.argv[2:]
    {"exposure": lambda: exposure(a[0], a[1], a[2]),
     "shake": lambda: shake(a[1], a[2], ref=a[0]),
     "grain": lambda: grain(a[0], a[1], a[2]),
     "chain": lambda: chain(a[0], a[1], a[2])}[c]()
