"""Undersoeker hjoernebaandet (avrundet dekkskant) i loften: x langs v, bredde."""
import sys
import numpy as np
import cadquery as cq
from OCP.BRep import BRep_Tool
s = cq.Shape.importBrep(sys.argv[1])
faces = [f for f in s.Faces() if f.geomType() == "BSPLINE" and 1e5 < f.Area() < 1e6]
f = faces[0]
srf = BRep_Tool.Surface_s(f.wrapped)
u0, u1, v0, v1 = srf.Bounds()
print("bounds u", u0, u1, "v", v0, v1)
vs = np.linspace(v0, v1, 4001)
for uu in (u0, 0.5 * (u0 + u1), u1):
    P = np.array([[srf.Value(uu, v).X(), srf.Value(uu, v).Y(), srf.Value(uu, v).Z()] for v in vs])
    dx = np.diff(P[:, 0])
    print(f"u={uu:.2f}: x {P[0,0]:.1f}..{P[-1,0]:.1f}, x monoton: {bool((dx > 0).all())}, min dx {dx.min():.4f}")
    # y langs x: kortbolget avvik (bow)
    m = P[:, 0] < 1600
    x, y, z = P[m, 0], P[m, 1], P[m, 2]
    xi = np.linspace(x.min(), x.max(), 800)
    yi = np.interp(xi, x, y); zi = np.interp(xi, x, z)
    d2y = np.gradient(np.gradient(yi, xi), xi)
    sc = np.sign(d2y[5:-5]); ch = int((np.diff(sc[np.abs(d2y[5:-5]) > 1e-6]) != 0).sum())
    print(f"   x<1600: y'' fortegnsskifter {ch}, maks |y''| {np.abs(d2y[5:-5]).max():.4f} ved x={xi[5:-5][np.argmax(np.abs(d2y[5:-5]))]:.0f}")
# bredden av baandet langs x
W = []
for v in np.linspace(v0, v1, 60):
    a = srf.Value(u0, v); b = srf.Value(u1, v)
    W.append((round(a.X()), round(np.hypot(a.Y() - b.Y(), a.Z() - b.Z()), 1)))
print("bredde (x, mm):", W[:14])
