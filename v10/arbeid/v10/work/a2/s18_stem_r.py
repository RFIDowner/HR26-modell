"""Stevnens radius i STL-en: vannrett snitt z = konst, sirkel rundt stevnspissen."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as CM
S = 30.0
for path, xb in zip(sys.argv[1::2], sys.argv[2::2]):
    xb = float(xb)
    V, F = CM.weld(CM.load_raw(path))
    A = V[F[:, 0]]; B = V[F[:, 1]]; Cc = V[F[:, 2]]
    out = []
    for zq in (400.0, 700.0, 1000.0):
        zm = (zq + 1400.0) / S
        pts = []
        for P0, P1 in ((A, B), (B, Cc), (Cc, A)):
            c = (P0[:, 2] - zm) * (P1[:, 2] - zm) < 0
            f = (zm - P0[c, 2]) / (P1[c, 2] - P0[c, 2])
            pts.append(P0[c] + f[:, None] * (P1[c] - P0[c]))
        Q = np.vstack(pts) * S
        x, y = Q[:, 0] + xb, Q[:, 1]
        m = x < x.min() + 400
        x, y = x[m], y[m]
        j = np.argmin(x)
        w = np.hypot(x - x[j], y - y[j]) < 12.0
        X, Y = x[w], y[w]
        Am = np.c_[2 * X, 2 * Y, np.ones_like(X)]
        sol, *_ = np.linalg.lstsq(Am, X ** 2 + Y ** 2, rcond=None)
        R = np.sqrt(sol[2] + sol[0] ** 2 + sol[1] ** 2)
        out.append(f"z={zq:.0f}: stevn x={x[j]:.0f}, R={R:.1f} mm ({w.sum()} pkt)")
    print(os.path.basename(path), " | ".join(out))
