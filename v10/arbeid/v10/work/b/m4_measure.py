"""Maal foer/etter i fullskala. argv: before.stl after.stl"""
import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b")
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
from geo import full_tris
from elib import section, chain
sys.path.insert(0, WT)
from hr26 import curves as C, params as P
A, B = full_tris(sys.argv[1]), full_tris(sys.argv[2])
for nm, T in (("foer", A), ("etter", B)):
    V = T.reshape(-1, 3); lo, hi = V.min(0), V.max(0)
    print(f"{nm}: LOA {hi[0]-lo[0]+4:.1f} (x {lo[0]:.1f}..{hi[0]:.1f})  bredde {hi[1]-lo[1]:.1f}  dypgang (kjol til DWL) {-lo[2]:.1f}")

def outline(T, z):
    segs = section(T, 2, z)
    L = chain(segs, tol=1e-4)
    P_ = np.vstack([l for l in L])
    return P_

def max_y_at(T, z, xs):
    P_ = outline(T, z)
    out = []
    for x in xs:
        m = np.abs(P_[:, 0] - x) < 6
        out.append(P_[m, 1].max() if m.any() else np.nan)
    return np.array(out)

print("\nTransom paa senterlinjen (x ved y~0):")
for z in (-200, -90, 0, 400, 804, 900):
    r = []
    for T in (A, B):
        P_ = outline(T, z); m = np.abs(P_[:, 1]) < 3
        r.append(P_[m, 0].max())
    print(f"  z={z:5d}: foer {r[0]:.1f}  etter {r[1]:.1f}  diff {r[1]-r[0]:+.1f}")

print("\nDekkskant ved hekken (maks halvbredde like under dekkskanten, z = sheer-8):")
xs = np.arange(7300, 7900, 50)
worst = 0
for x in xs:
    z = C.sheer_z(x) - 8
    a, b = max_y_at(A, z, [x])[0], max_y_at(B, z, [x])[0]
    worst = max(worst, abs(b - a))
    print(f"  x={x}: foer {a:.1f} etter {b:.1f} diff {b-a:+.1f}  (deck_half_breadth {C.deck_half_breadth(x):.1f})")
print("  stoerste avvik", round(worst, 1))

print("\nFenderlist: utstikk og hoyde (snitt x = konst, ytterste punkt naer strake_z):")
for x in (1000, 2500, 4000, 5500, 7000):
    zc = C.strake_z(x)
    for nm, T in (("foer", A), ("etter", B)):
        segs = section(T, 0, x)
        P_ = np.vstack(chain(segs, tol=1e-4))
        m = (P_[:, 1] > 0) & (np.abs(P_[:, 2] - zc) < 80)
        Q = P_[m]
        i = np.argmax(Q[:, 1])
        # skrogsiden rett over/under listen
        side = (P_[:, 1] > 0) & (np.abs(P_[:, 2] - zc) > 70) & (np.abs(P_[:, 2] - zc) < 120)
        ys = P_[side]
        yb = np.interp(Q[i, 2], ys[np.argsort(ys[:, 2])][:, 2], ys[np.argsort(ys[:, 2])][:, 1])
        band = Q[Q[:, 1] > yb + 2.0]
        print(f"  x={x} {nm}: ytterst y={Q[i,1]:.1f} ved z={Q[i,2]:.1f} (strake_z {zc:.1f}); utstikk ca {Q[i,1]-yb:.1f}; synlig hoyde ca {band[:,2].max()-band[:,2].min():.1f}")
