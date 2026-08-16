#!/usr/bin/env python3
"""Video I/O shared by the measurement and post-processing tools."""
import av
import numpy as np


def probe(path):
    with av.open(path) as c:
        s = c.streams.video[0]
        return {"w": s.codec_context.width, "h": s.codec_context.height,
                "fps": float(s.average_rate), "frames": s.frames,
                "codec": s.codec_context.name,
                "kbps": round((c.bit_rate or 0) / 1000)}


def read(path, n=None, gray=False, start=0):
    """Decode to (T, H, W[, 3]) uint8."""
    out = []
    with av.open(path) as c:
        for i, f in enumerate(c.decode(video=0)):
            if i < start:
                continue
            out.append(f.to_ndarray(format="gray" if gray else "rgb24"))
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
    if k >= n:
        return list(range(n))
    return sorted({int(round(i * (n - 1) / (k - 1))) for i in range(k)})


def blocks(n, nblocks, blocklen):
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


def keyframes(path):
    with av.open(path) as c:
        return [i for i, f in enumerate(c.decode(video=0)) if f.key_frame]
