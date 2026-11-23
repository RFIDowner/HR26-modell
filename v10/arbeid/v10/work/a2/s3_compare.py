"""Silhuetter og vannlinje fra STL: V9 (baseline), A1 og A2. Fullskala mm.
STL-ene er i baatkoordinater (modell-mm, baugspissen paa x=0, kjolen paa z=0).
argv: v9.stl a1.stl a2.stl  (baugspissens x i fullskala: 4, 4, 2)"""
import os, sys, time, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as CM
S = 30.0
DRAFT = 1400.0
paths = sys.argv[1:4]
XB = [4.0, 4.0, 4.0]
NAMES = ["V9", "A1", "A2"]


def load(path):
    V, F = CM.weld(CM.load_raw(path))
    return V, F


def edges(V, F):
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    return V[E[:, 0]], V[E[:, 1]]


def x_planes(A, B, dx):
    """Kryssingspunkter med planene x = k*dx (modell-mm): (k, punkt)."""
    sw = A[:, 0] > B[:, 0]
    A2 = np.where(sw[:, None], B, A); B2 = np.where(sw[:, None], A, B)
    k0 = np.ceil(A2[:, 0] / dx).astype(np.int64); k1 = np.floor(B2[:, 0] / dx).astype(np.int64)
    cnt = np.maximum(k1 - k0 + 1, 0)
    sel = cnt > 0
    A2, B2, k0, cnt = A2[sel], B2[sel], k0[sel], cnt[sel]
    rep = np.repeat(np.arange(len(cnt)), cnt)
    off = np.arange(len(rep)) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    k = k0[rep] + off
    L = np.maximum(B2[rep, 0] - A2[rep, 0], 1e-12)
    f = np.clip((k * dx - A2[rep, 0]) / L, 0.0, 1.0)
    return k, A2[rep] + f[:, None] * (B2[rep] - A2[rep])


def analyse(V, F, xb, dxf=6.0):
    A, B = edges(V, F)
    dx = dxf / S
    k, Pt = x_planes(A, B, dx)
    n = int(k.max()) + 1
    x = np.arange(n) * dxf + xb
    y = np.abs(Pt[:, 1]) * S
    z = Pt[:, 2] * S - DRAFT
    ymax = np.full(n, -np.inf); zmax = np.full(n, -np.inf); zmin = np.full(n, np.inf)
    np.maximum.at(ymax, k, y); np.maximum.at(zmax, k, z); np.minimum.at(zmin, k, z)
    # vannlinjen: kryssinger med z = DWL blant kantene, per x-boks
    za, zb_ = A[:, 2] * S - DRAFT, B[:, 2] * S - DRAFT
    c = (za < 0) != (zb_ < 0)
    f = za[c] / (za[c] - zb_[c])
    P = A[c] + f[:, None] * (B[c] - A[c])
    kx = np.floor(P[:, 0] / dx + 0.5).astype(np.int64)
    ok = (kx >= 0) & (kx < n)
    wl = np.full(n, -1.0)
    np.maximum.at(wl, kx[ok], np.abs(P[ok, 1]) * S)
    wl[wl < 0] = np.nan
    # senterlinjens underkant (|y| < 15 mm): profilen under vann
    cl = np.abs(Pt[:, 1]) * S < 15.0
    zcl = np.full(n, np.inf)
    np.minimum.at(zcl, k[cl], z[cl])
    bb = V.min(0), V.max(0)
    return dict(x=x, ymax=ymax, zmax=zmax, zmin=zmin, wl=wl, zcl=zcl, size=(bb[1] - bb[0]) * S, ntri=len(F))


t = time.time()
R = []
for p, xb in zip(paths, XB):
    V, F = load(p)
    R.append(analyse(V, F, xb))
print(f"lest og analysert {time.time()-t:.0f}s")
for nm, r in zip(NAMES, R):
    print(f"{nm}: {r['ntri']} tri, boks {np.round(r['size'], 1)} mm, stoerste bredde {2*np.nanmax(r['ymax'][np.isfinite(r['ymax'])]):.1f}, "
          f"stoerste vannlinjebredde {2*np.nanmax(r['wl']):.0f} ved x={r['x'][np.nanargmax(r['wl'])]:.0f}")


def cmp(a, b, key, lo, hi, label):
    xa, xb_ = R[a]["x"], R[b]["x"]
    xs = np.arange(lo, hi, 6.0)
    ya = np.interp(xs, xa, np.where(np.isfinite(R[a][key]), R[a][key], np.nan))
    yb = np.interp(xs, xb_, np.where(np.isfinite(R[b][key]), R[b][key], np.nan))
    d = yb - ya
    ok = np.isfinite(d)
    i = np.nanargmax(np.abs(np.where(ok, d, 0)))
    print(f"  {label:44s} {NAMES[b]}-{NAMES[a]}: min {np.nanmin(d[ok]):7.1f}  maks {np.nanmax(d[ok]):7.1f}  (stoerst ved x={xs[i]:.0f})")


print("SILHUETTER (fullskala mm):")
for a, b in ((0, 2), (1, 2)):
    cmp(a, b, "ymax", 20, 7900, "plan, halvbredde (med fenderlist)")
    cmp(a, b, "zmax", 20, 7900, "profil, overkant")
    cmp(a, b, "zcl", 20, 3300, "profil, senterlinje under, x 20-3300")
    cmp(a, b, "zcl", 5900, 7760, "profil, senterlinje under, x 5900-7760")
    cmp(a, b, "wl", 1100, 7700, "vannlinjens halvbredde")
np.savez(os.path.join(HERE, "sil_cmp.npz"), **{f"{nm}_{k}": v for nm, r in zip(NAMES, R) for k, v in r.items() if k not in ("size", "ntri")})
