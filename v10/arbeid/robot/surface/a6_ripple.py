"""Exact-surface waterlines of the bare loft (full scale): y(x) at fixed z, detrended."""
import sys, math
import numpy as np
COPY = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface/repo_copy"
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface"
sys.path.insert(0, COPY)
import cadquery as cq
from hr26 import curves as C, params as P
from scipy.interpolate import make_smoothing_spline
s = cq.Shape.importBrep(OUT + "/loft/loft_full.brep")
faces = s.Faces()
stb = [f for f in faces if f.geomType() == "BSPLINE" and f.Center().y > 100][0]
print("starboard face center", stb.Center())
xs_st = np.load(OUT + "/stations.npy")
res = {}
for z in (-300.0, -150.0, -50.0, 0.0, 50.0, 150.0, 300.0, 450.0, 600.0, 750.0):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
    so = BRepAlgoAPI_Section(stb.wrapped, gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)), False)
    so.Approximation(True); so.Build()
    sec = cq.Shape.cast(so.Shape())
    pts = []
    for e in sec.Edges():
        for t in np.linspace(0, 1, 4000):
            p = e.positionAt(t, mode="parameter"); pts.append((p.x, p.y))
    pts = np.array(pts)
    pts = pts[np.argsort(pts[:, 0])]
    # keep the outer branch (max y per x) and the x-range where it is a function of x
    xg = np.arange(math.ceil(pts[:, 0].min() / 5) * 5 + 50, math.floor(min(pts[:, 0].max(), 7700.0) / 5) * 5 - 50, 5.0)
    yg = np.interp(xg, pts[:, 0], pts[:, 1])
    # analytic intended half-breadth at this z
    ya = []
    for x in xg:
        sc = np.array(C.section(x, 400)); o = np.argsort(sc[:, 1])
        ya.append(np.interp(z, sc[o, 1], sc[o, 0]) if sc[:, 1].min() <= z <= sc[:, 1].max() else np.nan)
    ya = np.array(ya)
    # smooth trend: smoothing spline with large lam (wavelengths < ~1.2 m removed)
    sp = make_smoothing_spline(xg, yg, lam=2e9)
    r = yg - sp(xg)
    # second derivative (plan curvature) by finite differences over 40 mm
    h = 8
    d2 = (yg[2 * h:] - 2 * yg[h:-h] + yg[:-2 * h]) / (5.0 * h) ** 2
    # dominant wavelength of residual
    rr = r - r.mean(); F = np.abs(np.fft.rfft(rr * np.hanning(len(rr)))); fr = np.fft.rfftfreq(len(rr), 5.0)
    k = np.argmax(F[1:]) + 1
    res[z] = dict(x=xg, y=yg, ya=ya, r=r, d2x=xg[h:-h], d2=d2)
    dev = yg - ya
    print(f"z={z:6.0f}: x {xg[0]:.0f}..{xg[-1]:.0f}  residual vs smooth trend p-p {np.ptp(r):5.2f} mm (rms {r.std():.2f}) "
          f"= {np.ptp(r)/30:.3f} mm model; dominant wavelength {1/fr[k]:.0f} mm; loft-analytic dev p-p {np.nanmax(dev)-np.nanmin(dev):5.1f} (max |dev| {np.nanmax(np.abs(dev)):.1f})")
np.save(OUT + "/ripple.npy", res, allow_pickle=True)
