#!/usr/bin/env python3
"""Inject a known defect, confirm the metric detects it.

  selftest.py CLIP

A metric that has never been tested against a known input is a hypothesis.
Each case perturbs one property and asserts the responsible metrics move in the
expected direction.

This proves a metric measures what it claims. It does not prove the metric
separates generated footage from real footage — none of them does, so a passing
metric is a usable pointer, not a detector. See docs/pitfalls.md.

A metric with no case is UNCOVERED and is reported as a failure: silence about a
metric is not evidence for it.
"""
import subprocess, sys, tempfile, os
import cv2
import numpy as np
from vid import read, write, probe
import vq

TMP = tempfile.mkdtemp(prefix="selftest-")


def emit(F, fps, name):
    p = os.path.join(TMP, name + ".mp4")
    write(F, p, fps, crf=8)
    return p


def highlight_noise(F, sigma=4.0):
    """Noise only in the bright bands: tilts the noise-vs-luma profile upward."""
    Y = F.astype(np.float32).mean(-1)
    w = np.clip((Y - 140) / 60.0, 0, 1)[..., None]
    z = np.random.default_rng(2).normal(0, sigma, F.shape[:3])[..., None]
    return np.clip(F.astype(np.float32) + z * w, 0, 255).astype(np.uint8)


def force_clip(F, gain=1.25):
    return np.clip(F.astype(np.float32) * gain, 0, 255).astype(np.uint8)


def crush_black(F, off=40):
    return np.clip(F.astype(np.float32) - off, 0, 255).astype(np.uint8)


