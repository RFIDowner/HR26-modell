"""Normalvariasjon naer toppen av sideflatene (styrbord og babord) i baugen."""
import sys
import numpy as np
import cadquery as cq
from OCP.BRep import BRep_Tool
from OCP.GeomLProp import GeomLProp_SLProps
s = cq.Shape.importBrep(sys.argv[1])
fs = [f for f in s.Faces() if f.geomType() == "BSPLINE" and f.Area() > 1e7 and f.BoundingBox().zmin < 0]
for f in fs:
    srf = BRep_Tool.Surface_s(f.wrapped)
    u0, u1, v0, v1 = srf.Bounds()
    bb = f.BoundingBox()
    side = "stb" if bb.ymax > 100 else "port"
    print(side, "u", u0, u1, "v", v0, v1, "rational", srf.IsURational(), srf.IsVRational(), "poles", srf.NbUPoles(), srf.NbVPoles())
    W = np.array([[srf.Weight(i, j) for j in range(1, srf.NbVPoles() + 1)] for i in range(1, srf.NbUPoles() + 1)])
    print("   vekter min/max", W.min(), W.max())
    # u naer kanten mot hjoernebaandet
    us = np.linspace(u0, u1, 401)
    vs = np.linspace(v0, v0 + 0.25 * (v1 - v0), 60)
    worst = []
    for v in vs:
        P = np.array([[srf.Value(u, v).X(), srf.Value(u, v).Y(), srf.Value(u, v).Z()] for u in us])
        d1 = np.gradient(P, axis=0); d2 = np.gradient(d1, axis=0)
        sp = np.linalg.norm(d1, axis=1)
        k = np.linalg.norm(np.cross(d1, d2), axis=1) / np.maximum(sp ** 3, 1e-30)
        worst.append((round(P[0, 0]), round(float(sp.min() / sp.max()), 4), round(float(1.0 / k.max()), 1), round(float(us[np.argmax(k)]), 3)))
    print("   (x, min/max fart langs u, min radius, u der) :", worst[::6])
