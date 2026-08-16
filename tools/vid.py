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
