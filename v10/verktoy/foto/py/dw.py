"""Prototype: deadwood (wineglass) sections. The centreline profile stays curves.bottom_z (drawings); the convex
canoe-body section is built on a keel point raised by DW_H(x), and a smooth bump g(y/DW_W) carries the centreline
down to bottom_z, giving a hollow garboard."""
import sys, math; sys.path.insert(0, '.')
import numpy as np
import common as c

def install(C, dw_h, dw_w, shape=2.0):
    """dw_h, dw_w: callables x -> mm. Monkeypatch C._section_geom."""
    orig_bottom = C.bottom_z
    orig_geom = C._section_geom
    def geom(x):
        g = C._GEOM.get(("dw", x))
        if g is not None:
            return g
        h = max(float(dw_h(x)), 0.0)
        if h <= 0.5:
            g = orig_geom(x)
            C._GEOM[("dw", x)] = g
            return g
        zb = orig_bottom(x)
        C.bottom_z = lambda xx, _h=h: orig_bottom(xx) + _h      # canoe body keel point
        try:
            C._GEOM.pop(x, None)
            g = dict(orig_geom(x))
        finally:
            C.bottom_z = orig_bottom
            C._GEOM.pop(x, None)
        w = max(float(dw_w(x)), 1.0)
        pts = g["pts"].copy()
        t = np.clip(pts[:, 0] / w, 0.0, 1.0)
        pts[:, 1] -= h * (1.0 - t ** 2) ** shape
        seg = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
        g["pts"] = pts; g["s"] = np.r_[0.0, np.cumsum(seg)]
        g["K"] = np.array([0.0, zb]); g["zb"] = zb
        C._GEOM[("dw", x)] = g
        return g
    C._section_geom = geom
    C._GEOM.clear()
    return C
