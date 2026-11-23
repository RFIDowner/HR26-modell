"""Tangentene i _section_wire skaleres selv (scale=False): OCCs egen skalering
ga cusp i styrbord sidespline."""
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
fn = WT + "/hr26/hull.py"
src = open(fn, "rb").read().decode("utf-8").replace("\r\n", "\n")
old = '''    def pts(arr, sgn=1.0):
        return [cq.Vector(x, sgn * float(y), float(z)) for y, z in arr]

    def tan(vy, vz):
        return cq.Vector(0.0, vy, vz)

    def rev(par):
        return [1.0 - v for v in reversed(par)]

    edges = [
        cq.Edge.makeSpline(pts(side), tangents=[tan(1.0, 0.0), tan(ty, tz)], parameters=ps),
        cq.Edge.makeSpline(pts(corner), tangents=[tan(ty, tz), tan(dy, dz)], parameters=pc),
        cq.Edge.makeSpline(pts(deck), tangents=[tan(dy, dz), tan(dy, -dz)], parameters=pd),
        cq.Edge.makeSpline(pts(corner[::-1], -1.0), tangents=[tan(dy, -dz), tan(ty, -tz)],
                           parameters=rev(pc)),
        cq.Edge.makeSpline(pts(side[::-1], -1.0), tangents=[tan(ty, -tz), tan(1.0, 0.0)],
                           parameters=rev(ps)),
    ]
    return cq.Wire.assembleEdges(edges)
'''
new = '''    def spline(arr, par, t0, t1, sgn=1.0):
        # Parameterne er andeler av buelengden, saa farten langs kurven er
        # kurvens lengde: tangentene skaleres til den selv (scale=False).
        # OCCs egen skalering (scale=True) ga en cusp i styrbord sidespline.
        arr = np.asarray(arr, dtype=float)
        n = float(np.hypot(np.diff(arr[:, 0]), np.diff(arr[:, 1])).sum())
        v = [cq.Vector(x, sgn * float(y), float(z)) for y, z in arr]
        tg = [cq.Vector(0.0, t[0] * n, t[1] * n) for t in (t0, t1)]
        return cq.Edge.makeSpline(v, tangents=tg, parameters=list(par), scale=False)

    def rev(par):
        return [1.0 - v for v in reversed(par)]

    edges = [
        spline(side, ps, (1.0, 0.0), (ty, tz)),
        spline(corner, pc, (ty, tz), (dy, dz)),
        spline(deck, pd, (dy, dz), (dy, -dz)),
        spline(corner[::-1], rev(pc), (dy, -dz), (ty, -tz), -1.0),
        spline(side[::-1], rev(ps), (ty, -tz), (1.0, 0.0), -1.0),
    ]
    return cq.Wire.assembleEdges(edges)
'''
assert old in src
src = src.replace(old, new, 1)
open(fn, "wb").write(src.replace("\n", "\r\n").encode("utf-8"))
print("ok")
