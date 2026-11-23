"""Rebuild the bare hull loft (scratch copy of repo) and
 (a) sample the exact B-rep deck edge and topside waterlines,
 (b) re-tessellate it with the build's export settings and with absolute deflection."""
import sys, time, os
sys.dont_write_bytecode = True
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/"
sys.path.insert(0, D + "repo")
import numpy as np
import cadquery as cq
from hr26 import hull as H, curves as C, params as P
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir

t0 = time.time()
solid = H.hull_solid(40, 26)
print("loft+transom cut: %.1fs, faces %d, edges %d, volume %.3f m3" % (
    time.time() - t0, len(solid.Faces()), len(solid.Edges()), solid.Volume() / 1e9))

# ---- (a1) deck edge on y>0
best = None
for e in solid.Edges():
    ps = np.array([e.positionAt(t).toTuple() for t in np.linspace(0, 1, 50)])
    if ps[:, 1].mean() <= 0:
        continue
    d = [abs(p[1] - C.deck_half_breadth(p[0])) + abs(p[2] - C.sheer_z(p[0])) for p in ps]
    span = np.ptp(ps[:, 0])
    print("  edge: x %.0f-%.0f  y %.0f-%.0f  mean |dev| %.1f  len %.0f" % (ps[:, 0].min(), ps[:, 0].max(), ps[:, 1].min(), ps[:, 1].max(), np.mean(d), e.Length()))
    if np.mean(d) < 15 and span > 5000:
        best = e
assert best is not None
ps = np.array([best.positionAt(t).toTuple() for t in np.linspace(0, 1, 20001)])
ps = ps[np.argsort(ps[:, 0])]
np.save(D + "brep_deckedge.npy", ps)
print("deck edge sampled: x %.1f .. %.1f" % (ps[0, 0], ps[-1, 0]))


# ---- (a2) waterlines (z above DWL) and buttocks
def section_pts(shape, pln, n=3000):
    sec = BRepAlgoAPI_Section(shape.wrapped, pln)
    sec.Build()
    sh = cq.Shape.cast(sec.Shape())
    out = []
    for e in sh.Edges():
        L = e.Length()
        k = max(20, int(n * L / 8000.0))
        out.append(np.array([e.positionAt(t).toTuple() for t in np.linspace(0, 1, k)]))
    return out

wls = {}
for z in [150.0, 400.0, 700.0, 900.0]:
    segs = section_pts(solid, gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)), n=8000)
    pts = np.vstack(segs)
    pts = pts[pts[:, 1] > 1.0]
    pts = pts[np.argsort(pts[:, 0])]
    wls[z] = pts
    print("waterline z=%.0f: %d pts, x %.0f..%.0f, edges %d" % (z, len(pts), pts[0, 0], pts[-1, 0], len(segs)))
np.savez(D + "brep_waterlines.npz", **{f"z{int(k)}": v for k, v in wls.items()})

# ---- (b) tessellation tests, in model scale placed like build.export (rot 45, lay flat)
wp = cq.Workplane("XY").newObject([solid.scale(1.0 / P.SCALE)])
wp = wp.rotate((0, 0, 0), (0, 0, 1), 45.0)
bb = wp.val().BoundingBox()
wp = wp.translate((-(bb.xmin + bb.xmax) / 2.0, -(bb.ymin + bb.ymax) / 2.0, -bb.zmin))
shape = wp.val()
for tag, tol, ang, rel in [("rel_0.018_0.12", 0.018, 0.12, True),
                           ("abs_0.018_0.12", 0.018, 0.12, False),
                           ("abs_0.01_0.05", 0.01, 0.05, False)]:
    fn = D + f"loft_{tag}.stl"
    t1 = time.time()
    if rel:
        cq.exporters.export(cq.Workplane("XY").newObject([shape]), fn, tolerance=tol, angularTolerance=ang)
    else:
        # fresh copy so the earlier triangulation is not reused
        shp = cq.Shape.cast(shape.copy().wrapped) if hasattr(shape, "copy") else shape
        from OCP.BRepTools import BRepTools
        BRepTools.Clean_s(shp.wrapped)
        shp.exportStl(fn, tolerance=tol, angularTolerance=ang, relative=False)
    n = (os.path.getsize(fn) - 84) // 50
    print(f"{tag}: {n} triangles, {os.path.getsize(fn)/1e6:.1f} MB, {time.time()-t1:.1f}s")
    from OCP.BRepTools import BRepTools
    BRepTools.Clean_s(shape.wrapped)
print("done %.1fs" % (time.time() - t0))
