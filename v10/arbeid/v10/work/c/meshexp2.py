import sys, time, math
import numpy as np
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
import cadquery as cq
from hr26 import deckhouse as D, params as P
from meshexp import ntri
mode = sys.argv[1]
nh = int(sys.argv[2]) if len(sys.argv) > 2 else 36
def hf_solid(xs, plan, base, top, floor, angles, radii, what):
    if mode.startswith("arc"):
        D._resample.__defaults__ = (60.0, 1e9)  # bare lengde
    halves = [D._hf_section(x, plan, base, top, floor, angles, radii, n_half=nh) for x in xs]
    z_bot = min(float(h[:, 1].min()) for h in halves) - 60.0
    fulls = [np.vstack([h[::-1] * [-1.0, 1.0], h[1:]]) for h in halves]
    if mode == "meanchord":
        ps = []
        for f in fulls:
            L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(f, axis=0).T))]); ps.append(L / L[-1])
        par = np.mean(ps, axis=0)
    else:
        par = np.linspace(0, 1, len(fulls[0]))
    wires = []
    for x, f in zip(xs, fulls):
        vs = [cq.Vector(x, float(y), float(z)) for y, z in f]
        top_e = cq.Edge.makeSpline(vs, parameters=list(par))
        a, b = vs[0], vs[-1]
        lb, la = cq.Vector(x, b.y, z_bot), cq.Vector(x, a.y, z_bot)
        wires.append(cq.Wire.assembleEdges([top_e, cq.Edge.makeLine(b, lb), cq.Edge.makeLine(lb, la), cq.Edge.makeLine(la, a)]))
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)])
D._hf_solid = hf_solid
t = time.time(); c = D.coachroof().val(); tb = time.time() - t
print(mode, nh, "build", round(tb, 1), "valid", c.isValid(), "V", round(c.Volume() / 1e9, 4), ntri(c))
