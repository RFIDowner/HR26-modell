"""Verifiserer de nye kurvene i arbeidstreet mot maalepunktene og mot V9."""
import os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
sys.path.insert(0, os.path.join(HERE, "origpkg")); sys.path.insert(0, WT)
t0 = time.time()
from hr26 import curves as C, params as P
print(f"import curves: {time.time() - t0:.2f}s")
from hr26o import curves as C0
D = os.path.join(WT, "data")

def ev(f, xs):
    return np.array([f(float(v)) for v in xs])

def dkappa(f, xs, h=1.0):
    y = ev(f, xs); yp = ev(f, xs + h); ym = ev(f, xs - h)
    d1 = (yp - ym) / (2 * h); d2 = (yp - 2 * y + ym) / h ** 2
    return d2 / (1 + d1 ** 2) ** 1.5 * 1000.0          # 1/m

def kinks(f, xs, h=0.5):
    """Knekk (grader) i hvert punkt: vinkelen mellom tangentene rett foer og rett etter."""
    a = np.degrees(np.arctan((ev(f, xs) - ev(f, xs - h)) / h))
    b = np.degrees(np.arctan((ev(f, xs + h) - ev(f, xs)) / h))
    return b - a

def nsign(k, eps=1e-3):
    s = np.sign(np.where(np.abs(k) <= eps, 0, k)); s = s[s != 0]
    return int((np.diff(s) != 0).sum())

out = {}
# ------------------------------------------------- dekkslinje
raw = np.genfromtxt(os.path.join(D, "deck_halfbreadth.csv"), delimiter=",", names=True)
so = np.array(P.STERN_OUTLINE)
m = raw["x_from_bow_mm"] < so[0, 0]
tx, ty = raw["x_from_bow_mm"][m], raw["half_breadth_mm"][m]
xx = np.arange(0.0, 7891.0, 1.0)
for nm, mod in (("V9 ", C0), ("V10", C)):
    rt = ev(mod.deck_half_breadth, tx) - ty
    rs = ev(mod.deck_half_breadth, so[:, 0]) - so[:, 1]
    y = ev(mod.deck_half_breadth, xx)
    k = dkappa(mod.deck_half_breadth, xx[2:-2])
    kk = kinks(mod.deck_half_breadth, xx[2:-2])
    print(f"DEKK {nm}: bredde {2*y.max():.1f} mm @x={xx[y.argmax()]:.0f}; maks avvik spor {np.abs(rt).max():.1f} mm (x={tx[np.argmax(np.abs(rt))]:.0f}), "
          f"hekk {np.abs(rs).max():.1f} mm; sprang ved 7300: {mod.deck_half_breadth(7300.0) - mod.deck_half_breadth(7299.999):+.2f} mm; "
          f"stoerste knekk {np.abs(kk).max():.2f} grader; krumningsskift 0-7891: {nsign(k)}")
# holdestykket aktenfor hjoernet
print("  hold: " + ", ".join(f"{v:.0f}:{C.deck_half_breadth(v):.1f}/{C0.deck_half_breadth(v):.1f}" for v in (7850, 7891, 7900, 7910, 7948, 7970, 7990)))
d = ev(C.deck_half_breadth, xx) - ev(C0.deck_half_breadth, xx)
print(f"  V10 - V9: {d.min():+.1f} .. {d.max():+.1f} mm (min @x={xx[d.argmin()]:.0f}, maks @x={xx[d.argmax()]:.0f})")
# ------------------------------------------------- spring
dz = np.array(P.DECK_EDGE_Z)
xs = np.arange(0.0, 7950.0, 1.0)
for nm, mod in (("V9 ", C0), ("V10", C)):
    r = ev(mod.sheer_z, dz[:, 0]) - dz[:, 1]
    k = dkappa(mod.sheer_z, xs[2:-2]); kk = kinks(mod.sheer_z, xs[2:-2])
    print(f"SPRING {nm}: maks avvik {np.abs(r).max():.1f} mm (x={dz[np.argmax(np.abs(r)),0]:.0f}); stoerste knekk {np.abs(kk).max():.3f} grader; krumningsskift {nsign(k, 1e-4)}")
# ------------------------------------------------- fenderlist
hs = np.genfromtxt(os.path.join(D, "hull_stations.csv"), delimiter=",", names=True)
for nm, mod in (("V9 ", C0), ("V10", C)):
    r = ev(mod.strake_z, hs["x_from_bow_mm"]) - hs["strake_z_mm"]
    k = dkappa(mod.strake_z, xs[2:-2]); kk = kinks(mod.strake_z, xs[2:-2])
    print(f"LIST {nm}: maks avvik {np.abs(r).max():.1f} mm (x={hs['x_from_bow_mm'][np.argmax(np.abs(r))]:.0f}); stoerste knekk {np.abs(kk).max():.3f} grader; krumningsskift {nsign(k, 1e-4)}")
