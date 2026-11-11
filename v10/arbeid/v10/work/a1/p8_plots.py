"""Krumning foer/etter og avvik fra maalepunktene for alle lengdekurvene."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
sys.path.insert(0, os.path.join(HERE, "origpkg")); sys.path.insert(0, WT)
from hr26 import curves as C, params as P
from hr26o import curves as C0
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

V9C, V10C, INK, SEC, BAND = "#9a9993", "#2a78d6", "#0b0b0b", "#52514e", "#e9f0fa"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": "#bdbcb6", "axes.labelcolor": INK, "xtick.color": SEC,
                     "ytick.color": SEC, "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "axes.titlesize": 9, "axes.titleweight": "bold", "axes.titlelocation": "left"})
D = os.path.join(WT, "data")

def ev(f, xs):
    return np.array([f(float(v)) for v in xs])

def kappa(f, xs, h):
    y = ev(f, xs); yp = ev(f, xs + h); ym = ev(f, xs - h)
    d1 = (yp - ym) / (2 * h); d2 = (yp - 2 * y + ym) / h ** 2
    return d2 / (1 + d1 ** 2) ** 1.5 * 1000.0

def nsign(k, eps):
    s = np.sign(np.where(np.abs(k) <= eps, 0, k)); s = s[s != 0]
    return int((np.diff(s) != 0).sum())

def kpanel(ax, f0, f1, x0, x1, h, clip, title, eps):
    xs = np.arange(x0 + h, x1 - h, 2.0)
    k0, k1 = kappa(f0, xs, h), kappa(f1, xs, h)
    ax.plot(xs, np.clip(k0, -clip, clip), color=V9C, lw=1.0, label=f"V9 (np.interp + _fair): {nsign(k0, eps)} fortegnsskift")
    ax.plot(xs, k1, color=V10C, lw=2.0, label=f"V10 (spline): {nsign(k1, eps)} fortegnsskift")
    ax.set_ylim(-clip * 1.08, clip * 1.08); ax.axhline(0, color="#bdbcb6", lw=0.8)
    ax.set_title(title); ax.set_ylabel("krumning 1/m"); ax.legend(loc="lower left", fontsize=7.5)
    ax.text(0.995, 0.97, f"V9 klippet ved +-{clip:g} (knekk = topper)", transform=ax.transAxes, ha="right", va="top", fontsize=7, color=SEC)

fig, ax = plt.subplots(5, 2, figsize=(15.5, 17.5))
# ------------------------------------------------------ dekkslinje
kpanel(ax[0, 0], C0.deck_half_breadth, C.deck_half_breadth, 0.0, 7400.0, 10.0, 0.6,
       "Dekkslinjen i plan, x 0-7400: krumning (negativ = buer utover)", 0.01)
xs = np.arange(7150.0, 7885.0, 1.0)
ax[0, 1].plot(xs, np.clip(kappa(C0.deck_half_breadth, xs, 5.0), -12, 12), color=V9C, lw=1.0, label="V9: hopp ved 7300, knekk i hvert maalepunkt")
ax[0, 1].plot(xs, kappa(C.deck_half_breadth, xs, 5.0), color=V10C, lw=2.0, label="V10: en topp, R min %.0f mm" % (1000.0 / abs(kappa(C.deck_half_breadth, xs, 5.0)).max()))
xt = np.array([C.transom_x(C.sheer_z(7850.0), y) for y in [C.deck_half_breadth(7845.0)]])
ax[0, 1].axvline(xt[0], color=INK, lw=0.8, ls="--"); ax[0, 1].text(xt[0] - 4, -11, "akterspeilet kapper\nher i dekkshoyde", ha="right", fontsize=7, color=SEC)
ax[0, 1].set_ylim(-12.5, 12.5); ax[0, 1].set_title("Dekkslinjen rundt hekken, x 7150-7885"); ax[0, 1].set_ylabel("krumning 1/m"); ax[0, 1].legend(loc="upper left", fontsize=7.5)
# avvik
raw = np.genfromtxt(os.path.join(D, "deck_halfbreadth.csv"), delimiter=",", names=True)
so = np.array(P.STERN_OUTLINE); m = raw["x_from_bow_mm"] < so[0, 0]
mx = np.r_[raw["x_from_bow_mm"][m], so[:, 0]]; my = np.r_[raw["half_breadth_mm"][m], so[:, 1]]
a = ax[1, 0]
a.axhspan(-12.5, 12.5, color=BAND, zorder=0)
r0 = ev(C0.deck_half_breadth, mx) - my; r1 = ev(C.deck_half_breadth, mx) - my
a.plot(mx, r0, "o", color=V9C, ms=3.5, label=f"V9: maks {np.abs(r0).max():.1f} mm, bredde {2*max(ev(C0.deck_half_breadth, np.arange(0, 7891, 5.0))):.0f}")
a.plot(mx, r1, "o", color=V10C, ms=4.5, label=f"V10: maks {np.abs(r1).max():.1f} mm, bredde {2*max(ev(C.deck_half_breadth, np.arange(0, 7891, 5.0))):.0f}")
a.text(7950, 13.2, "baand = en strek paa 1:50-tegningen (12,5 mm)", ha="right", fontsize=7, color=SEC)
a.text(2860, -16.5, "2 516-3 220: bulk i sporet\n(rekkefester/vant paa tegningen)", ha="center", fontsize=7, color=SEC)
a.set_ylim(-20, 20); a.set_ylabel("kurve - maalepunkt, mm"); a.legend(loc="upper left", fontsize=7.5)
a.set_title("Dekkslinjen: avvik fra sporet (x < 7300) og STERN_OUTLINE")
# ------------------------------------------------------ spring
kpanel(ax[1, 1], C0.sheer_z, C.sheer_z, 0.0, 7950.0, 10.0, 0.3, "Springet (dekkskantens hoyde): krumning i profil", 0.003)
dz = np.array(P.DECK_EDGE_Z)
ins = ax[1, 1].inset_axes([0.62, 0.62, 0.36, 0.33])
ins.axhspan(-5, 5, color=BAND, zorder=0)
ins.plot(dz[:, 0], ev(C0.sheer_z, dz[:, 0]) - dz[:, 1], "o", color=V9C, ms=3)
ins.plot(dz[:, 0], ev(C.sheer_z, dz[:, 0]) - dz[:, 1], "o", color=V10C, ms=3.5)
ins.set_title("avvik fra DECK_EDGE_Z, mm (V9 7,1 / V10 5,0)", fontsize=7, fontweight="normal"); ins.tick_params(labelsize=6.5)
# ------------------------------------------------------ fenderlist
kpanel(ax[2, 0], C0.strake_z, C.strake_z, 0.0, 7950.0, 10.0, 0.12, "Fenderlistens hoyde: krumning i profil (V10 maks 1,3 mm fra strake_z_mm)", 0.003)
# ------------------------------------------------------ profil
kpanel(ax[2, 1], C0.bottom_z, C.bottom_z, 0.0, 7950.0, 10.0, 2.5, "Profilen paa senterlinjen (stevn, forfot, kanobunn): krumning", 0.003)
ax[2, 1].annotate("V9: sprang 91 mm\nved 1008", (1008, 2.5), (1500, 1.7), fontsize=7, color=INK, arrowprops=dict(arrowstyle="-", color=SEC, lw=0.7))
uw = np.loadtxt(os.path.join(D, "uw_station.csv"), delimiter=",", skiprows=1)
a = ax[3, 0]
xs = np.arange(0.0, 3400.0, 2.0)
a.plot(uw[uw[:, 0] < 3400, 0], -uw[uw[:, 0] < 3400, 1], ".", color=INK, ms=1.2, label="sporet undervannsprofil (uw_station.csv)")
a.plot(xs, ev(C0.bottom_z, xs), color=V9C, lw=1.2, label="V9")
a.plot(xs, ev(C.bottom_z, xs), color=V10C, lw=2.0, label="V10")
a.axhline(0, color="#bdbcb6", lw=0.8); a.text(30, 12, "DWL", fontsize=7, color=SEC)
a.set_xlim(0, 3400); a.set_ylim(-560, 1260); a.set_ylabel("z over DWL, mm"); a.legend(loc="upper right", fontsize=7.5)
a.set_title("Forstevn og forfot i profil")
ins = a.inset_axes([0.33, 0.38, 0.33, 0.42])
s = (uw[:, 0] >= P.LWL_FWD) & (uw[:, 0] <= 2800)
ins.axhspan(-12.5, 12.5, color=BAND, zorder=0)
ins.plot(uw[s, 0], ev(C0.bottom_z, uw[s, 0]) + uw[s, 1], color=V9C, lw=1.0)
ins.plot(uw[s, 0], ev(C.bottom_z, uw[s, 0]) + uw[s, 1], color=V10C, lw=1.6)
ins.set_ylim(-40, 100); ins.tick_params(labelsize=6.5)
ins.set_title("kurve - spor, mm (V9 maks 85 / V10 maks 10)", fontsize=7, fontweight="normal")
# hele profilen
a = ax[3, 1]
xs = np.arange(0.0, 7951.0, 2.0)
a.plot(uw[:, 0], -uw[:, 1], ".", color=INK, ms=1.0, label="sporet omriss (med kjol, propell, ror)")
a.plot(xs, ev(C0.bottom_z, xs), color=V9C, lw=1.2, label="V9")
a.plot(xs, ev(C.bottom_z, xs), color=V10C, lw=2.0, label="V10")
h = np.array(P.CANOE_BOTTOM_HIDDEN); a.plot(h[:, 0], h[:, 1], "s", color=SEC, ms=3, mfc="none", label="CANOE_BOTTOM_HIDDEN (skjult bak kjol/propell/ror)")
a.set_xlim(0, 8200); a.set_ylim(-1450, 1260); a.set_ylabel("z over DWL, mm"); a.legend(loc="upper right", fontsize=7.5)
a.set_title("Hele profilen")
# ------------------------------------------------------ vannlinje og fyldighet
kpanel(ax[4, 0], C0.wl_half_breadth, C.wl_half_breadth, 1012.0, 7770.0, 10.0, 2.0, "Halvbredde i DWL (WATERPLANE): krumning i plan, fram til akterspeilet (7 770)", 0.003)
ax[4, 0].annotate("V9: 27 grader knekk ved 7239", (7239, -2.0), (5600, -1.6), fontsize=7, color=INK, arrowprops=dict(arrowstyle="-", color=SEC, lw=0.7))
a = ax[4, 1]
xs = np.arange(0.0, 7950.0, 2.0)
a.plot(xs, np.gradient(ev(C0.fullness, xs), xs) * 1000, color=V9C, lw=1.0, label="V9: trappetrinn (np.interp)")
a.plot(xs, np.gradient(ev(C.fullness, xs), xs) * 1000, color=V10C, lw=2.0, label="V10: naturlig kubisk spline")
a.set_title("SECTION_FULLNESS: helning dm/dx"); a.set_ylabel("dm/dx, 1/m"); a.legend(loc="lower left", fontsize=7.5)
for r in ax.ravel():
    r.set_xlabel("x fra baugen, fullskala mm")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "a1_curvature_before_after.png"), dpi=100)
print("ok")
