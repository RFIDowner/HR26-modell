"""Render av export/stl/01_skrog.stl (+ 16_ruff-tak.stl) med et loest
fotokamera (uwlib/geo9374-kamera: C, R, f, cx, cy), VTK offscreen, i
bildets pikselstoerrelse. Plasseringen av STL-en i modellrammen er som i
vrender.py (dreid 45 grader paa platen, skala 30, baugen x 40, kjolbunn -1400).

  python ../../../../tools/memcap.py --gb 3 -- python kd_render.py n4|n6 ut.png
"""
import json
import sys

import numpy as np
import trimesh
import vtk
from vtk.util import numpy_support as ns

import common as c


def _rot(V, ang_deg):
    a = np.radians(-ang_deg)
    R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    return V @ R.T


def load_parts():
    m = trimesh.load(c.REPO + "/export/stl/01_skrog.stl")
    best = None
    for ang in (45.0, -45.0, 135.0, -135.0):
        V = _rot(m.vertices, ang)
        ext = V.max(0) - V.min(0)
        if best is None or ext[0] > best[1][0]:
            best = (ang, ext)
    ang = best[0]
    V = _rot(m.vertices, ang) * 30.0
    xs = V[:, 0]
    lo, hi = xs.min(), xs.max()

    def width_near(x0):
        sel = np.abs(xs - x0) < 0.05 * (hi - lo)
        return np.ptp(V[sel, 1])
    flip = width_near(lo + 0.05 * (hi - lo)) > width_near(hi - 0.05 * (hi - lo))
    if flip:
        V[:, 0] *= -1
        V[:, 1] *= -1
    sx = 40.0 - V[:, 0].min()
    sz = -1400.0 - V[:, 2].min()
    sy = -0.5 * (V[:, 1].max() + V[:, 1].min())
    V = V + [sx, sy, sz]
    parts = [(V, m.faces)]
    try:
        r = trimesh.load(c.REPO + "/export/stl/16_ruff-tak.stl")
        # lokket ligger for seg paa platen: plasser det ved aa matche ruffens
        # aapning er usikkert, saa det tas bare med om det allerede ligger riktig
    except Exception:
        r = None
    return parts


def poly(V, F):
    pts = vtk.vtkPoints()
    pts.SetData(ns.numpy_to_vtk(np.ascontiguousarray(V), deep=True))
    cells = vtk.vtkCellArray()
    Fa = np.c_[np.full(len(F), 3), F].astype(np.int64).ravel()
    cells.SetCells(len(F), ns.numpy_to_vtkIdTypeArray(Fa, deep=True))
    p = vtk.vtkPolyData()
    p.SetPoints(pts)
    p.SetPolys(cells)
    nm = vtk.vtkPolyDataNormals()
    nm.SetInputData(p)
    nm.SetFeatureAngle(35)
    nm.Update()
    return nm.GetOutput()


def render(cam, W, H, out):
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.75, 0.85, 0.95)
    for V, F in load_parts():
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(poly(V, F))
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetColor(0.93, 0.93, 0.9)
        a.GetProperty().SetSpecular(0.2)
        ren.AddActor(a)
    vc = ren.GetActiveCamera()
    Cc = np.asarray(cam.C, float)
    R = np.asarray(cam.R, float)
    vc.SetPosition(*Cc)
    vc.SetFocalPoint(*(Cc + 1000.0 * R[2]))
    vc.SetViewUp(*(-R[1]))
    f = cam.f * getattr(cam, "asp", 1.0)
    vc.SetViewAngle(np.degrees(2.0 * np.arctan(0.5 * H / f)))
    # hovedpunkt: VTK WindowCenter i normaliserte koordinater
    wx = -(cam.cx - 0.5 * W) / (0.5 * W)
    wy = (cam.cy - 0.5 * H) / (0.5 * H)
    vc.SetWindowCenter(wx, wy)
    ren.ResetCameraClippingRange()
    lk = vtk.vtkLightKit()
    lk.AddLightsToRenderer(ren)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(W, H)
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(out)
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()
    print("ok", out)


def cam_named(name):
    import geo9374 as G
    if name == "n4":
        J = json.load(open(c.W + "/out/n4_fprof.json"))
        q = np.asarray(J["out"]["pin_Nc_f850"]["q"], float)
        return G.Cam9374(q[:7], 1170, 831), 1170, 831
    if name == "n6":
        import n6_geo as N
        J = json.load(open(c.W + "/out/n6_cam.json"))
        d = J["modes"][J["main"]]
        q = np.asarray(d["q"], float)
        return N.Cam(q[:7], J["W"], J["H"]), J["W"], J["H"]
    if name == "9387":
        J = json.load(open(c.W + "/out/cam9387.json"))
        q = np.asarray(J["modes"]["fri"]["q"], float)
        return G.Cam9374(q[:7], 2000, 1500), 2000, 1500
    if name == "9374":
        cam, d = G.load_cam()
        return cam, 761, 472
    raise KeyError(name)


if __name__ == "__main__":
    cam, W, H = cam_named(sys.argv[1])
    render(cam, W, H, sys.argv[2])
