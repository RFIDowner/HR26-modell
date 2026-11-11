"""Kantene i loften: type, lengde, antall knuter og poler (langs x)."""
import sys
import numpy as np
import cadquery as cq
from OCP.BRep import BRep_Tool
from OCP.GeomAdaptor import GeomAdaptor_Curve
s = cq.Shape.importBrep(sys.argv[1])
for i, e in enumerate(s.Edges()):
    L = e.Length()
    if L < 500:
        continue
    c = BRep_Tool.Curve_s(e.wrapped, 0.0, 1.0)
    a, b = e._bounds()
    ga = GeomAdaptor_Curve(c)
    info = ""
    try:
        bs = ga.BSpline()
        info = f"deg {bs.Degree()} knots {bs.NbKnots()} poles {bs.NbPoles()} rational {bs.IsRational()}"
    except Exception:
        pass
    bb = e.BoundingBox()
    # glatthet: krumning langs kanten
    ts = np.linspace(a, b, 3000)
    P = np.array([[c.Value(t).X(), c.Value(t).Y(), c.Value(t).Z()] for t in ts])
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    print(f"{i:2d} {e.geomType():8s} L={L:8.1f} x {bb.xmin:7.1f}..{bb.xmax:7.1f} y {bb.ymin:7.1f}..{bb.ymax:7.1f}  {info}  seg min/max {seg.min():.3f}/{seg.max():.3f}")
