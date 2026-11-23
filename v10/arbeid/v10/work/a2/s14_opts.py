"""Hvilket makeSpline-valg gir cusp i sidesplinen?"""
import sys
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
sys.path.insert(0, WT)
import numpy as np
import cadquery as cq
from hr26 import curves as C


def speed(e):
    c = e._geomAdaptor(); a, b = c.FirstParameter(), c.LastParameter()
    ts = np.linspace(a, b, 4001)
    P = np.array([[c.Value(t).X(), c.Value(t).Y(), c.Value(t).Z()] for t in ts])
    sp = np.linalg.norm(np.gradient(P, axis=0), axis=1)
    return round(float(sp.min() / sp.max()), 4), round(float((ts[np.argmin(sp)] - a) / (b - a)), 3)


x = 800.0
sp = C.section_parts(x, 28)
side = sp["side"]; ps = [float(v) for v in sp["side_par"]]; ty, tz = sp["t_side"]
V = [cq.Vector(x, float(y), float(z)) for y, z in side]
Vp = [cq.Vector(x, -float(y), float(z)) for y, z in side[::-1]]
T = lambda a, b: cq.Vector(0.0, a, b)
rev = [1.0 - v for v in reversed(ps)]
print("stb, params+tangents     ", speed(cq.Edge.makeSpline(V, tangents=[T(1, 0), T(ty, tz)], parameters=ps)))
print("stb, params+tangents noscale", speed(cq.Edge.makeSpline(V, tangents=[T(1, 0), T(ty, tz)], parameters=ps, scale=False)))
print("stb, params only         ", speed(cq.Edge.makeSpline(V, parameters=ps)))
print("stb, tangents only       ", speed(cq.Edge.makeSpline(V, tangents=[T(1, 0), T(ty, tz)])))
print("port, params+tangents    ", speed(cq.Edge.makeSpline(Vp, tangents=[T(ty, -tz), T(1, 0)], parameters=rev)))
print("stb, params+tangents scaled by L", speed(cq.Edge.makeSpline(V, tangents=[T(1, 0) * 1183.0, T(ty, tz) * 1183.0], parameters=ps, scale=False)))
