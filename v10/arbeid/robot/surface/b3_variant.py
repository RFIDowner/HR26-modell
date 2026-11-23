"""Variant loft in the scratch copy: same section points, but every section spline gets the
SAME parameter list (index-uniform), so the sections share one knot vector."""
import sys, os, time
import numpy as np
SC = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface"
COPY = SC + "/repo_copy"
sys.path.insert(0, COPY)
import cadquery as cq
from hr26 import hull as H, curves as C, params as P
from OCP.BRep import BRep_Tool
from OCP.GeomAdaptor import GeomAdaptor_Surface
from OCP.GeomAbs import GeomAbs_BSplineSurface

def section_wire_param(x, n_pts=24):
    pts = C.section(x, n=n_pts)
    stb = [cq.Vector(x, y, z) for (y, z) in pts]
    port = [cq.Vector(x, -y, z) for (y, z) in reversed(pts)]
    arc = [cq.Vector(x, y, z) for (y, z) in C.deck_arc(x)]
    u = list(np.linspace(0.0, 1.0, len(stb)))
    edges = [cq.Edge.makeSpline(stb, parameters=u)]
    if len(arc) > 2 and (arc[0] - arc[-1]).Length > 1e-6:
        a = [stb[-1]] + arc[1:-1] + [port[0]]
        edges.append(cq.Edge.makeSpline(a, parameters=list(np.linspace(0.0, 1.0, len(a)))))
    elif (stb[-1] - port[0]).Length > 1e-6:
        edges.append(cq.Edge.makeLine(stb[-1], port[0]))
    edges.append(cq.Edge.makeSpline(port, parameters=u))
    if (port[-1] - stb[0]).Length > 1e-6:
        edges.append(cq.Edge.makeLine(port[-1], stb[0]))
    return cq.Wire.assembleEdges(edges)

H._section_wire = section_wire_param
npts = [len(C.section(x, 26)) for x in C.stations(40)]
print("points per section (26 requested):", sorted(set(npts)))
t = time.time()
s = H.hull_solid(40, 26)
print("variant built %.1fs" % (time.time() - t))
for i, f in enumerate(s.Faces()):
    ad = GeomAdaptor_Surface(BRep_Tool.Surface_s(f.wrapped))
    if ad.GetType() == GeomAbs_BSplineSurface:
        bs = ad.BSpline()
        print(f"face {i}: udeg {bs.UDegree()} vdeg {bs.VDegree()} uknots {bs.NbUKnots()} vknots {bs.NbVKnots()} poles {bs.NbUPoles()}x{bs.NbVPoles()}")
sm = s.scale(1.0 / P.SCALE)
s.exportBrep(SC + "/loft/variant_full.brep")
cq.exporters.export(cq.Workplane().newObject([sm]), SC + "/loft/variant_rel0.018.stl", tolerance=0.018, angularTolerance=0.12)
sm.exportStl(SC + "/loft/variant_abs0.005.stl", tolerance=0.005, angularTolerance=0.05, relative=False)
sm.exportStl(SC + "/loft/variant_abs0.002.stl", tolerance=0.002, angularTolerance=0.05, relative=False)
for f in ("variant_rel0.018.stl", "variant_abs0.005.stl", "variant_abs0.002.stl"):
    print(f, (os.path.getsize(SC + "/loft/" + f) - 84) // 50, "triangles")
