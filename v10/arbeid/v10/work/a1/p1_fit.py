"""Prototype-tilpasning av dekkslinjen."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "orig")); sys.path.insert(0, HERE)
from hr26 import curves as C0, params as P
import fit_lib as L
D = os.path.join(HERE, "orig", "data")
raw = np.genfromtxt(os.path.join(D, "deck_halfbreadth.csv"), delimiter=",", names=True)
so = np.array(P.STERN_OUTLINE)
rx, ry = raw["x_from_bow_mm"], raw["half_breadth_mm"]
m = rx < so[0, 0]
mx = np.r_[rx[m], so[:, 0]]; my = np.r_[ry[m], so[:, 1]]
art = (mx > 2450) & (mx < 3250)
xx = np.arange(0.0, so[-1, 0] + 0.01, 1.0)
cur = np.array([C0.deck_half_breadth(v) for v in mx])
print(f"orig: res trace {np.abs(cur[:m.sum()]-ry[m]).max():.1f} (utenom 2450-3250: {np.abs((cur-my)[(~art)&(np.arange(len(mx))<m.sum())]).max():.1f}) stern {np.abs(cur[m.sum():]-so[:,1]).max():.1f}")
def rep(name, s):
    yy = s(xx); k = L.curvature(s, xx)
    r = s(mx) - my
    sc = 0.5 * P.BEAM / yy.max()
    r2 = sc * s(mx) - my
    print(f"{name:34s} max {yy.max():7.1f}@{xx[yy.argmax()]:4.0f} res trace {np.abs(r[:m.sum()]).max():5.1f} (utenom art {np.abs(r[(~art)&(np.arange(len(mx))<m.sum())]).max():4.1f}) stern {np.abs(r[m.sum():]).max():4.1f} | skalert: trace {np.abs(r2[:m.sum()]).max():5.1f} stern {np.abs(r2[m.sum():]).max():4.1f} | fortegnsskift {L.sign_changes(xx, k, 1e-7).round().tolist()}")
    return s
cases = {
 "A lsq curves-9": dict(KN=[800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7600,7700,7760,7800,7830,7860], ws=100.0, lam=0, sign=0),
 "B konveks, samme knuter": dict(KN=[800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7600,7700,7760,7800,7830,7860], ws=100.0, lam=0, sign=-1),
 "C konveks, baugknuter": dict(KN=[150,400,800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7600,7700,7760,7800,7830,7860], ws=100.0, lam=0, sign=-1),
 "D konveks, baug, stern w=10": dict(KN=[150,400,800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7600,7700,7760,7800,7830,7860], ws=10.0, lam=0, sign=-1),
 "E konveks, faerre hekk-knuter": dict(KN=[150,400,800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7650,7780,7840], ws=10.0, lam=0, sign=-1),
}
S = {}
for nm, cs in cases.items():
    t = L.knots(0.0, so[-1, 0], cs["KN"])
    w = np.r_[np.ones(m.sum()), np.full(len(so), cs["ws"])]
    S[nm] = rep(nm, L.fit_shape(mx, my, t, w, lam=cs["lam"], sign=cs["sign"]))
np.save(os.path.join(HERE, "p1_cases.npy"), {k: (v.t, v.c) for k, v in S.items()}, allow_pickle=True)
