"""Exact loft lines vs input functions vs STL vs Bambu: numbers."""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "repo"))
from hr26 import curves as C
from hr26 import params as P
from scipy.signal import savgol_filter

L = np.load(os.path.join(HERE, "loft_lines.npz"))
XS = np.load(os.path.join(HERE, "loft_stations.npy"))

def resample(p, step=5.0, x0=None, x1=None):
    p = p[np.argsort(p[:, 0])]
    _, u = np.unique(np.round(p[:, 0], 3), return_index=True)
    p = p[u]
    x0 = p[0, 0] if x0 is None else x0; x1 = p[-1, 0] if x1 is None else x1
    xx = np.arange(np.ceil(x0), x1, step)
    return xx, np.interp(xx, p[:, 0], p[:, 1]), np.interp(xx, p[:, 0], p[:, 2])

def curv(xx, yy):
    d1 = np.gradient(yy, xx); d2 = np.gradient(d1, xx)
    return d2 / (1 + d1 ** 2) ** 1.5 * 1000.0       # 1/m

# --- exact loft deck edge
de = L["deck_edge"]
x, y, z = resample(de, 5.0, 20.0, 7840.0)
hb = np.array([C.deck_half_breadth(v) for v in x]); zs = np.array([C.sheer_z(v) for v in x])
dy = y - hb; dz = z - zs
i = np.argmax(np.abs(dy))
print(f"LOFT deck edge vs deck_half_breadth: max |dy| {abs(dy[i]):.1f} mm at x={x[i]:.0f}")
m = np.abs(dy) > 2.0
runs = []
idx = np.nonzero(m)[0]
if len(idx):
    start = idx[0]; prev = idx[0]
    for k in idx[1:]:
        if k != prev + 1:
            runs.append((x[start], x[prev], dy[start:prev + 1][np.argmax(np.abs(dy[start:prev + 1]))])); start = k
        prev = k
    runs.append((x[start], x[prev], dy[start:prev + 1][np.argmax(np.abs(dy[start:prev + 1]))]))
print("  runs with |dy| > 2 mm (x0, x1, peak dy):", [(int(a), int(b), round(float(c), 1)) for a, b, c in runs])
print(f"  max |dz| (sheer) {np.abs(dz).max():.2f} mm")
kp = curv(x, y); kz = curv(x, z)
# curvature sign changes of the loft deck edge in plan, 300..7600
sel = (x > 300) & (x < 7600)
sg = np.sign(savgol_filter(kp, 9, 2)[sel]); sc = np.nonzero(np.diff(sg) != 0)[0]
print("  plan curvature sign changes (loft deck edge, 300-7600):", np.round(x[sel][sc]).astype(int).tolist())
sg = np.sign(savgol_filter(kz, 9, 2)[sel]); sc = np.nonzero(np.diff(sg) != 0)[0]
print("  profile curvature sign changes (loft deck edge, 300-7600):", np.round(x[sel][sc]).astype(int).tolist())
np.savez(os.path.join(HERE, "loft_deck.npz"), x=x, y=y, z=z, kp=kp, kz=kz, dy=dy, dz=dz)

# --- loft waterlines (topsides and below): curvature peaks vs knots/stations
wp_knots = P.LWL_FWD + np.array([p[0] for p in P.WATERPLANE]) * P.LWL
fu_knots = np.array([p[0] for p in P.SECTION_FULLNESS]) * P.LOA
print("WATERPLANE knots x:", np.round(wp_knots).astype(int).tolist())
print("FULLNESS knots x:", np.round(fu_knots).astype(int).tolist())
WL = {}
for key in ("wl_-300", "wl_-150", "wl_150", "wl_400", "wl_700", "wl_900"):
    p = L[key]
    xx, yy, _ = resample(p, 5.0)
    k = curv(xx, yy)
    WL[key] = (xx, yy, k)
    # local maxima of |kappa| above a threshold, interior
    ks = savgol_filter(k, 7, 2)
    a = np.abs(ks)
    pk = [j for j in range(2, len(a) - 2) if a[j] == a[j - 2:j + 3].max() and a[j] > 0.25 and 400 < xx[j] < 7700]
    near = []
    for j in pk:
        dst = np.abs(XS - xx[j]).min(); dk = np.abs(wp_knots - xx[j]).min(); df = np.abs(fu_knots - xx[j]).min()
        near.append((int(xx[j]), round(float(ks[j]), 2), int(dst), int(dk), int(df)))
    print(f"{key}: |kappa| peaks > 0.25 1/m (x, kappa, d_to_station, d_to_WATERPLANE_knot, d_to_FULLNESS_knot):")
    for r in near:
        print("    ", r)
    # curvature sign changes (wiggles) 500-7500
    sel = (xx > 600) & (xx < 7400)
    s2 = np.sign(ks[sel]); print("   sign changes at:", np.round(xx[sel][np.nonzero(np.diff(s2) != 0)[0]]).astype(int).tolist())
np.savez(os.path.join(HERE, "loft_wl.npz"), **{k: np.stack([v[0], v[1], v[2]]) for k, v in WL.items()})

# --- STL polyline and Bambu: max heading change over 30 mm and curvature after the same SG filter
Ld = np.load(os.path.join(HERE, "lines.npz"))
dep = Ld["de"]; dep = dep[(dep[:, 0] > 300) & (dep[:, 0] < 7710)]
xs_ = np.arange(400.0, 7600.0, 10.0)
ys_ = np.interp(xs_, dep[:, 0], dep[:, 1]); zs_ = np.interp(xs_, dep[:, 0], dep[:, 2])
bx, by, bz = Ld["b_x"], Ld["b_y"], Ld["b_z"]
yb = np.interp(xs_, bx, by)
ymo = np.load(os.path.join(HERE, "ours_maxy.npy")); xo = (np.arange(len(ymo)) + 0.5) * 10.0
yo = np.interp(xs_, xo, ymo)
yf = np.array([C.deck_half_breadth(v) for v in xs_])
def head(yy, xx, w=3):
    return np.degrees(np.arctan(np.gradient(yy, xx)))
for nm, yy in (("function deck_half_breadth", yf), ("STL deck-edge polyline", ys_), ("STL max|y| silhouette", yo), ("Bambu max|y| silhouette (beam x1.223)", yb)):
    th = head(yy, xs_)
    jump = np.abs(th[3:] - th[:-3]).max()          # 30 mm window
    k = savgol_filter(yy, 31, 3, deriv=2, delta=10.0) * 1000.0     # 1/m, 300 mm window
    kk = k[(xs_ > 800) & (xs_ < 7300)]
    sgc = int((np.diff(np.sign(kk)) != 0).sum())
    print(f"{nm:40s}: max heading change over 30 mm {jump:5.2f} deg; SG(300mm) curvature range {kk.min():+.3f}..{kk.max():+.3f} 1/m, sign changes 800-7300: {sgc}")
np.savez(os.path.join(HERE, "plan_cmp.npz"), x=xs_, yf=yf, ys=ys_, yo=yo, yb=yb, zs=zs_)
# Bambu profile of its max-beam line and our STL sheer
zb = np.interp(xs_, bx, bz)
for nm, zz in (("STL sheer polyline z", zs_), ("Bambu z of max-beam line", savgol_filter(zb, 5, 1))):
    th = head(zz, xs_)
    print(f"{nm:40s}: max heading change over 30 mm {np.abs(th[3:] - th[:-3]).max():5.2f} deg")
