import numpy as np
import common as c
import geo9374 as G
G.use_model(None)
import n4_ovl as O
cam, d = O.load("fprof:pin_Nc_f850")
print(cam.W, cam.H, cam.cx, cam.cy, cam.f, type(cam))
P, C = c.P, c.C
for x in (2000, 4000, 6000, 7500):
    X = np.array([[x, -G.side_y(x, C.strake_z(x)), C.strake_z(x)], [x, -C.deck_half_breadth(x), C.sheer_z(x)]])
    u, v, z = cam.project(X)
    print(x, np.round(u, 1), np.round(v, 1))
import vtk
Rm = np.asarray(cam.R); C0 = np.asarray(cam.C)
print("R", np.round(Rm, 3))
ren = vtk.vtkRenderer(); rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren); rw.SetSize(1170, 831)
vc = ren.GetActiveCamera()
vc.SetPosition(*C0); vc.SetFocalPoint(*(C0 + 5000 * Rm[2])); vc.SetViewUp(*(-Rm[1]))
vc.SetViewAngle(np.degrees(2 * np.arctan(0.5 * 831 / cam.f))); vc.SetClippingRange(500, 60000)
rw.Render()
print("vtk pos", vc.GetPosition(), "fp", vc.GetFocalPoint(), "up", vc.GetViewUp(), "ang", vc.GetViewAngle())
co = vtk.vtkCoordinate(); co.SetCoordinateSystemToWorld()
x = 4000; X = [x, -G.side_y(x, C.strake_z(x)), C.strake_z(x)]
co.SetValue(*X); dpy = co.GetComputedDoubleDisplayValue(ren); print("vtk display", dpy, "-> v", 831 - dpy[1])