# ------------------------------------------------- profil
uw = np.loadtxt(os.path.join(D, "uw_station.csv"), delimiter=",", skiprows=1)
ff = (uw[:, 0] >= P.LWL_FWD) & (uw[:, 0] <= 2800.0)
sx = np.arange(0.0, 851.0, 5.0)
stem0 = ev(C0.bottom_z, sx)
for nm, mod in (("V9 ", C0), ("V10", C)):
    r = ev(mod.bottom_z, uw[ff, 0]) + uw[ff, 1]
    rs = ev(mod.bottom_z, sx) - stem0
    k = dkappa(mod.bottom_z, xs[2:-2]); kk = kinks(mod.bottom_z, xs[2:-2])
    jump = mod.bottom_z(1008.001) - mod.bottom_z(1007.999)
    print(f"PROFIL {nm}: forfot/kanobunn 1008-2800 maks avvik fra sporet {np.abs(r).max():.1f} mm (x={uw[ff,0][np.argmax(np.abs(r))]:.0f}); "
          f"forstevn 0-850 mot V9 {np.abs(rs).max():.1f} mm; sprang ved 1008 {jump:+.1f} mm; stoerste knekk {np.abs(kk).max():.2f} grader @x={xs[2:-2][np.argmax(np.abs(kk))]:.0f}; krumningsskift {nsign(k, 1e-4)}")
xr = 0.5 * (P.KEEL_LE_ROOT + P.KEEL_TE_ROOT)
print(f"  kjolrot bottom_z({xr:.0f}): V9 {C0.bottom_z(xr):.2f}  V10 {C.bottom_z(xr):.2f}")
def transom_bottom(f):
    xs_ = np.arange(7600.0, 7950.0, 0.25)
    g = ev(f, xs_) - (xs_ - P.TRANSOM_WL_X) / P.TRANSOM_RAKE
    i = np.nonzero(np.diff(np.sign(g)))[0][0]
    return xs_[i], f(xs_[i])
print("  akterspeilets underkant paa senterlinjen: V9 x=%.0f z=%.1f   V10 x=%.0f z=%.1f" % (*transom_bottom(C0.bottom_z), *transom_bottom(C.bottom_z)))
print("  stevnhode: bottom_z(0)=%.1f sheer_z(0)=%.1f; ved x=4: %.1f / %.1f; DWL-kryss: x=%.1f" % (C.bottom_z(0), C.sheer_z(0), C.bottom_z(4), C.sheer_z(4),
      xs[np.argmin(np.abs(ev(C.bottom_z, xs[800:1200])))+800]))
db = ev(C.bottom_z, xs) - ev(C0.bottom_z, xs)
for a, b in ((0, 850), (850, 1008), (1008, 2800), (2800, 3800), (3800, 5800), (5800, 7950)):
    s = (xs >= a) & (xs < b)
    print(f"  V10-V9 bunn {a}-{b}: {db[s].min():+.1f}..{db[s].max():+.1f}")
# ------------------------------------------------- tabeller
for nm, f0, f1, rng in (("FULLNESS", C0.fullness, C.fullness, (0, 7950)), ("WL", C0.wl_half_breadth, C.wl_half_breadth, (1009, 7950))):
    xq = np.arange(rng[0] + 2, rng[1] - 2, 1.0)
    for v, f in (("V9 ", f0), ("V10", f1)):
        kk = kinks(f, xq)
        print(f"{nm} {v}: stoerste knekk {np.abs(kk).max():.3f} grader @x={xq[np.argmax(np.abs(kk))]:.0f}; maks {ev(f, xq).max():.2f}")
print(f"_BW_MAX V9 {C0._BW_MAX:.1f}  V10 {C._BW_MAX:.1f}")
# WL innenfor dekkshalvbredden?
xq = np.arange(1010.0, 7900.0, 5.0)
print("WL - dekk (maks, skal vaere < 0):", (ev(C.wl_half_breadth, xq) - ev(C.deck_half_breadth, xq)).max().round(1))
# fart
t0 = time.time()
for v in np.linspace(0, 7950, 20000):
    C.deck_half_breadth(v); C.sheer_z(v); C.bottom_z(v); C.strake_z(v)
print(f"80 000 kall: {time.time() - t0:.2f}s")
t0 = time.time()
for v in np.linspace(0, 7950, 200):
    C.section(v, 26)
print(f"200 section(): {time.time() - t0:.2f}s")
