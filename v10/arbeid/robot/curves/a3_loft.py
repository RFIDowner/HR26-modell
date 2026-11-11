"""Build ONLY the hull loft (hull_solid, as in build_hull: 40 stations, 26 pts)
from the scratch copy of the repo, and sample the exact B-rep deck-edge curve
and a few waterlines / buttocks of the loft. No files are exported."""
import sys, os, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "repo"))
import cadquery as cq
from hr26 import curves as C
from hr26 import hull as H
from hr26 import params as P
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_UniformAbscissa
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir

t0 = time.time()
s = H.hull_solid(40, 26)
print(f"loft built in {time.time()-t0:.1f}s, volume {s.Volume()/1e9:.3f} m3, faces {len(s.Faces())}, edges {len(s.Edges())}")

def sample_edge(e, step=5.0):
    c = BRepAdaptor_Curve(e.wrapped)
    u0, u1 = c.FirstParameter(), c.LastParameter()
    n = max(50, int(e.Length() / step))
    us = np.linspace(u0, u1, n)
    return np.array([[c.Value(u).X(), c.Value(u).Y(), c.Value(u).Z()] for u in us])

# deck edge: edges whose points lie at |y| ~ deck_half_breadth and z ~ sheer_z
out = {}
for i, e in enumerate(s.Edges()):
    pts = sample_edge(e, 20.0)
    if np.ptp(pts[:, 0]) < 2000:
        continue
    hb = np.array([C.deck_half_breadth(x) for x in pts[:, 0]])
    zs = np.array([C.sheer_z(x) for x in pts[:, 0]])
    dy = np.abs(np.abs(pts[:, 1]) - hb).max(); dz = np.abs(pts[:, 2] - zs).max()
    print(f"edge {i}: x {pts[:,0].min():.0f}-{pts[:,0].max():.0f}, y sign {np.sign(pts[:,1].mean()):+.0f}, max|dy| {dy:.1f} max|dz| {dz:.1f}, len {e.Length():.0f}")
    if dy < 40 and dz < 40 and pts[:, 1].mean() > 0:
        out["deck_edge"] = sample_edge(e, 5.0)

# waterlines and buttocks through the loft (exact B-rep sections)
def section_pts(plane, step=5.0):
    sec = BRepAlgoAPI_Section(s.wrapped, plane)
    sec.Build()
    sh = cq.Shape.cast(sec.Shape())
    pts = [sample_edge(e, step) for e in sh.Edges()]
    return np.concatenate(pts) if pts else np.zeros((0, 3))

for z in (-300.0, -150.0, 150.0, 400.0, 700.0, 900.0):
    p = section_pts(gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)))
    p = p[p[:, 1] > 0]
    out[f"wl_{int(z)}"] = p[np.argsort(p[:, 0])]
    print(f"waterline z={z}: {len(p)} pts, x {p[:,0].min():.0f}-{p[:,0].max():.0f}")
for y in (300.0, 600.0, 900.0):
    p = section_pts(gp_Pln(gp_Pnt(0, y, 0), gp_Dir(0, 1, 0)))
    out[f"bt_{int(y)}"] = p
    print(f"buttock y={y}: {len(p)} pts")
np.savez(os.path.join(HERE, "loft_lines.npz"), **out)
print(f"done {time.time()-t0:.1f}s")
