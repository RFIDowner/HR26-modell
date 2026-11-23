"""kk_: karm- og kantmaaler (V10, 13.11.2026). Felles hjelpere.

* model_mesh(): 01_skrog.stl lagt tilbake i modellens ramme (x fra baugen,
  y styrbord +, z over DWL), samme regel som vrender.py. Bufres i out/.
* render(cam, ...): VTK-render med et loest hullkamera (uwlib.Cam-konvensjon:
  Q = (X - C) R^T, u = f Qx/Qz + cx, v = f Qy/Qz + cy). Gir RGB-bilde og
  verdenskoordinater per piksel (fra dybdebufferen), saa et punkt i bildet
  kan oversettes til modellens (x, y, z).

Kjoeres alltid under minnetaket:
  python ../../../../tools/memcap.py --gb 3 -- python kk_xxx.py
"""
import os
import sys

import numpy as np

import common as c

OUT = c.W + "/out"
STL = c.REPO + "/export/stl/01_skrog.stl"
CACHE = os.path.join(os.environ.get("TEMP", OUT), "kk_mesh_cache.npz")   # ikke i repoet


def _to_model(V0, ang_deg):
    a = np.radians(-ang_deg)
    R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    return V0 @ R.T


def model_mesh():
    """(V, F) for 01_skrog.stl i modellens ramme, fullskala mm."""
    st = os.stat(STL)
    key = np.array([st.st_size, int(st.st_mtime)], float)
    if os.path.exists(CACHE):
        d = np.load(CACHE)
        if np.allclose(d["key"], key):
            return d["V"], d["F"]
    import trimesh
    m = trimesh.load(STL)
    V0 = np.asarray(m.vertices, float)
    best = None
    for ang in (45.0, -45.0, 135.0, -135.0):
        V = _to_model(V0, ang)
        ext = V.max(0) - V.min(0)
        if best is None or ext[0] > best[1][0]:
            best = (ang, ext, V)
    V = best[2] * 30.0
    xs = V[:, 0]
    lo, hi = xs.min(), xs.max()

    def width_near(x0):
        sel = np.abs(xs - x0) < 0.05 * (hi - lo)
        return np.ptp(V[sel, 1])

    if width_near(lo + 0.05 * (hi - lo)) > width_near(hi - 0.05 * (hi - lo)):
        V[:, 0] *= -1
        V[:, 1] *= -1
        lo = V[:, 0].min()
    V[:, 0] += 40.0 - lo
    V[:, 2] += -1400.0 - V[:, 2].min()
    V[:, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min())
    F = np.asarray(m.faces, np.int64)
    np.savez(CACHE, V=V, F=F, key=key)
    return V, F


def _poly(V, F):
    import vtk
    from vtk.util import numpy_support as ns
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


def render(cam, V, F, W=None, H=None, scale=1.0, light_dir=None):
    """Render (V, F) med kameraet `cam` (uwlib/geo9374-Cam, hovedpunkt cx, cy;
    fortegning k1/k2 ignoreres). scale > 1 gir et stoerre bilde med samme
    utsnitt. Gir (rgb uint8 H x W x 3, XYZ float H x W x 3, NaN = bakgrunn)."""
    import vtk
    from vtk.util import numpy_support as ns
    W = int(round((W or cam.W) * scale))
    H = int(round((H or cam.H) * scale))
    f = cam.f * scale
    cx, cy = cam.cx * scale, cam.cy * scale
    Rm = np.asarray(cam.R, float)
    C = np.asarray(cam.C, float)
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.55, 0.70, 0.90)
    mp = vtk.vtkPolyDataMapper()
    mp.SetInputData(_poly(V, F))
    a = vtk.vtkActor()
    a.SetMapper(mp)
    a.GetProperty().SetColor(0.93, 0.92, 0.86)
    a.GetProperty().SetSpecular(0.15)
    a.GetProperty().SetAmbient(0.25)
    ren.AddActor(a)
    vc = ren.GetActiveCamera()
    vc.SetPosition(*C)
    vc.SetFocalPoint(*(C + 5000.0 * Rm[2]))
    vc.SetViewUp(*(-Rm[1]))
    vc.SetViewAngle(np.degrees(2.0 * np.arctan(0.5 * H / f)))
    # hovedpunkt utenfor midten: vtk WindowCenter i normaliserte koordinater
    wcx = -(cx - 0.5 * W) / (0.5 * W)
    wcy = (cy - 0.5 * H) / (0.5 * H)
    vc.SetWindowCenter(wcx, wcy)
    vc.SetClippingRange(500.0, 60000.0)
    lk = vtk.vtkLightKit()
    lk.AddLightsToRenderer(ren)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(W, H)
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.ReadFrontBufferOff()
    w2i.Update()
    img = ns.vtk_to_numpy(w2i.GetOutput().GetPointData().GetScalars()).reshape(H, W, -1)[::-1, :, :3].copy()
    zf = vtk.vtkWindowToImageFilter()
    zf.SetInput(rw)
    zf.SetInputBufferTypeToZBuffer()
    zf.ReadFrontBufferOff()
    zf.Update()
    zb = ns.vtk_to_numpy(zf.GetOutput().GetPointData().GetScalars()).reshape(H, W)[::-1, :].astype(float)
    n, fa = vc.GetClippingRange()
    zndc = 2.0 * zb - 1.0
    ze = 2.0 * fa * n / ((fa + n) - zndc * (fa - n))
    uu, vv = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    dirs = np.stack([(uu - cx) / f, (vv - cy) / f, np.ones_like(uu)], -1)
    XYZ = C + ze[..., None] * (dirs @ Rm)
    XYZ[zb >= 0.999999] = np.nan
    return img, XYZ


def font(sz=15):
    from PIL import ImageFont
    try:
        return ImageFont.truetype("arial.ttf", sz)
    except OSError:
        return ImageFont.load_default()


if __name__ == "__main__":
    V, F = model_mesh()
    print(V.shape, F.shape, V.min(0).round(), V.max(0).round())
