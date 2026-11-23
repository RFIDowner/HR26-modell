"""Shared image access for the Enderlein drawing 448-5 (read-only)."""
import os

import numpy as np
from PIL import Image

SRC = os.path.join(os.path.expanduser("~"), "Documents", "Seilbåt", "Hallberg-Rassy-kilder",
                   "HR26interior448-5.jpeg")
WORK = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "work"))
OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def gray():
    """Grey image as float array, 0 = black, 255 = white. Index [y, x]."""
    return np.asarray(Image.open(SRC).convert("L"), dtype=float)


def rgb():
    return Image.open(SRC).convert("RGB")


def dark(a, thr=150):
    return a < thr


def runs(mask1d):
    """Start/end (inclusive) of True runs in a 1-D boolean array."""
    m = np.r_[False, mask1d, False].astype(int)
    d = np.diff(m)
    s = np.where(d == 1)[0]
    e = np.where(d == -1)[0] - 1
    return list(zip(s, e))


def centroid_runs(profile, thr):
    """Sub-pixel centres of dark runs in a 1-D grey profile (darkness weighted)."""
    out = []
    for s, e in runs(profile < thr):
        w = np.clip(255.0 - profile[s:e + 1], 0, None)
        c = float(np.sum(np.arange(s, e + 1) * w) / max(np.sum(w), 1e-9))
        out.append((c, s, e, float(profile[s:e + 1].min())))
    return out
