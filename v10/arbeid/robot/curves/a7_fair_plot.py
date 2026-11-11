"""Fairing proposal (step 4) + the key plots."""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "repo"))
from hr26 import curves as C
from hr26 import params as P
from scipy.interpolate import make_smoothing_spline, CubicSpline, PchipInterpolator
from scipy.signal import savgol_filter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B1, B2, B3, GR, INK, RED = "#2a78d6", "#eb6834", "#1baf7a", "#9a9993", "#0b0b0b", "#e34948"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": "#bdbcb6", "axes.labelcolor": INK, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False})
XS = np.load(os.path.join(HERE, "loft_stations.npy"))
LD = np.load(os.path.join(HERE, "loft_deck.npz"))
WL = np.load(os.path.join(HERE, "loft_wl.npz"))

def disc_kappa(xk, yk):
    s = np.diff(yk) / np.diff(xk); th = np.arctan(s)
    h = 0.5 * (np.diff(xk)[:-1] + np.diff(xk)[1:])
    return xk[1:-1], np.diff(th) / h * 1000.0, np.degrees(np.diff(th))

def stations(ax):
    for v in XS:
        ax.axvline(v, color="#d9d8d2", lw=0.5, zorder=0)

def kplot(ax, xk, k, color, label, clip):
    kc = np.clip(k, -clip, clip)
    ax.vlines(xk, 0, kc, color=color, lw=1.6, label=label)
    for a, b in zip(xk, k):
        if abs(b) > clip:
            ax.annotate(f"{b:+.1f}", (a, np.sign(b) * clip), fontsize=7, color=INK, ha="center",
                        va="bottom" if b > 0 else "top")

# ===================================================== fairing (step 4)
raw = np.genfromtxt(os.path.join(HERE, "repo", "data", "deck_halfbreadth.csv"), delimiter=",", names=True)
rx, ry = raw["x_from_bow_mm"], raw["half_breadth_mm"]
so = np.array(P.STERN_OUTLINE)
# measured deck outline: raw trace forward of the stern table + STERN_OUTLINE (measured point by point)
mx = np.r_[rx[rx < 7300.0], so[:, 0]]; my = np.r_[ry[rx < 7300.0], so[:, 1]]
w = np.r_[np.ones((rx < 7300.0).sum()), np.full(len(so), 10.0)]
art = ((mx > 2450) & (mx < 3250))      # dent-then-bump stretch of the trace (forehatch / stanchion / chainplate area)
from scipy.interpolate import make_lsq_spline
KN = [800, 1600, 2400, 3200, 4000, 4800, 5600, 6400, 7000, 7400, 7600, 7700, 7760, 7800, 7830, 7860]
sp_d = make_lsq_spline(mx, my, np.r_[[0.0] * 4, KN, [7891.0] * 4], k=3, w=w)
r_d = sp_d(mx) - my
lam_d = len(KN)

print(f"DECK fairing: LSQ {lam_d} knots; max |res| trace(non-artefact) {np.abs(r_d[(~art)&(w==1)]).max():.1f} mm, "
      f"artefact zone {np.abs(r_d[art]).max():.1f} mm, stern outline {np.abs(r_d[w>1]).max():.1f} mm")
xx = np.arange(0.0, 7891.0, 5.0)
cur_hb = np.array([C.deck_half_breadth(v) for v in xx])
print(f"  current deck_half_breadth vs measured: max |dev| trace(non-artefact) "
      f"{np.abs(np.interp(mx[(~art)&(w==1)], xx, cur_hb) - my[(~art)&(w==1)]).max():.1f} mm, stern {np.abs(np.interp(so[:,0], xx, cur_hb) - so[:,1]).max():.1f} mm")
print(f"  fairing vs current function: max |diff| {np.abs(sp_d(xx) - cur_hb).max():.1f} mm (x={xx[np.argmax(np.abs(sp_d(xx)-cur_hb))]:.0f})")
for x0 in (300, 2550, 3150, 7300, 7700, 7850):
    print(f"   x={x0}: current {C.deck_half_breadth(x0):.1f}  faired {float(sp_d(x0)):.1f}")

