#!/usr/bin/env python3
"""Video I/O shared by the measurement and post-processing tools."""
import os
from multiprocessing import Pool

import av
import cv2
import numpy as np
from scipy import ndimage

# Contiguous runs, for the metrics that compare ADJACENT frames.
NBLOCK, BLOCKLEN = 3, 16
BANDS = ((0, 64), (64, 128), (128, 192), (192, 256))
CENTRES = np.array([(lo + hi) / 2 for lo, hi in BANDS], float)


def probe(path):
    with av.open(path) as c:
        v = c.streams.video[0]
        return {"fps": float(v.average_rate),
                "kbps": round((c.bit_rate or 0) / 1000),
                "width": int(v.width), "height": int(v.height)}


def read(path, n=None):
    """Decode to (T, H, W, 3) uint8."""
    out = []
    with av.open(path) as c:
        for f in c.decode(video=0):
            out.append(f.to_ndarray(format="rgb24"))
            if n and len(out) >= n:
                break
    return np.asarray(out)


def count(path):
    """Frame count. The container header is trusted when it has one."""
    with av.open(path) as c:
        n = c.streams.video[0].frames
    if n:
        return int(n)
    with av.open(path) as c:                       # header lied; count them
        return sum(1 for _ in c.decode(video=0))


def spread(n, k):
    """k indices evenly across [0, n), including the first and last frame.

    Sampling the FIRST k frames instead biases every statistic toward the head of
    the clip, which is exactly where generated video looks best - degradation is
    end-loaded.
    """
    if n <= 0:
        return []
    if k <= 1:
        return [0]
    if k >= n:
        return list(range(n))
    return sorted({int(round(i * (n - 1) / (k - 1))) for i in range(k)})


def blocks(n, nblocks=NBLOCK, blocklen=BLOCKLEN):
    """nblocks contiguous runs of blocklen frames, spread across the clip with
    one anchored at the tail.

    Metrics comparing ADJACENT frames (displacement, frame-to-frame energy, SSIM)
    are only meaningful on genuinely consecutive frames, so they cannot use
    spread(). Contiguous blocks keep adjacency while still covering the whole
    clip, tail included.
    """
    blocklen = min(blocklen, n)
    if nblocks < 2 or n <= blocklen:
        return [list(range(blocklen))]
    starts = sorted({int(round(i * (n - blocklen) / (nblocks - 1)))
                     for i in range(nblocks)})
    return [list(range(s, s + blocklen)) for s in starts]


def pairs(idx):
    """Adjacent (u, v) index pairs within each block of blocks()."""
    for b in idx:
        yield from zip(b, b[1:])


def read_at(path, idx):
    """Decode once, keep only the requested indices. Returns {index: RGB frame}."""
    want = set(idx)
    if not want:
        return {}
    last, out = max(want), {}
    with av.open(path) as c:
        for i, f in enumerate(c.decode(video=0)):
            if i in want:
                out[i] = f.to_ndarray(format="rgb24")
            if i >= last:
                break
    return out


def to_gray(f):
    """Single RGB frame as float32 gray."""
    return cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32)


def pmap(fn, items):
    """Map fn over items, in parallel when there is more than one.

    Each worker holds a few hundred MB of decoded frames, so the cap is set by
    memory rather than by core count. VQ_JOBS overrides it. Results are identical
    to the serial ones; only the wall clock changes.
    """
    jobs = int(os.environ.get("VQ_JOBS", 0)) or min(4, os.cpu_count() or 1)
    if len(items) > 1 and jobs > 1:
        with Pool(min(len(items), jobs)) as pool:
            return pool.map(fn, items)
    return [fn(x) for x in items]


def write(frames, path, fps, crf=12):
    """Encode (T, H, W, 3) uint8 to H.264."""
    frames = np.ascontiguousarray(frames, np.uint8)
    with av.open(path, "w") as c:
        s = c.add_stream("libx264", rate=int(round(fps)))
        s.width, s.height, s.pix_fmt = frames.shape[2], frames.shape[1], "yuv420p"
        s.options = {"crf": str(crf)}
        for f in frames:
            for p in s.encode(av.VideoFrame.from_ndarray(f, format="rgb24")):
                c.mux(p)
        for p in s.encode():
            c.mux(p)


def luma(F):
    """Rec.601 luma. Keyed on a trailing size-3 axis so it is shape-agnostic."""
    F = F.astype(np.float32)
    if F.shape[-1] != 3:
        return F
    return F[..., 0] * .299 + F[..., 1] * .587 + F[..., 2] * .114


def luma_profile(F, min_px=20000):
    """Noise level in flat regions, per luma band. None where a band is too small
    to estimate.

    Flatness is ranked WITHIN each band. A single global gradient threshold selects
    almost only shadow and starves the bright bands to a handful of pixels, turning
    their estimate into numerical noise.
    """
    Y = luma(F)
    res = Y - ndimage.gaussian_filter(Y, (0, 1, 1))
    grad = ndimage.gaussian_gradient_magnitude(Y, (0, 1.5, 1.5))
    out = []
    for lo, hi in BANDS:
        inband = (Y >= lo) & (Y < hi)
        if inband.sum() < min_px:
            out.append(None)
            continue
        v = res[inband][grad[inband] < np.percentile(grad[inband], 40)]
        out.append(float(1.4826 * np.median(np.abs(v - np.median(v))))
                   if v.size else 0.0)
    return out
