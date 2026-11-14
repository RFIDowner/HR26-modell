"""Trinn 9 «magen»: bilder av forslag foer/etter (ingen CAD).

Skroget fra kurvene (uwlib.hull_mesh) og kjolen (n1_geo.keel_mesh) rendres
med VTK fra faste vinkler: som brukerens skjermbilder (mage3: skraatt ovenfra
akterfra; blaa: fra babord ovenfra), nedenfra fra siden, akterfra nedenfra
(som «nye 1») og forfra nedenfra (som IMG_9395). Vannlinjer (svart, z 0 til
-400 hver 100 mm) og spant (graa, hver 500 mm) tegnes paa skroget.
Pluss et spantriss x 3 200-7 400: foer (blaa) og etter (roed).

  python ../../../../tools/memcap.py --gb 3 -- python mage_vis.py UTMAPPE [forslag.json ...]
"""
import json
import os
import sys
import types

if "cadquery" not in sys.modules:
    sys.modules["cadquery"] = types.ModuleType("cadquery")

import numpy as np
import vtk
from vtk.util import numpy_support as ns
from PIL import Image, ImageDraw, ImageFont

import common as c
import uwlib as U
import n1_geo as N
import opt_mage as M

VIEWS = {     # (kamera, siktepunkt, synsvinkel i grader)
    "mage3": ((11800.0, -7600.0, 4300.0), (3900.0, 0.0, -250.0), 34.0),
    "blaa": ((3000.0, -8200.0, 6200.0), (4100.0, 0.0, -250.0), 36.0),
    "side_lavt": ((4300.0, -9800.0, -1500.0), (4300.0, 0.0, -150.0), 34.0),
    "akter_under": ((13000.0, -900.0, -2600.0), (5000.0, 0.0, -100.0), 40.0),
    "forfra_under": ((-1800.0, -3600.0, -2300.0), (4300.0, 0.0, -300.0), 42.0),
}


def font(sz):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", sz)
    except OSError:
        return ImageFont.load_default()


def poly(V, F):
    pts = vtk.vtkPoints()
    pts.SetData(ns.numpy_to_vtk(np.ascontiguousarray(V, dtype=float), deep=True))
    cells = vtk.vtkCellArray()
    Fa = np.c_[np.full(len(F), 3), F].astype(np.int64).ravel()
    cells.SetCells(len(F), ns.numpy_to_vtkIdTypeArray(Fa, deep=True))
    p = vtk.vtkPolyData()
    p.SetPoints(pts)
    p.SetPolys(cells)
    nm = vtk.vtkPolyDataNormals()
    nm.SetInputData(p)
    nm.SetFeatureAngle(60)
    nm.SplittingOff()
    nm.Update()
    return nm.GetOutput()


def cut_actor(pd, normal, values, color, width):
    cut = vtk.vtkCutter()
    pl = vtk.vtkPlane()
    pl.SetNormal(*normal)
    pl.SetOrigin(0.0, 0.0, 0.0)
    cut.SetCutFunction(pl)
    cut.SetInputData(pd)
    for i, v in enumerate(values):
        cut.SetValue(i, v)
    cut.Update()
    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(cut.GetOutputPort())
    m.ScalarVisibilityOff()
    a = vtk.vtkActor()
    a.SetMapper(m)
    a.GetProperty().SetColor(*color)
    a.GetProperty().SetLineWidth(width)
    a.GetProperty().LightingOff()
    return a


def render(V, F, VK, FK, view, W=900, H=640):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1.0, 1.0, 1.0)
    pd = poly(V, F)
    actors = [(pd, (0.86, 0.80, 0.70))]
    if len(FK):
        actors.append((poly(VK, FK), (0.80, 0.74, 0.64)))
    for pdx, col in actors:
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(pdx)
        m.ScalarVisibilityOff()
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetColor(*col)
        a.GetProperty().SetAmbient(0.22)
        a.GetProperty().SetDiffuse(0.78)
        a.GetProperty().SetSpecular(0.18)
        a.GetProperty().SetSpecularPower(25)
        a.GetProperty().SetInterpolationToPhong()
        ren.AddActor(a)
    ren.AddActor(cut_actor(pd, (0, 0, 1), [0.0, -100.0, -200.0, -300.0, -400.0], (0.05, 0.05, 0.05), 1.6))
    ren.AddActor(cut_actor(pd, (1, 0, 0), list(np.arange(1000.0, 7600.0, 500.0)), (0.45, 0.45, 0.45), 1.0))
    pos, foc, ang = VIEWS[view]
    vc = ren.GetActiveCamera()
    vc.SetPosition(*pos)
    vc.SetFocalPoint(*foc)
    vc.SetViewUp(0.0, 0.0, 1.0)
    vc.SetViewAngle(ang)
    ren.ResetCameraClippingRange()
    hl = vtk.vtkLight()
    hl.SetLightTypeToHeadlight()
    hl.SetIntensity(0.75)
    ren.AddLight(hl)
    top = vtk.vtkLight()
    top.SetLightTypeToSceneLight()
    top.SetPosition(3000.0, -2000.0, 20000.0)
    top.SetFocalPoint(4000.0, 0.0, 0.0)
    top.SetIntensity(0.35)
    ren.AddLight(top)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(W, H)
    rw.SetMultiSamples(4)
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    img = w2i.GetOutput()
    arr = ns.vtk_to_numpy(img.GetPointData().GetScalars()).reshape(H, W, -1)[::-1, :, :3]
    return Image.fromarray(np.ascontiguousarray(arr))


