"""Maaler grensesnitt og dekksdetaljer paa BREP (fullskala) og paa STL-er.

python measure.py build2.brep build2.stl baseline_fine.stl
"""
import sys, math
import numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/c")
import cadquery as cq
from common import load_raw

brep, stl_new, stl_old = sys.argv[1], sys.argv[2], sys.argv[3]


def section_pts(shape, origin, normal, n_per_edge=60):
    pl = cq.Face.makePlane(20000, 20000, basePnt=origin, dir=normal)
    sec = shape.intersect(pl) if False else None
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
    s = BRepAlgoAPI_Section(shape.wrapped, gp_Pln(gp_Pnt(*origin), gp_Dir(*normal)))
    s.Build()
    out = cq.Shape.cast(s.Shape())
    pts = []
    for e in out.Edges():
        for t in np.linspace(0, 1, n_per_edge):
            p = e.positionAt(t)
            pts.append((p.x, p.y, p.z))
    return np.array(pts)


S = cq.Shape.importBrep(brep)
print("BREP: gyldig", S.isValid(), "solider", len(S.Solids()))

# mastehullet: snitt like under taket ved masten
z = 1378.3 - 100.0
P = section_pts(S, (0, 0, z), (0, 0, 1))
m = (np.abs(P[:, 0] - 3400) < 200) & (np.abs(P[:, 1]) < 150)
Q = P[m]
print(f"mastehull ved z={z:.0f}: x {Q[:,0].min():.1f}..{Q[:,0].max():.1f}  y {Q[:,1].min():.1f}..{Q[:,1].max():.1f}"
      f"  senter ({0.5*(Q[:,0].min()+Q[:,0].max()):.1f}, {0.5*(Q[:,1].min()+Q[:,1].max()):.1f})")

# rekkepaaler: hull i dekket ved STANCHION_X (snitt 60 mm under dekket)
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
from hr26 import params as Pm, curves as C
for x in Pm.STANCHION_X[:2] + Pm.PULPIT_X[:1]:
    y = C.deck_half_breadth(x) - Pm.STANCHION_INSET if x not in Pm.PULPIT_X else max(C.deck_half_breadth(x) - Pm.STANCHION_INSET, 60.0)
    zz = C.deck_z(x, y) - 60.0
    P = section_pts(S, (0, 0, zz), (0, 0, 1))
    m = (np.hypot(P[:, 0] - x, P[:, 1] - y) < 40)
    Q = P[m]
    if len(Q):
        print(f"hull x={x:.0f}: senter ({Q[:,0].mean():.1f}, {Q[:,1].mean():.1f}) forventet ({x:.0f}, {y:.1f}), diameter {Q[:,0].max()-Q[:,0].min():.1f}")


def stl_full(path):
    T = load_raw(path).astype(np.float64) * 30.0
    T[:, :, 0] += 4.0
    T[:, :, 2] -= 1400.0
    return T


for tag, path in (("NY", stl_new), ("FOER", stl_old)):
    T = stl_full(path)
    V = T.reshape(-1, 3)
    bb0, bb1 = V.min(0), V.max(0)
    print(f"{tag}: bbox x {bb0[0]:.0f}..{bb1[0]:.0f} (LOA {bb1[0]-bb0[0]:.0f})  bredde {bb1[1]-bb0[1]:.0f}  hoyde {bb1[2]-bb0[2]:.0f}")
    # noe foran stevnen under dekk? minste x for z i 780..1190, |y| < 120
    for z0, z1 in ((780, 960), (960, 1190), (1190, 1300)):
        m = (V[:, 2] > z0) & (V[:, 2] < z1) & (np.abs(V[:, 1]) < 120)
        print(f"   minste x for z {z0}-{z1}: {V[m, 0].min():.0f}")
    # hoyeste punkt per omraade
    for name, (xa, xb, ya) in {"stevnbeslag x<500": (0, 500, 200), "klamp 7500": (7350, 7650, 1100),
                              "vinsj 6540": (6450, 6650, 1100), "vinsj 5900": (5800, 6000, 1100)}.items():
        m = (V[:, 0] > xa) & (V[:, 0] < xb) & (np.abs(V[:, 1]) < ya)
        print(f"   {name}: topp z {V[m, 2].max():.0f}")
