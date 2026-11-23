"""Sidesplinen alene ved stasjonene i baugen: fart langs parameteren."""
import sys
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
sys.path.insert(0, WT)
import numpy as np
import cadquery as cq
from hr26 import curves as C, hull as H
for x in (51.5, 115.6, 205.0, 400.0, 800.0, 1500.0, 3000.0):
    w = H._section_wire(x, 26)
    es = w.Edges()
    for k in (0, 4):
        e = es[k] if k < len(es) else None
        c = e._geomAdaptor()
        a, b = c.FirstParameter(), c.LastParameter()
        ts = np.linspace(a, b, 2001)
        P = np.array([[c.Value(t).X(), c.Value(t).Y(), c.Value(t).Z()] for t in ts])
        sp = np.linalg.norm(np.gradient(P, axis=0), axis=1)
        j = int(np.argmin(sp))
        print(f"x={x:7.1f} kant {k}: L={e.Length():7.1f}  fart min/max {sp.min()/sp.max():.4f} ved t={(ts[j]-a)/(b-a):.3f}  ende y,z ({P[-1,1]:.1f},{P[-1,2]:.1f}) start ({P[0,1]:.1f},{P[0,2]:.1f})")
    sp_ = C.section_parts(x, 28)
    print("    t_side", np.round(sp_["t_side"], 3), " siste sidepunkter", np.round(sp_["side"][-3:], 1).tolist())