dz = np.array(P.DECK_EDGE_Z)
best = None
for lam in np.logspace(3, 12, 181):
    sp = make_smoothing_spline(dz[:, 0], dz[:, 1], lam=lam)
    if np.abs(sp(dz[:, 0]) - dz[:, 1]).max() <= 5.0:
        best = (lam, sp)
lam_s, sp_s = best
r_s = sp_s(dz[:, 0]) - dz[:, 1]
print(f"SHEER fairing: lam={lam_s:.3g}; max |res| {np.abs(r_s).max():.2f} mm at x={dz[np.argmax(np.abs(r_s)),0]:.0f}; residuals {np.round(r_s,1).tolist()}")
cur_s = np.array([C.sheer_z(v) for v in xx])
print(f"  current sheer_z vs measured: max |dev| {np.abs(np.interp(dz[:,0], xx, cur_s) - dz[:,1]).max():.2f} mm")
ks_after = sp_s.derivative(2)(xx) / (1 + sp_s.derivative(1)(xx) ** 2) ** 1.5 * 1000
sel = (xx > 300) & (xx < 7600)
print("  faired sheer curvature sign changes (300-7600):", np.round(xx[sel][np.nonzero(np.diff(np.sign(ks_after[sel])) != 0)[0]]).astype(int).tolist())
kd_after = sp_d.derivative(2)(xx) / (1 + sp_d.derivative(1)(xx) ** 2) ** 1.5 * 1000
print("  faired deck curvature sign changes (300-7600):", np.round(xx[sel][np.nonzero(np.diff(np.sign(kd_after[sel])) != 0)[0]]).astype(int).tolist())
# what the loft would make of the faired curves: interpolate the station samples (proxy for makeLoft)
def loft_proxy(f):
    xs = XS[(XS > 10) & (XS < 7840)]
    cs = CubicSpline(xs, f(xs)); xq = np.arange(xs[0], xs[-1], 5.0)
    return xq, cs(xq, 2) / (1 + cs(xq, 1) ** 2) ** 1.5 * 1000
xq, kd_lp = loft_proxy(sp_d); _, ks_lp = loft_proxy(sp_s)
xq0, kd_lp0 = loft_proxy(np.vectorize(C.deck_half_breadth)); _, ks_lp0 = loft_proxy(np.vectorize(C.sheer_z))
np.savez(os.path.join(HERE, "faired.npz"), xx=xx, hb=sp_d(xx), zs=sp_s(xx))

