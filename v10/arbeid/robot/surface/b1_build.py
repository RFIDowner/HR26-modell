"""Rebuild ONLY the bare hull loft in the scratch copy, export STLs at several tolerances,
and dump B-spline surface info. Never touches the repo."""
import sys, time, os
COPY = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface/repo_copy"
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface/loft"
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, COPY)
import cadquery as cq
from hr26 import hull as H, params as P, curves as C
import hr26
print("using", hr26.__file__)
t = time.time()
s = H.hull_solid(40, 26)
print("built %.1fs" % (time.time() - t))
sm = s.scale(1.0 / P.SCALE)
s.exportBrep(OUT + "/loft_full.brep")
from OCP.BRep import BRep_Tool
from OCP.GeomAdaptor import GeomAdaptor_Surface
from OCP.GeomAbs import GeomAbs_BSplineSurface
for i, f in enumerate(s.Faces()):
    surf = BRep_Tool.Surface_s(f.wrapped)
    ad = GeomAdaptor_Surface(surf)
    info = f"face {i}: {f.geomType():10s} area(full) {f.Area():12.0f}"
    if ad.GetType() == GeomAbs_BSplineSurface:
        bs = ad.BSpline()
        info += f"  udeg {bs.UDegree()} vdeg {bs.VDegree()}  uknots {bs.NbUKnots()} vknots {bs.NbVKnots()}  poles {bs.NbUPoles()}x{bs.NbVPoles()}"
        info += f"  U[{bs.FirstUKnotIndex()}] range {ad.FirstUParameter():.3f}..{ad.LastUParameter():.3f} V {ad.FirstVParameter():.3f}..{ad.LastVParameter():.3f}"
    print(info)
w = cq.Workplane("XY").newObject([sm])
for tol, ang in ((0.018, 0.12), (0.018, 0.03), (0.018, 0.01), (0.005, 0.03), (0.002, 0.02)):
    fn = f"{OUT}/loft_t{tol}_a{ang}.stl"
    t = time.time()
    cq.exporters.export(w, fn, tolerance=tol, angularTolerance=ang)
    n = (os.path.getsize(fn) - 84) // 50
    print(f"export tol {tol} ang {ang}: {n} triangles, {os.path.getsize(fn)/1e6:.1f} MB, {time.time()-t:.1f}s")
print("done")
