"""Radius i dekkskanten i STL-en: snitt x = konst, sirkeltilpasning rundt hjoernet."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as CM
S = 30.0
path = sys.argv[1]; xb = float(sys.argv[2])
V, F = CM.weld(CM.load_raw(path))
A = V[F[:, 0]]; B = V[F[:, 1]]; Cc = V[F[:, 2]]
for xq in (3200.0, 5000.0, 1500.0):
    xm = (xq - xb) / S
    pts = []
    for P0, P1 in ((A, B), (B, Cc), (Cc, A)):
        c = (P0[:, 0] - xm) * (P1[:, 0] - xm) < 0
        f = (xm - P0[c, 0]) / (P1[c, 0] - P0[c, 0])
        Q = P0[c] + f[:, None] * (P1[c] - P0[c])
        pts.append(Q)
    Q = np.vstack(pts) * S
    y, z = Q[:, 1], Q[:, 2] - 1400.0
    m = y > 0
    y, z = y[m], z[m]
    # ytre hjoerne: punktene med stoerst y + z (oppe-ute), naer dekkskanten
    s = y + 0.35 * z
    top = np.argsort(-s)[:4000]
    yy, zz = y[top], z[top]
    # behold et vindu rundt hjoernet: innen 45 mm fra punktet med maks s
    j = np.argmax(yy + 0.35 * zz)
    w = np.hypot(yy - yy[j], zz - zz[j]) < 30
    Y, Z = yy[w], zz[w]
    Am = np.c_[2 * Y, 2 * Z, np.ones_like(Y)]
    sol, *_ = np.linalg.lstsq(Am, Y ** 2 + Z ** 2, rcond=None)
    yc, zc = sol[0], sol[1]; R = np.sqrt(sol[2] + yc ** 2 + zc ** 2)
    res = np.abs(np.hypot(Y - yc, Z - zc) - R)
    print(f"{os.path.basename(path)} x={xq:.0f}: {w.sum()} punkt rundt hjoernet ({yy[j]:.0f}, {zz[j]:.0f}); sirkel R = {R:.1f} mm (rest maks {res.max():.2f} mm), ytterste y {y.max():.1f}")
