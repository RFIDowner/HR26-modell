import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "orig")); sys.path.insert(0, HERE)
from hr26 import curves as C0, params as P
import fit_lib as L
from scipy.interpolate import make_smoothing_spline
D = os.path.join(HERE, "orig", "data")
hs = np.genfromtxt(os.path.join(D, "hull_stations.csv"), delimiter=",", names=True)
uw = np.loadtxt(os.path.join(D, "uw_station.csv"), delimiter=",", skiprows=1)
dz = np.array(P.DECK_EDGE_Z)
xx = np.arange(0.0, 7950.01, 1.0)
# ------------------------------------------- spring: utjevnende spline
for lam in [1e7, 2e7, 4e7, 8e7]:
    t = np.r_[[dz[0, 0]] * 4, dz[1:-1, 0], [dz[-1, 0]] * 4]
    s = L.fit(dz[:, 0], dz[:, 1], t, lam=lam, pen_der=2)
    ref = make_smoothing_spline(dz[:, 0], dz[:, 1], lam=lam)
    r = s(dz[:, 0]) - dz[:, 1]
    k = L.curvature(s, xx)
    print(f"sheer lam={lam:.0e}: max|res| {np.abs(r).max():.2f} at {dz[np.argmax(np.abs(r)),0]:.0f}  vs scipy {np.abs(s(xx)-ref(xx)).max():.2e}  inflections {L.sign_changes(xx, k, 1e-9).round().tolist()}")
r0 = np.array([C0.sheer_z(v) for v in dz[:, 0]]) - dz[:, 1]
print(f"sheer orig: max|res| {np.abs(r0).max():.2f}")
# ------------------------------------------- fenderlist
xs, zk = hs["x_from_bow_mm"], hs["strake_z_mm"]
r0 = np.array([C0.strake_z(v) for v in xs]) - zk
print(f"strake orig: max|res| {np.abs(r0).max():.2f}")
for KN in ([1000, 2000, 3000, 4000, 5000, 6000, 7000], [800, 1600, 2400, 3200, 4000, 4800, 5600, 6400, 7200], [600, 1500, 2500, 3300, 4000, 4800, 5600, 6400, 7100]):
    for sign in (0, 1):
        t = L.knots(0.0, 7950.0, KN)
        s = L.fit_shape(xs, zk, t, sign=sign)
        r = s(xs) - zk; k = L.curvature(s, xx)
        print(f"strake {KN} sign={sign}: max|res| {np.abs(r).max():.2f} at {xs[np.argmax(np.abs(r))]:.0f}, inflections {len(L.sign_changes(xx, k, 1e-9))}")
