"""Mesher hver flate i den bare loften for seg (absolutt toleranse) og teller
degenererte trekanter: hvilken flate lager dem?"""
import sys
import numpy as np
import cadquery as cq
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
s = cq.Shape.importBrep(sys.argv[1])
sc = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0 / 30.0
s = s.scale(sc)
BRepMesh_IncrementalMesh(s.wrapped, 0.01, False, 0.05, True)
for i, f in enumerate(s.Faces()):
    loc = TopLoc_Location()
    tri = BRep_Tool.Triangulation_s(f.wrapped, loc)
    if tri is None:
        print(i, f.geomType(), "ingen triangulering"); continue
    P = np.array([[tri.Node(j + 1).X(), tri.Node(j + 1).Y(), tri.Node(j + 1).Z()] for j in range(tri.NbNodes())])
    T = np.array([[tri.Triangle(j + 1).Value(k) - 1 for k in (1, 2, 3)] for j in range(tri.NbTriangles())])
    A = 0.5 * np.linalg.norm(np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]), axis=1)
    bad = A < 1e-10
    bb = f.BoundingBox()
    msg = ""
    if bad.any():
        c = P[T[bad]].mean(1) * 30.0
        msg = f"  degenerte ved x {c[:,0].min():.0f}..{c[:,0].max():.0f}, median x {np.median(c[:,0]):.0f}"
    print(f"{i} {f.geomType():8s} areal {f.Area()*900/1e6:7.3f} m2  noder {len(P):7d} trekanter {len(T):7d} degenererte {int(bad.sum()):6d}{msg}")
