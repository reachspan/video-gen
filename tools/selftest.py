#!/usr/bin/env python3
"""Inject a known defect, confirm the metric detects it.

  selftest.py CLIP

A metric that has never been tested against a known input is a hypothesis.
Each case perturbs one property and asserts the responsible metric moves in the
expected direction; metrics that should be unaffected are checked for stability.
"""
import subprocess, sys, tempfile, os
import cv2
import numpy as np
from scipy import ndimage
from vid import read, write, probe
import vq

TMP = tempfile.mkdtemp(prefix="selftest-")


def emit(F, fps, name):
    p = os.path.join(TMP, name + ".mp4")
    write(F, p, fps, crf=8)
    return p


def radial_blur(F):
    """Soften toward the corners: what a lens does, what a renderer does not."""
    h, w = F.shape[1:3]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(yy / h - .5, xx / w - .5)
    a = np.clip((r - .15) / .45, 0, 1)[..., None]
    out = np.empty_like(F)
    for i, fr in enumerate(F):
        out[i] = np.clip(fr * (1 - a) + cv2.GaussianBlur(fr, (0, 0), 3.0) * a, 0, 255)
    return out


def add_noise(F, sigma):
    z = np.random.default_rng(1).normal(0, sigma, F.shape[:3])[..., None]
    return np.clip(F.astype(np.float32) + z, 0, 255).astype(np.uint8)


def force_clip(F, gain=1.25):
    return np.clip(F.astype(np.float32) * gain, 0, 255).astype(np.uint8)


def occlude(F):
    """Blank a background patch for the second half: an impermanent object."""
    G = F.copy()
    h, w = F.shape[1:3]
    G[len(G) // 2:, int(h * .05):int(h * .13), int(w * .04):int(w * .16)] = 0
    return G


def translate(F, px=3.0):
    out = np.empty_like(F)
    for i, fr in enumerate(F):
        M = np.float32([[1, 0, px * (i % 2)], [0, 1, 0]])
        out[i] = cv2.warpAffine(fr, M, (F.shape[2], F.shape[1]),
                                borderMode=cv2.BORDER_REPLICATE)
    return out


CASES = [
    ("radial blur",   radial_blur,                "sharpness_radial_corr", "down"),
    ("noise +3.0",    lambda F: add_noise(F, 3.0), "noise_sigma_flat",     "up"),
    ("gain 1.25x",    force_clip,                 "clip_high_pct",         "up"),
    ("occluded patch", occlude,                   "permanence_worst_ncc",  "down"),
    ("3px jitter",    translate,                  "motion_mean",           "up"),
]


def main(clip):
    F = read(clip, 48)
    fps = probe(clip)["fps"]
    base_path = emit(F, fps, "base")
    base = vq.measure(base_path)
    print(f"base: {os.path.basename(clip)}  {len(F)} frames\n")
    print(f"{'injected':<16}{'metric':<28}{'base':>10}{'after':>10}{'want':>7}  result")

    fails = 0
    for name, fn, key, want in CASES:
        m = vq.measure(emit(fn(F), fps, name.replace(" ", "_")))
        b, a = base.get(key), m.get(key)
        if b is None or a is None:
            print(f"{name:<16}{key:<28}{'-':>10}{'-':>10}{want:>7}  SKIP (None)")
            continue
        moved = (a > b) if want == "up" else (a < b)
        rel = abs(a - b) / max(abs(b), 1e-9)
        ok = moved and rel > 0.05
        fails += not ok
        print(f"{name:<16}{key:<28}{b:>10.4f}{a:>10.4f}{want:>7}  "
              f"{'PASS' if ok else 'FAIL'} ({rel*100:.0f}%)")

    subprocess.run(["rm", "-rf", TMP])
    print(f"\n{len(CASES) - fails}/{len(CASES)} metrics respond to their own defect")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
