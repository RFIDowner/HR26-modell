import sys, numpy as np, math
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b")
from geo import *
path = sys.argv[1]
T = full_tris(path)
print("bbox full:", T.reshape(-1,3).min(0).round(1), T.reshape(-1,3).max(0).round(1))
for z in (-200, -100, 0, 200, 400, 600, 700, 804, 900):
    L = outer_lines(T, 2, z)
    # take the polyline with the largest x extent (outer hull)
    best = None
    for P in L:
        if P[:, 0].max() > 7600 and (best is None or len(P) > len(best)):
            best = P
    if best is None:
        print(z, "none"); continue
    P = best[(best[:, 0] > 7300) & (best[:, 1] > 0)]
    if len(P) < 3:
        print(z, "few"); continue
    o = np.argsort(-P[:, 1]) if False else None
    # order along the curve: by angle around a point inboard-forward
    c = np.array([7300.0, 0.0])
    ang = np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0])
    P = P[np.argsort(-ang)]
    d = np.diff(P[:, :2], axis=0); l = np.hypot(d[:, 0], d[:, 1]); k = l > 0.05
    P2 = np.vstack([P[:1, :2], P[1:, :2][k]])
    d = np.diff(P2, axis=0); a = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    kink = (np.diff(a) + 180) % 360 - 180
    i = np.argmax(np.abs(kink))
    # total turn within +-60 mm of max kink
    s = np.r_[0, np.cumsum(np.hypot(d[:, 0], d[:, 1]))]
    sm = s[1:-1]
    w = np.abs(sm - sm[i]) < 60
    print(f"z={z:5d}: max kink {kink[i]:6.1f} deg at ({P2[i+1,0]:.0f},{P2[i+1,1]:.0f}); turn within +-60mm {kink[w].sum():6.1f}; "
          f"transom at y=0 x={P2[:,0].max():.0f}; side y at x=7700 {np.interp(7700, P2[::-1,0], P2[::-1,1]) if P2[0,0]>P2[-1,0] else float('nan'):.0f}")