# ===================================================== IMAGE 1: curves as used
fig, ax = plt.subplots(6, 1, figsize=(13, 13.5), sharex=True)
xk = np.r_[C._X[C._X < 7300.0], C._SX[:-1]]; yk = np.array([C.deck_half_breadth(v) for v in xk])
a, k, _ = disc_kappa(xk, yk)
stations(ax[0]); kplot(ax[0], a, k, B1, "deck_half_breadth as used: kink / knot spacing", 1.6)
ax[0].plot(LD["x"], np.clip(savgol_filter(LD["kp"], 9, 2), -1.6, 1.6), color=B2, lw=1.1, label="exact loft deck edge (B-rep)")
ax[0].axvline(7300, color=RED, lw=1.0, ls="--"); ax[0].text(7290, 1.25, "C0 step +9.5 mm\nat x=7300", color=INK, fontsize=7.5, ha="right")
ax[0].set_ylabel("plan curvature\n1/m"); ax[0].legend(loc="lower left", ncol=2); ax[0].set_ylim(-1.75, 1.75)
ax[0].set_title("Deck outline in plan (deck_half_breadth): bow S-bend from _fair end effect (x=150-450), step at 7300, stern table kinks", loc="left", fontsize=9)
a, k, _ = disc_kappa(C._X, C._ZS); a2, k2, _ = disc_kappa(dz[:, 0], dz[:, 1])
stations(ax[1]); kplot(ax[1], a2, k2, GR, "DECK_EDGE_Z measured table (piecewise linear)", 0.25)
ax[1].vlines(a + 15, 0, np.clip(k, -0.25, 0.25), color=B1, lw=1.6, label="sheer_z as used (_ZS, 150 mm knots)")
ax[1].plot(LD["x"], np.clip(savgol_filter(LD["kz"], 9, 2), -0.25, 0.25), color=B2, lw=1.1, label="exact loft deck edge (B-rep)")
ax[1].set_ylabel("profile curvature\n1/m"); ax[1].legend(loc="lower left", ncol=3); ax[1].set_ylim(-0.27, 0.27)
ax[1].set_title("Sheer (deck edge z): measured table has an S-wiggle 3000-4500 (curvature changes sign 5 times)", loc="left", fontsize=9)
a, k, _ = disc_kappa(C._X, C._ZK); stations(ax[2]); kplot(ax[2], a, k, B1, "strake_z as used (_ZK)", 0.12)
ax[2].set_ylabel("profile curvature\n1/m"); ax[2].legend(loc="lower left"); ax[2].set_ylim(-0.13, 0.13)
ax[2].set_title("Rubbing strake centre line z: _fair end effect at 150/300; 7 curvature sign changes", loc="left", fontsize=9)
fu = np.array(P.SECTION_FULLNESS); xf = fu[:, 0] * P.LOA; sl = np.diff(fu[:, 1]) / np.diff(xf) * 1000
stations(ax[3]); ax[3].step(np.r_[xf[:-1], xf[-1]], np.r_[sl, sl[-1]], where="post", color=B1, lw=1.6, label="d(fullness)/dx as used (np.interp)")
ax[3].set_ylabel("dm/dx\n1/m"); ax[3].legend(loc="lower left")
ax[3].set_title("SECTION_FULLNESS exponent: slope jumps at 7 knots (each puts a crease into every waterline below DWL)", loc="left", fontsize=9)
wp = np.array(P.WATERPLANE); xw = P.LWL_FWD + wp[:, 0] * P.LWL; yw = C._BW_MAX * wp[:, 1]
a, k, d = disc_kappa(xw, yw); stations(ax[4]); kplot(ax[4], a, k, B1, "wl_half_breadth as used: kink / knot spacing", 0.5)
for xa, dd in zip(a, d):
    ax[4].text(xa, 0.12, f"{dd:.0f}°", fontsize=7, ha="center", color=INK)
ax[4].set_ylabel("plan curvature\n1/m"); ax[4].legend(loc="lower left"); ax[4].set_ylim(-0.55, 0.3)
ax[4].set_title("DWL half-breadth (WATERPLANE): kinks of 2-8° amidships, 27° and 23° at x=7239/7708 (labels = kink angle)", loc="left", fontsize=9)
stations(ax[5])
for key, col, lab in (("wl_150", B1, "z=+150"), ("wl_400", B2, "z=+400"), ("wl_700", B3, "z=+700")):
    xw_, yw_, kw_ = WL[key]
    ax[5].plot(xw_, np.clip(savgol_filter(kw_, 7, 2), -2, 2), color=col, lw=1.0, label=f"loft waterline {lab}")
ax[5].set_ylim(-2.1, 2.1); ax[5].set_ylabel("plan curvature\n1/m"); ax[5].legend(loc="lower left", ncol=3)
ax[5].set_title("What the loft makes of it: topside waterlines of the exact B-rep - curvature peaks sit on the stations (grey lines), 11-18 inflections each", loc="left", fontsize=9)
ax[5].set_xlabel("x from bow, full-scale mm   (grey verticals = the 42 loft stations used for 01_skrog.stl)")
ax[5].set_xlim(0, 7950)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "1_curves_as_used.png"), dpi=115); plt.close(fig)

# ===================================================== IMAGE 2: STL vs Bambu
Ld = np.load(os.path.join(HERE, "lines.npz")); BO = np.load(os.path.join(HERE, "bambu_outline.npz"))
de = Ld["de"]; de = de[(de[:, 0] > 300) & (de[:, 0] < 7710)]
fig, ax = plt.subplots(3, 1, figsize=(13, 9.6), sharex=True)
def heading(x, y):
    return np.degrees(np.arctan(np.gradient(y, x)))