def occlude(F):
    """Blank tile (0,0) for the second half: an object that vanishes.

    Covers the whole tile. Blanking part of one leaves the rest of its texture
    correlated, and real footage produces worse cells than that unaided, so a
    partial defect would prove nothing.
    """
    G = F.copy()
    h, w = F.shape[1:3]
    G[len(G) // 2:, 0:h // 6, 0:w // 4] = 0
    return G


def morph(F, amp=40.0):
    """A growing low-frequency warp. Global translation compensation cannot
    remove it, so it decorrelates EVERY background tile — the global-degradation
    case, as opposed to occlude()'s single localized one.

    Amplitude comes from the metric's measured sensitivity: permanence_mean_ncc
    moves 5.1% at 20px, 14.6% at 40px and 29.4% at 80px. The mean only registers
    gross degradation, with a floor around 20px; below that read the worst tile.
    """
    h, w = F.shape[1:3]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.empty_like(F)
    for i, fr in enumerate(F):
        k = amp * i / max(len(F) - 1, 1)
        mx = xx + k * np.sin(4 * np.pi * yy / h)
        my = yy + k * np.cos(4 * np.pi * xx / w)
        out[i] = cv2.remap(fr, mx, my, cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_REPLICATE)
    return out


def recolour(F, shift=40):
    """Push tile (0,1) warm for the second half: a tile that stays structurally
    correlated while its colour changes. An explicit R-up/B-down cast, since a
    channel swap does nothing on the neutral greys that fill much of a frame.
    """
    G = F.copy().astype(np.int16)
    h, w = F.shape[1:3]
    sl = (slice(len(G) // 2, None), slice(0, h // 6), slice(w // 4, w // 2))
    G[sl][..., 0] += shift
    G[sl][..., 2] -= shift
    return np.clip(G, 0, 255).astype(np.uint8)


def translate(F, px=3.0):
    out = np.empty_like(F)
    for i, fr in enumerate(F):
        M = np.float32([[1, 0, px * (i % 2)], [0, 1, 0]])
        out[i] = cv2.warpAffine(fr, M, (F.shape[2], F.shape[1]),
                                borderMode=cv2.BORDER_REPLICATE)
    return out


def freeze_subject(F):
    """Paste the centre of the midpoint frame over every later frame: the subject
    stops moving while the camera and the edges carry on. This is T1 statue torso,
    injected directly."""
    G = F.copy()
    h, w = F.shape[1:3]
    ys, xs = slice(int(h * .15), int(h * .95)), slice(int(w * .20), int(w * .80))
    still = F[len(F) // 2][ys, xs]
    for i in range(len(F) // 2, len(F)):
        G[i][ys, xs] = still
    return G


def burst(F, px=4.0):
    """Motion concentrated in one burst: same mean energy, uneven over time."""
    out = F.copy()
    a, b = len(F) // 3, 2 * len(F) // 3
    for i in range(a, b):
        M = np.float32([[1, 0, px * ((i - a) % 2)], [0, 1, 0]])
        out[i] = cv2.warpAffine(F[i], M, (F.shape[2], F.shape[1]),
                                borderMode=cv2.BORDER_REPLICATE)
    return out


def blur_one(F):
    """Soften a single frame: a one-off temporal discontinuity."""
    G = F.copy()
    G[len(G) // 2] = cv2.GaussianBlur(F[len(F) // 2], (0, 0), 4.0)
    return G


# (label, injection, [(metric, expected direction), ...])
CASES = [
    ("highlight noise", highlight_noise,            [("noise_luma_slope", "up")]),
    ("gain 1.25x",     force_clip,                  [("clip_high_pct", "up")]),
    ("crush -40",      crush_black,                 [("clip_low_pct", "up")]),
    ("occluded patch", occlude,                     [("permanence_worst_ncc", "down")]),
    ("global morph",   morph,                       [("permanence_mean_ncc", "down")]),
    ("recoloured patch", recolour,                  [("permanence_chroma_worst", "up")]),
    ("3px jitter",     translate,                   [("motion_mean", "up"),
                                                     ("displacement_px", "up")]),
    ("frozen subject", freeze_subject,              [("subject_stillness", "down"),
                                                     ("subject_vs_background", "down")]),
    ("one blurred frame", blur_one,                 [("ssim_min", "down")]),
]


def main(clip):
    F = read(clip, 48)
    fps = probe(clip)["fps"]
    base = vq.measure(emit(F, fps, "base"))
    print(f"base: {os.path.basename(clip)}  {len(F)} frames\n")
    print(f"{'injected':<18}{'metric':<24}{'base':>10}{'after':>10}{'want':>6}  result")

    covered, fails, measured = set(), 0, {}
    for name, fn, asserts in CASES:
        m = measured[name] = vq.measure(emit(fn(F), fps, name.replace(" ", "_")))
        for key, want in asserts:
            covered.add(key)
            b, a = base.get(key), m.get(key)
            if b is None or a is None:
                print(f"{name:<18}{key:<24}{'-':>10}{'-':>10}{want:>6}  FAIL (metric absent)")
                fails += 1
                continue
            moved = (a > b) if want == "up" else (a < b)
            rel = abs(a - b) / max(abs(b), 1e-9)
            ok = moved and rel > 0.05
            fails += not ok
            print(f"{name:<18}{key:<24}{b:>10.4f}{a:>10.4f}{want:>6}  "
                  f"{'PASS' if ok else 'FAIL'} ({rel * 100:.0f}%)")

    # Localization is the whole point of the hotspot list: a metric that reacts
    # to a defect but points somewhere else cannot drive a repair. occlude()
    # blanks rows .05-.13h and cols .04-.16w of the second half, which is tile
    # (0, 0) on a 6x4 grid, from the midpoint on.
    hs = (measured["occluded patch"].get("permanence_hotspots") or [None])[0]
    if hs is None:
        print(f"{'occluded patch':<18}{'permanence_hotspots':<24}{'-':>10}{'-':>10}"
              f"{'-':>6}  FAIL (no hotspots)")
        fails += 1
    else:
        ok = hs["tile"] == [0, 0] and hs["frame"] >= len(F) // 2
        fails += not ok
        print(f"{'occluded patch':<18}{'hotspot -> (frame,tile)':<24}"
              f"{'(0,0)':>10}{str(tuple(hs['tile'])):>10}{'@' + str(hs['frame']):>6}  "
              f"{'PASS' if ok else 'FAIL'} (ncc {hs['ncc']})")
    covered.add("permanence_hotspots")

    # A metric nobody injected against is untested, not passing.
    uncovered = [k for k in vq.KEYS if k not in covered
                 and k not in ("fps", "kbps", "gop")]
    for k in uncovered:
        print(f"{'-':<18}{k:<24}{'-':>10}{'-':>10}{'-':>6}  UNCOVERED")

    subprocess.run(["rm", "-rf", TMP])
    n = sum(len(a) for _, _, a in CASES) + 1   # + the localization check
    print(f"\n{n - fails}/{n} assertions pass; {len(uncovered)} metric(s) uncovered")
    return 1 if (fails or uncovered) else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