def body_plan(p_list, labels, colors, W=1400, H=880):
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    sc = 0.50
    cx, cz = W // 2, int(60 + 1050 * sc)
    f = font(18)
    xs = np.array([3600.0, 4000.0, 4400.0, 4800.0, 5200.0, 5600.0, 6000.0, 6400.0, 6800.0, 7200.0])
    for z in (-400.0, -300.0, -200.0, -100.0, 0.0, 300.0, 600.0, 900.0):
        y = cz - z * sc
        d.line([(30, y), (W - 30, y)], fill=(225, 225, 225))
        d.text((W - 80, y - 20), "%+.0f" % z, fill=(150, 150, 150), font=f)
    d.line([(cx, 40), (cx, H - 40)], fill=(200, 200, 200))
    for p, col in zip(p_list, colors):
        M.install(p)
        for x in xs:
            s = np.array(c.C.section(float(x), 120))
            side = 1.0 if x >= 5400.0 else -1.0       # akter paa hoeyre side, forut paa venstre
            pts = [(cx + side * y * sc, cz - z * sc) for y, z in s]
            d.line(pts, fill=col, width=2)
    for i, (lab, col) in enumerate(zip(labels, colors)):
        d.text((30, 20 + 26 * i), lab, fill=col, font=font(22))
    d.text((30, H - 34), "spantriss hver 400 mm: venstre x 3 600 (ytterst) til 5 200, hoeyre x 5 600 (ytterst) til 7 200", fill=(90, 90, 90), font=f)
    return im


def wl_plan(p_list, labels, colors, W=1400, H=760):
    """Halvbreddeplan: vannlinjer under vann (z 0 ... -380) fra x 3 000 til 7 600."""
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    x0, x1 = 3000.0, 7600.0
    sx = (W - 120) / (x1 - x0)
    sy = 0.62
    base = H - 50

    def P(x, y):
        return (60 + (x - x0) * sx, base - y * sy)
    for xg in np.arange(3000.0, 7601.0, 500.0):
        d.line([P(xg, 0), P(xg, 1050)], fill=(230, 230, 230))
        d.text(P(xg - 60, -10), "%.0f" % xg, fill=(120, 120, 120), font=font(14))
    for xv, lab in ((3578.0, "vinduets forkant"), (6996.0, "ca. 7 m")):
        d.line([P(xv, 0), P(xv, 1050)], fill=(170, 170, 170), width=2)
        d.text(P(xv + 20, 1040), lab, fill=(120, 120, 120), font=font(14))
    xs = np.arange(x0, x1 + 1, 25.0)
    for p, col in zip(p_list, colors):
        M.install(p)
        for z in (0.0, -100.0, -200.0, -300.0, -380.0):
            pts = []
            for x in xs:
                g = c.C._section_geom(float(x))
                q = g["pts"]
                zz = np.maximum.accumulate(q[:, 1])
                if z > q[0, 1] + 1.0 and x < U.transom_x(z, 0.0):
                    pts.append(P(x, float(np.interp(z, zz, q[:, 0]))))
                elif pts:
                    break
            if len(pts) > 1:
                d.line(pts, fill=col, width=2)
    M.install(p_list[0])
    for z in (0.0, -100.0, -200.0, -300.0, -380.0):
        q = c.C._section_geom(3100.0)["pts"]
        zz = np.maximum.accumulate(q[:, 1])
        d.text(P(3005.0, float(np.interp(z, zz, q[:, 0])) + 25), "z %+.0f" % z, fill=(60, 60, 60), font=font(14))
    for i, (lab, col) in enumerate(zip(labels, colors)):
        d.text((70, 14 + 26 * i), lab, fill=col, font=font(22))
    d.text((W - 560, 14), "vannlinjer under vann, halvbredde (mm), sett ovenfra", fill=(90, 90, 90), font=font(16))
    return im


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    k = len(M.KNOTS)
    props = [("foer trinn 9", np.zeros(3 * k))]
    for a in sys.argv[2:]:
        dd = json.load(open(a if os.path.exists(a) else c.W + "/out/" + a))
        props.append((os.path.basename(a).replace(".json", ""), np.r_[dd["deadrise"], dd["n"], dd["flare"]]))
    VK, FK = N.keel_mesh()
    for view in VIEWS:
        tiles = []
        for lab, p in props:
            M.install(p)
            V, F = U.hull_mesh(260, 72)
            im = render(V, F, VK, FK, view)
            ImageDraw.Draw(im).text((14, 10), lab, fill=(0, 0, 0), font=font(26))
            tiles.append(im)
        Wt = sum(t.width for t in tiles)
        sheet = Image.new("RGB", (Wt, tiles[0].height), (255, 255, 255))
        x0 = 0
        for t in tiles:
            sheet.paste(t, (x0, 0))
            x0 += t.width
        sheet.save(os.path.join(out, "vis_%s.png" % view))
        print("skrev", os.path.join(out, "vis_%s.png" % view))
    cols = [(0, 90, 220), (220, 0, 60), (0, 150, 60), (200, 120, 0)]
    bp = body_plan([p for _, p in props], [lab for lab, _ in props], cols[:len(props)])
    bp.save(os.path.join(out, "spantriss.png"))
    print("skrev", os.path.join(out, "spantriss.png"))
    wl = wl_plan([p for _, p in props], [lab for lab, _ in props], cols[:len(props)])
    wl.save(os.path.join(out, "vannlinjer.png"))
    print("skrev", os.path.join(out, "vannlinjer.png"))


if __name__ == "__main__":
    main()
