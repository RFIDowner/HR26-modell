"""How far does the OCC interpolating spline stray from the formula it samples? (full-scale mm)"""
import sys, math
import numpy as np
sys.path.insert(0, r"C:/Users/stig/Documents/GitHub/HR26-modell")
from hr26 import curves as C, params as P
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.gp import gp_Pnt

FR = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def spl(x, pts, n=6000):
    e = cq.Edge.makeSpline([cq.Vector(x, y, z) for (y, z) in pts])
    ad = BRepAdaptor_Curve(e.wrapped)
    us = np.linspace(ad.FirstParameter(), ad.LastParameter(), n)
    out = []
    for u in us:
        p = gp_Pnt(); ad.D0(u, p); out.append((p.Y(), p.Z()))
    return np.array(out)


def normal_dev(test, ref):
    """signed distance of each test point to polyline ref (+ = outward = larger y side)"""
    seg_a = ref[:-1]; seg_b = ref[1:]
    d = seg_b - seg_a
    L2 = (d ** 2).sum(1)
    res = []
    for p in test:
        t = np.clip(((p - seg_a) * d).sum(1) / np.maximum(L2, 1e-12), 0, 1)
        q = seg_a + t[:, None] * d
        dist = np.hypot(*(p - q).T)
        j = int(np.argmin(dist))
        # outward normal of ref segment (walking keel->deck, outward is to the right: (dz, -dy))
        nrm = np.array([d[j, 1], -d[j, 0]]) / math.sqrt(L2[j])
        res.append(np.sign(((p - q[j]) * nrm).sum()) * dist[j])
    return np.array(res)


print(f"{'f':>5} {'x':>5} | spline-formula dev (mm, + = outward): below DWL max+/max- | 0..300 above | 300..deck | z of worst above")
for f in FR:
    x = f * P.LOA
    pts = C.section(x, n=26)
    S = spl(x, pts)
    A = np.array(C.section(x, n=8000))
    dev = normal_dev(S[::6], A)
    Z = S[::6, 1]
    b = Z < 0; a1 = (Z >= 0) & (Z < 300); a2 = Z >= 300
    def mm(s):
        return (round(dev[s].max(), 1), round(dev[s].min(), 1)) if s.any() else ("-", "-")
    ja = np.nonzero(Z >= 0)[0]
    jw = ja[np.argmax(np.abs(dev[ja]))]
    print(f"{f:5.2f} {x:5.0f} | {mm(b)} | {mm(a1)} | {mm(a2)} | z={Z[jw]:.0f} dev={dev[jw]:.1f}")
