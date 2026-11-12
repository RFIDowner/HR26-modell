"""Traced Enderlein lines in model coordinates (mm): loads the pixel traces,
cleans them (outlier removal, light smoothing) and converts with calib."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.ndimage import median_filter
import calib as K
from img import WORK

SNAP = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snap"))


def _load(name):
    return json.load(open(os.path.join(WORK, name)))


def clean_xy(p, along=0, med=5, tol=1.2):
    """Sort along an axis, drop points far from a running median of the
    other coordinate, return (N, 2)."""
    p = np.asarray(p, float)[:, :2]
    o = 1 - along
    p = p[np.argsort(p[:, along])]
    if len(p) > med:
        m = median_filter(p[:, o], size=med, mode="nearest")
        p = p[np.abs(p[:, o] - m) <= tol]
    return p


def smooth(p, along=0, w=5):
    p = np.asarray(p, float)
    if len(p) < w:
        return p
    o = 1 - along
    q = p.copy()
    k = np.ones(w) / w
    pad = np.r_[np.full(w // 2, p[0, o]), p[:, o], np.full(w // 2, p[-1, o])]
    q[:, o] = np.convolve(pad, k, mode="valid")
    return q


def profile_px():
    return _load("profile_px.json")


def profile_mm():
    """dict name -> (N, 2) array of (x, z) in mm (z above the drawing's DWL)."""
    d = profile_px()
    spec = {   # name: (axis along which the line is a function, median, tol)
        "hull_aft_bottom": (0, 7, 1.2), "hull_te_fillet": (0, 3, 2.0), "hull_te": (1, 7, 1.2),
        "hull_keel_bottom": (0, 7, 1.0), "hull_keel_le": (1, 5, 1.5), "hull_fwd_bottom": (0, 7, 1.2),
        "hull_stem": (1, 5, 1.5), "transom": (1, 7, 1.0), "rudder_le_upper": (1, 7, 1.0),
        "foredeck_cl": (0, 9, 0.8), "coachroof_front": (1, 3, 2.0), "roof_cl": (0, 9, 0.8),
        "seahood_top": (0, 7, 0.8), "hatch_top": (0, 9, 0.8), "forehatch_top": (0, 7, 0.8),
        "coachroof_aft_face": (1, 7, 1.0), "coaming_top": (0, 9, 0.9), "sheer_line": (0, 15, 0.8),
        "strake_line": (0, 15, 0.8), "aft_dashed_345": (0, 9, 1.0), "window_top": (0, 9, 0.8),
        "window_bottom": (0, 9, 0.8), "window_fwd_end": (1, 3, 2.0), "mast_aft_line": (1, 9, 0.8),
        "mast_fwd_line": (1, 9, 0.8), "dwl_dashes": (0, 1, 99),
    }
    out = {}
    for k, v in d.items():
        al, med, tol = spec.get(k, (0, 5, 1.5))
        p = clean_xy(v, al, med, tol)
        x, z = K.prof_xz(p[:, 0], p[:, 1])
        out[k] = np.c_[x, z]
    return out


def hull_outline_mm():
    """One ordered polyline: transom foot -> keel -> stem head, (x, z) mm."""
    pm = profile_mm()
    parts = []
    for k in ("hull_aft_bottom", "hull_te_fillet", "hull_te", "hull_keel_bottom",
              "hull_keel_le", "hull_fwd_bottom", "hull_stem"):
        p = pm[k]
        if k in ("hull_aft_bottom", "hull_keel_bottom", "hull_fwd_bottom"):
            p = p[np.argsort(-p[:, 0])]          # x decreasing = toward the bow? no: sort by px
        parts.append((k, p))
    return parts


def plan_mm():
    """deck outline: dict with 'top', 'bottom' (x, half-breadth >0) sorted by x,
    and 'bow_rows', 'transom_rows' (x, y signed)."""
    d = _load("plan_outline_px.json")
    out = {}
    for side in ("top", "bottom"):
        p = np.asarray(d[side], float)
        x, y = K.plan_xy(p[:, 0], p[:, 1])
        y = np.abs(y)
        q = np.c_[x, y, (p[:, 3] - p[:, 2]) * K.S]   # with ink width
        out[side] = q[np.argsort(q[:, 0])]
    for k in ("bow_rows", "transom_rows"):
        p = np.asarray(d[k], float)
        x, y = K.plan_xy(p[:, 0], p[:, 1])
        out[k] = np.c_[x, y]
    return out


def model():
    if SNAP not in sys.path:
        sys.path.insert(0, SNAP)
    from hr26 import curves as C, params as P
    return C, P
