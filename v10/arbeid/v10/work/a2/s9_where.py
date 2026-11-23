"""Hvor paa hjoernebaandet og siden legger mesheren trekantene? (x-histogram)"""
import sys
import numpy as np
import cadquery as cq
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
s = cq.Shape.importBrep(sys.argv[1]).scale(1.0 / 30.0)
BRepMesh_IncrementalMesh(s.wrapped, 0.01, False, 0.05, True)
for i, f in enumerate(s.Faces()):
    tri = BRep_Tool.Triangulation_s(f.wrapped, TopLoc_Location())
    if tri is None or tri.NbTriangles() < 50000:
        continue
    P = np.array([[tri.Node(j + 1).X() * 30, tri.Node(j + 1).Y() * 30, tri.Node(j + 1).Z() * 30] for j in range(tri.NbNodes())])
    UV = np.array([[tri.UVNode(j + 1).X(), tri.UVNode(j + 1).Y()] for j in range(tri.NbNodes())])
    H, e = np.histogram(P[:, 0], bins=[0, 20, 60, 120, 250, 500, 1000, 2000, 4000, 6000, 7000, 7600, 7800, 7900, 8000])
    print(i, f.geomType(), tri.NbTriangles(), "noder per x-intervall:", {f"{int(a)}-{int(b)}": int(h) for a, b, h in zip(e[:-1], e[1:], H)})
    Hu, eu = np.histogram(UV[:, 0], bins=10)
    print("   u-fordeling:", Hu.tolist(), " u", round(UV[:, 0].min(), 3), round(UV[:, 0].max(), 3))
