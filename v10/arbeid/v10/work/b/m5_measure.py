import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b")
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
from geo import full_tris
from elib import section
sys.path.insert(0, WT)
from hr26 import curves as C
A, B = full_tris(sys.argv[1]), full_tris(sys.argv[2])
def pts(T, axis, c):
    s = section(T, axis, c)
    return s.reshape(-1, 3) if len(s) else np.zeros((0, 3))
print("Akterspeil paa senterlinjen, x ved y=0 (ytre flate):")
for z in (-200, -90, 0, 400, 700, 900):
    r = []
    for T in (A, B):
        sg = section(T, 2, z)
        y0, y1 = sg[:, 0, 1], sg[:, 1, 1]
        m = (y0 * y1 <= 0) & (np.abs(y1 - y0) > 1e-9)
        f = -y0[m] / (y1[m] - y0[m])
        xs = sg[m, 0, 0] + f * (sg[m, 1, 0] - sg[m, 0, 0])
        xs = xs[xs > 7500]
        r.append(xs.max() if len(xs) else float('nan'))
    print(f"  z={z:5d}: foer {r[0]:.1f} etter {r[1]:.1f} diff {r[1]-r[0]:+.1f}")
print("Dekkskant ved hekken (stoerste halvbredde i z = sheer-8, x-vindu 6 mm):")
worst = 0.0
for x in range(7300, 7900, 50):
    z = C.sheer_z(x) - 8.0
    r = []
    for T in (A, B):
        P_ = pts(T, 2, z); m = np.abs(P_[:, 0] - x) < 6
        r.append(P_[m, 1].max() if m.any() else float('nan'))
    worst = max(worst, abs(r[1] - r[0]))
    print(f"  x={x}: foer {r[0]:.1f} etter {r[1]:.1f} diff {r[1]-r[0]:+.1f} (tabell {C.deck_half_breadth(x):.1f})")
print("  stoerste avvik %.1f mm" % worst)
print("Fenderlist (snitt x = konst): utstikk og synlig hoyde")
for x in (600, 1500, 3000, 4500, 6000, 7200):
    zc = C.strake_z(x)
    for nm, T in (("foer", A), ("etter", B)):
        P_ = pts(T, 0, x); P_ = P_[(P_[:, 1] > 0) & (np.abs(P_[:, 2] - zc) < 160)]
        # skrogsiden: lineaer tilpasning av ytterste y mot z utenfor listen
        bins = np.arange(zc - 150, zc + 151, 5.0)
        prof = np.array([[0.5 * (a + b), P_[(P_[:, 2] >= a) & (P_[:, 2] < b), 1].max()] for a, b in zip(bins[:-1], bins[1:]) if ((P_[:, 2] >= a) & (P_[:, 2] < b)).any()])
        side = prof[np.abs(prof[:, 0] - zc) > 90]
        k = np.polyfit(side[:, 0], side[:, 1], 2)
        dev = prof[:, 1] - np.polyval(k, prof[:, 0])
        vis = prof[dev > 1.5]
        i = np.argmax(dev)
        print(f"  x={x} {nm:5s}: utstikk {dev[i]:5.1f} mm ved z={prof[i,0]:.0f} (strake_z {zc:.0f}); synlig hoyde {vis[:,0].max()-vis[:,0].min()+5:.0f} mm")