xf_ = np.arange(300.0, 7700.0, 5.0)
hf = np.array([C.deck_half_breadth(v) for v in xf_])
ax[0].plot(xf_, heading(xf_, hf), color=GR, lw=1.0, label="deck_half_breadth function (as used)")
ax[0].plot(LD["x"], heading(LD["x"], LD["y"]), color=B2, lw=1.0, label="exact loft deck edge (B-rep)")
segx = np.repeat(de[:, 0], 2)[1:-1]; segh = np.repeat(np.degrees(np.arctan(np.diff(de[:, 1]) / np.diff(de[:, 0]))), 2)
ax[0].plot(segx, segh, color=B1, lw=1.8, label=f"01_skrog.stl deck edge: {len(de)} vertices, {len(de)-1} straight segments")
bx, by = BO["x"], BO["y"]; ok = ~np.isnan(by)
hb_b = heading(bx[ok], savgol_filter(by[ok], 5, 2))
ax[0].plot(bx[ok], hb_b, color=B3, lw=1.0, label="Bambu max-beam line (scaled, beam x1.223)")
ax[0].set_ylim(-25, 30); ax[0].set_ylabel("plan heading, deg"); ax[0].legend(loc="lower left", ncol=2)
ax[0].set_title("Deck outline in plan - direction of the line along the hull. A staircase = straight segments with corners (what Bambu Studio shows)", loc="left", fontsize=9)
for v in de[:, 0]:
    ax[0].axvline(v, color="#c9d8f0", lw=0.6, zorder=0)
# chord deviation per segment
dev = []
for p0, p1 in zip(de[:-1], de[1:]):
    xs_ = np.linspace(p0[0], p1[0], 60)
    dev.append(np.abs(np.array([C.deck_half_breadth(v) for v in xs_]) - np.interp(xs_, [p0[0], p1[0]], [p0[1], p1[1]])).max())
ax[1].bar(0.5 * (de[:-1, 0] + de[1:, 0]), np.array(dev) / 30.0, width=np.diff(de[:, 0]) * 0.92, color=B1, label="plan: chord sag of STL deck edge vs true curve")
devz = []
for p0, p1 in zip(de[:-1], de[1:]):
    xs_ = np.linspace(p0[0], p1[0], 60)
    devz.append(np.abs(np.array([C.sheer_z(v) for v in xs_]) - np.interp(xs_, [p0[0], p1[0]], [p0[2], p1[2]])).max())
ax[1].plot(0.5 * (de[:-1, 0] + de[1:, 0]), np.array(devz) / 30.0, "o", color=B2, ms=5, label="profile: chord sag (sheer)")
ax[1].axhline(0.2, color=RED, lw=0.9, ls="--"); ax[1].text(7600, 0.205, "0.2 mm = one layer", fontsize=7.5, color=INK, ha="right")
ax[1].set_ylabel("model mm (1:30)"); ax[1].legend(loc="upper center", ncol=2); ax[1].set_ylim(0, 0.27)
ax[1].set_title("How far the STL's straight deck-edge segments leave the true curve (model scale)", loc="left", fontsize=9)
segz = np.repeat(np.degrees(np.arctan(np.diff(de[:, 2]) / np.diff(de[:, 0]))), 2)
ax[2].plot(xf_, heading(xf_, np.array([C.sheer_z(v) for v in xf_])), color=GR, lw=1.0, label="sheer_z function (as used)")
ax[2].plot(segx, segz, color=B1, lw=1.8, label="01_skrog.stl deck edge (profile)")
ax[2].set_ylim(-9, 2); ax[2].set_ylabel("profile heading, deg"); ax[2].legend(loc="lower left", ncol=3)
ax[2].set_title("Sheer in profile - direction of the line (Bambu omitted: its max-beam height is not a well-defined line)", loc="left", fontsize=9)
ax[2].set_xlabel("x from bow, full-scale mm"); ax[2].set_xlim(0, 7950)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "2_stl_deckedge_vs_bambu.png"), dpi=115); plt.close(fig)

