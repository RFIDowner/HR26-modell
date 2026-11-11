"""Veggtykkelse ved den avrundede dekkskanten i det uthulte skroget (STL-snitt)."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
import common as CM
sys.path.insert(0, WT)
from hr26 import curves as C
S = 30.0
V, F = CM.weld(CM.load_raw(sys.argv[1]))
xb = 4.0
A = V[F[:, 0]]; B = V[F[:, 1]]; Cc = V[F[:, 2]]
for xq in (3200.0, 5000.0):
    xm = (xq - xb) / S
    segs = []
    for P0, P1 in ((A, B), (B, Cc), (Cc, A)):
        c = (P0[:, 0] - xm) * (P1[:, 0] - xm) < 0
        f = (xm - P0[c, 0]) / (P1[c, 0] - P0[c, 0])
        segs.append(P0[c] + f[:, None] * (P1[c] - P0[c]))
    Q = np.vstack(segs) * S
    y, z = Q[:, 1], Q[:, 2] - 1400.0
    sp = C.section_parts(xq, 200, 60, 81)
    outer = np.vstack([sp["side"], sp["corner"], sp["deck"][: len(sp["deck"]) // 2 + 1]])
    # tett ytre kurve
    d = np.array([np.min(np.hypot(outer[:, 0] - a, outer[:, 1] - b)) for a, b in zip(y, z)])
    hb = C.deck_half_breadth(xq); zs = C.sheer_z(xq)
    reg = (y > hb - 250) & (y > 0) & (z > zs - 250)
    # inne i skrogets ytre snitt (lukket polygon: side, hjoerne, dekk, senterlinje)
    poly = np.vstack([[0.0, outer[0, 1]], outer, [0.0, outer[-1, 1]]])
    def inside(py, pz):
        n = len(poly); c = np.zeros(len(py), bool)
        for i in range(n):
            y1, z1 = poly[i]; y2, z2 = poly[(i + 1) % n]
            m = ((z1 > pz) != (z2 > pz))
            xi = (y2 - y1) * (pz - z1) / np.where(z2 != z1, z2 - z1, 1e-12) + y1
            c ^= m & (py < xi)
        return c
    inner = reg & (d > 3.0) & inside(y, z)
    w = inner & (d < 45.0)
    o = np.argsort(d[w])[:12]
    print("   naermeste innvendige punkter (y-hb, z-zs, d):", [(round(a - hb), round(b - zs), round(c, 1)) for a, b, c in zip(y[w][o], z[w][o], d[w][o])])
    print("   antall innvendige punkter med d < 45:", int(w.sum()), " d-fordeling:", np.histogram(d[inner], bins=[3, 10, 20, 30, 40, 45, 50, 60, 100, 1000])[0].tolist())
    print(f"x={xq:.0f}: punkter i hjoernet {reg.sum()}, paa ytterskallet {int((reg & (d < 1.0)).sum())}, "
          f"minste avstand innvendig flate -> ytterflate {d[inner].min():.1f} mm (HULL_WALL 45)")
