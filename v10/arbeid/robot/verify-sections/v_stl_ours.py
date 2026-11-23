"""Slice our 01_skrog.stl and compare with curves.section() formula."""
import sys, math, json
import numpy as np
HERE = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-sections"
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:/Users/stig/Documents/GitHub/HR26-modell")
from v_stl_lib import load_stl, rot_z, slice_x, outer_y_of_z
from hr26 import curves as C, params as P

ANG = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
T = rot_z(load_stl(r"C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl"), -ANG)
V = T.reshape(-1, 3)
T[:, :, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min())
V = T.reshape(-1, 3)
# full-scale frame: keel bottom z=0 -> -1400 ; x from bow
S = P.SCALE
F = T.copy(); F *= S; F[:, :, 2] -= 1400.0
xmin = F[:, :, 0].min()
# x alignment: use the keel tip (z < -1395) leading/trailing edge vs params
kt = F.reshape(-1, 3); kt = kt[kt[:, 2] < -1390.0]
le, te = kt[:, 0].min(), kt[:, 0].max()
off_keel = 0.5 * ((P.KEEL_LE_TIP - le) + (P.KEEL_TE_TIP - te))
print(f"rotation {ANG}: bow min x = {xmin:.1f} (raw), keel tip x {le:.1f}..{te:.1f} (len {te-le:.1f}, params {P.KEEL_TE_TIP-P.KEEL_LE_TIP:.0f})")
print(f"  x offset from keel tip: {off_keel:.1f}  -> bow tip then at x = {xmin+off_keel:.1f}")
F[:, :, 0] += off_keel

def form_y(x, z):
    """formula outer half-breadth at height z (dense polyline of section())"""
    sec = np.array(C.section(x, n=2000))
    # section is monotone in z
    return np.interp(z, sec[:, 1], sec[:, 0], left=np.nan, right=np.nan)

def contour(x, zg):
    seg = slice_x(F, x)
    yp = outer_y_of_z(seg, zg, +1)
    ym = -outer_y_of_z(seg, zg, -1)
    return yp, ym

def fit_lean(zg, y, lo, hi):
    m = (zg >= lo) & (zg <= hi) & np.isfinite(y)
    if m.sum() < 3:
        return np.nan
    b = np.polyfit(zg[m], y[m], 1)[0]
    return math.degrees(math.atan(b))

named = [1192, 1988, 2385, 3180, 3975, 4770, 5565, 5962, 6360, 6758, 7155, 7552]
zg = np.arange(-600.0, 1250.0, 2.0)
print(f"\n{'x':>6} {'lean[-60,-5]':>12} {'lean[5,60]':>10} {'lean[250,400]':>13} | STL-formula: {'below':>6} {'0..300':>6} {'300..strk-60':>12} | chordDev STL {'formula':>7}")
rows = {}
for x in named:
    yp, ym = contour(x, zg)
    y = 0.5 * (yp + ym)
    asym = np.nanmax(np.abs(yp - ym))
    fy = form_y(x, zg)
    zb, zs, zk = C.bottom_z(x), C.sheer_z(x), C.strake_z(x)
    l1 = fit_lean(zg, y, -60, -5); l2 = fit_lean(zg, y, 5, 60); l3 = fit_lean(zg, y, 250, 400)
    d = y - fy
    def mx(lo, hi):
        m = (zg >= lo) & (zg <= hi) & np.isfinite(d)
        return float(d[m][np.argmax(np.abs(d[m]))]) if m.any() else np.nan
    dbel = mx(zb + 20, -2); d03 = mx(2, 300); dup = mx(300, zk - 60)
    # topside chord deviation measured in the STL: chord from STL y at z=0 to formula deck edge (bd, zs)
    bd = C.deck_half_breadth(x)
    y0 = np.interp(0.0, zg, y)
    m = (zg > 0) & (zg < zk - 60) & np.isfinite(y)
    chord = y0 + (bd - y0) * zg[m] / zs
    dev_stl = (y[m] - chord)
    # formula chord deviation (horizontal), same z-range
    fch = fy[m] - (fy[np.argmin(np.abs(zg))] + (bd - fy[np.argmin(np.abs(zg))]) * zg[m] / zs)
    rows[x] = dict(lean_below=l1, lean_above=l2, lean_250_400=l3, d_below=dbel, d_0_300=d03, d_300_up=dup,
                   chord_stl=float(dev_stl.min()), chord_form=float(fch.min()), asym=float(asym))
    print(f"{x:6.0f} {l1:12.1f} {l2:10.1f} {l3:13.1f} | {dbel:12.1f} {d03:6.1f} {dup:12.1f} | {dev_stl.min():8.1f} {fch.min():7.1f}   asym {asym:.1f}")

# all loft stations and midpoints: max |STL - formula| below DWL and 0..strake-60
xs = json.load(open(HERE + "/v_formula.json"))["loft_x"]
mids = [0.5 * (a + b) for a, b in zip(xs[:-1], xs[1:])]
print("\nloft stations + midpoints: max |STL - formula| (mm full scale), underwater / topside (z 20..strake-60)")
worst = []
for x in sorted(xs + mids):
    if x < 150 or x > 7700:
        continue
    yp, ym = contour(x, zg)
    y = 0.5 * (yp + ym)
    fy = form_y(x, zg)
    zb, zk = C.bottom_z(x), C.strake_z(x)
    d = y - fy
    mu = (zg > max(zb, -560) + 25) & (zg < -2) & np.isfinite(d)
    mt = (zg > 20) & (zg < zk - 60) & np.isfinite(d)
    # exclude the window recess band
    if 3650 < x < 4950:
        mt &= ~((zg > zk + 0) & (zg < zs + 10)) if False else mt
    du = float(d[mu][np.argmax(np.abs(d[mu]))]) if mu.any() else np.nan
    dt = float(d[mt][np.argmax(np.abs(d[mt]))]) if mt.any() else np.nan
    tag = "loft" if x in xs else "mid "
    worst.append((x, du, dt))
    print(f"  {tag} x={x:7.1f}  under {du:7.1f}  top {dt:7.1f}")
json.dump(dict(rows=rows, worst=worst, x_off=off_keel), open(HERE + f"/v_stl_ours_{int(ANG)}.json", "w"), indent=1, default=float)