# ===================================================== IMAGE 3: fairing before/after
fig, ax = plt.subplots(4, 1, figsize=(13, 11), sharex=True)
xk = np.r_[C._X[C._X < 7300.0], C._SX[:-1]]; yk = np.array([C.deck_half_breadth(v) for v in xk])
a, k, _ = disc_kappa(xk, yk)
kplot(ax[0], a, k, GR, "before: deck_half_breadth as used (kink/spacing at knots)", 1.6)
ax[0].plot(LD["x"], np.clip(savgol_filter(LD["kp"], 9, 2), -1.6, 1.6), color=B2, lw=1.0, label="before: exact loft deck edge")
ax[0].plot(xx, np.clip(kd_after, -1.6, 1.6), color=B1, lw=1.8, label="after: fairing spline")
ax[0].set_ylim(-1.75, 1.75); ax[0].set_ylabel("plan curvature 1/m"); ax[0].legend(loc="lower left", ncol=3)
ax[0].set_title(f"Deck outline: least-squares cubic B-spline ({lam_d} interior knots, dense in the stern rounding) through deck_halfbreadth.csv (x<7300) + STERN_OUTLINE", loc="left", fontsize=9)
ax[1].plot(mx[~art], r_d[~art], "o", color=B1, ms=3.5, label="fairing - measured point")
ax[1].plot(mx[art], r_d[art], "x", color=RED, ms=5, label="trace points 2516-3220 (dent-then-bump stretch of the trace)")
cur_at = np.interp(mx, xx, cur_hb) - my
ax[1].plot(mx, cur_at, ".", color=GR, ms=4, label="current function - measured point")
ax[1].axhspan(-12.5, 12.5, color="#eef3fb", zorder=0); ax[1].text(7000, 13.5, "band = 0.25 mm line width on the 1:50 drawing", fontsize=7.5, color=INK, ha="right"); ax[1].set_ylabel("deviation, full mm"); ax[1].legend(loc="lower left", ncol=3)
ax[1].set_ylim(-20, 20)
a2, k2, _ = disc_kappa(dz[:, 0], dz[:, 1]); a, k, _ = disc_kappa(C._X, C._ZS)
kplot(ax[2], a2, k2, GR, "before: DECK_EDGE_Z table", 0.25)
ax[2].vlines(a + 15, 0, np.clip(k, -0.25, 0.25), color="#7d7c77", lw=1.2, label="before: sheer_z as used")
ax[2].plot(LD["x"], np.clip(savgol_filter(LD["kz"], 9, 2), -0.25, 0.25), color=B2, lw=1.0, label="before: exact loft deck edge")
ax[2].plot(xx, ks_after, color=B1, lw=1.8, label="after: fairing spline")
ax[2].set_ylim(-0.27, 0.27); ax[2].set_ylabel("profile curvature 1/m"); ax[2].legend(loc="lower left", ncol=4)
ax[2].set_title(f"Sheer: cubic smoothing spline through the 18 DECK_EDGE_Z points, lam={lam_s:.2g} (residual <= 5 mm)", loc="left", fontsize=9)
ax[3].plot(dz[:, 0], r_s, "o", color=B1, ms=5, label="fairing - DECK_EDGE_Z point")
ax[3].plot(dz[:, 0], np.interp(dz[:, 0], xx, cur_s) - dz[:, 1], ".", color=GR, ms=6, label="current sheer_z - DECK_EDGE_Z point")
ax[3].axhspan(-5, 5, color="#eef3fb", zorder=0); ax[3].set_ylabel("deviation, full mm"); ax[3].legend(loc="lower left", ncol=2)
ax[3].set_xlabel("x from bow, full-scale mm"); ax[3].set_xlim(0, 7950)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "3_fairing_before_after.png"), dpi=115); plt.close(fig)
print("loft-proxy curvature sign changes 300-7600 (station samples -> cubic):")
s = (xq > 300) & (xq < 7600)
for nm, kk in (("deck before", kd_lp0), ("deck after", kd_lp), ("sheer before", ks_lp0), ("sheer after", ks_lp)):
    print(f"   {nm:12s}: {int((np.diff(np.sign(kk[s])) != 0).sum())}")
