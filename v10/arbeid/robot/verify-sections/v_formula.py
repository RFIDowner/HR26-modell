"""Independent check of curves.section(): analytic curvature, topside chord
deviation, and the OCC spline (as hull._section_wire builds it).
Reads the user's repo read-only (import only)."""
import sys, math, json
import numpy as np
sys.path.insert(0, r"C:/Users/stig/Documents/GitHub/HR26-modell")
from hr26 import curves as C, params as P
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.gp import gp_Pnt, gp_Vec

LOA = P.LOA
named = [398, 1192, 1988, 2385, 3180, 3975, 4770, 5565, 5962, 6360, 6758, 7155, 7552]

def form(x):
    zb = C.bottom_z(x); zs = C.sheer_z(x); bd = max(C.deck_half_breadth(x), 1e-3)
    m = max(C.fullness(x), 1.02)
    bw = min(C.wl_half_breadth(x), bd) if zb < -1 else min(C.wl_half_breadth(x) * 0.55, bd * 0.75)
    return zb, zs, bd, bw, m

def y_under(z, zb, bw, m):           # z in [zb, 0]
    u = np.clip(z / zb, 0, 1)
    return bw * np.clip(1 - u ** m, 0, None) ** (1 / m)

def y_top(z, zs, bd, bw):            # z in [0, zs]
    s = np.clip(z / zs, 0, 1)
    return bw + (bd - bw) * s ** 1.45

def kappa_yz(y, z):
    """signed curvature of planar polyline, + = turning left (convex bilge
    when walking keel -> deck), - = hollow"""
    dy = np.gradient(y); dz = np.gradient(z)
    ddy = np.gradient(dy); ddz = np.gradient(dz)
    return (dy * ddz - dz * ddy) / np.maximum((dy * dy + dz * dz) ** 1.5, 1e-30)

out = {}
print("ANALYTIC (formula)")
print(f"{'x':>6} {'zb':>7} {'zs':>6} {'bd':>6} {'bw':>6} {'bw/bd':>6} {'m':>5} {'R(-10)':>8} {'R(+10)':>9} {'chordDev':>8} {'zDev':>5} {'flDeck':>6} {'flChord':>7}")
for x in named:
    zb, zs, bd, bw, m = form(x)
    rec = dict(zb=zb, zs=zs, bd=bd, bw=bw, m=m)
    if zb < -1:
        # analytic: curvature of y(z) graph, kappa = y''/(1+y'^2)^1.5 ; convex if y''<0
        def R_at(z, f):
            h = 0.01
            y0, yp, ym = f(z), f(z + h), f(z - h)
            d1 = (yp - ym) / (2 * h); d2 = (yp - 2 * y0 + ym) / h ** 2
            k = -d2 / (1 + d1 * d1) ** 1.5      # + convex
            return 1 / k
        Rm = R_at(-10.0, lambda z: y_under(z, zb, bw, m))
        Rp = R_at(10.0, lambda z: y_top(z, zs, bd, bw))
        zz = np.linspace(0, zs, 4001); yy = y_top(zz, zs, bd, bw)
        chord = bw + (bd - bw) * zz / zs
        dev = yy - chord; i = np.argmin(dev)
        fl_deck = math.degrees(math.atan((bd - bw) * 1.45 / zs))
        fl_ch = math.degrees(math.atan((bd - bw) / zs))
        rec.update(R_m10=Rm, R_p10=Rp, chord_dev=float(dev[i]), z_dev=float(zz[i]), fl_deck=fl_deck, fl_chord=fl_ch)
        print(f"{x:6.0f} {zb:7.1f} {zs:6.0f} {bd:6.0f} {bw:6.0f} {bw/bd:6.3f} {m:5.2f} {Rm:8.1f} {Rp:9.1f} {dev[i]:8.1f} {zz[i]:5.0f} {fl_deck:6.1f} {fl_ch:7.1f}")
    else:
        # stem branch: y = bd*t^1.45 from (0,zb) to (bd,zs)
        zz = np.linspace(zb, zs, 4001); s = (zz - zb) / (zs - zb)
        yy = bd * s ** 1.45; chord = bd * s
        dev = yy - chord; i = np.argmin(dev)
        rec.update(chord_dev=float(dev[i]), z_dev=float(zz[i]))
        print(f"{x:6.0f} {zb:7.1f} {zs:6.0f} {bd:6.0f}  stem branch  chordDev {dev[i]:.1f} at z {zz[i]:.0f}  flare at deck {math.degrees(math.atan(bd*1.45/(zs-zb))):.1f}")
    out[x] = rec

# ---- OCC spline exactly as hull._section_wire (makeSpline through C.section(x, n=26))
print("\nOCC SPLINE (n_pts=26, default parametrisation)")
print(f"{'x':>6} {'npts':>4} {'Rmin':>7} {'zRmin':>6} {'turn<0':>6} {'turn150':>7} {'z45':>6} {'DWLlean':>7} {'maxOut':>6} {'zOut':>5} {'nInfl':>5} {'zInfl'}")
spl = {}
for x in named:
    pts = C.section(x, n=26)
    zb, zs, bd, bw, m = form(x)
    e = cq.Edge.makeSpline([cq.Vector(x, y, z) for (y, z) in pts])
    ad = BRepAdaptor_Curve(e.wrapped)
    u0, u1 = ad.FirstParameter(), ad.LastParameter()
    us = np.linspace(u0, u1, 20001)
    Y = np.empty_like(us); Z = np.empty_like(us); K = np.empty_like(us); ANG = np.empty_like(us)
    p = gp_Pnt(); v1 = gp_Vec(); v2 = gp_Vec()
    for j, u in enumerate(us):
        ad.D2(u, p, v1, v2)
        Y[j], Z[j] = p.Y(), p.Z()
        y1, z1, y2, z2 = v1.Y(), v1.Z(), v2.Y(), v2.Z()
        K[j] = (y1 * z2 - z1 * y2) / (y1 * y1 + z1 * z1) ** 1.5
        ANG[j] = math.degrees(math.atan2(z1, y1))      # 0 = horizontal outward, 90 = vertical up
    rec = dict(npts=len(pts))
    # inflections: sign changes of K ignoring tiny |K|
    sgn = np.sign(np.where(np.abs(K) < 1e-7, 0, K))
    nz = np.nonzero(sgn)[0]
    infl = [float(Z[nz[i]]) for i in range(1, len(nz)) if sgn[nz[i]] != sgn[nz[i - 1]]]
    if zb < -1:
        below = Z < 0
        jmax = np.argmax(np.where(below, K, -1))
        Rmin = 1 / K[jmax]
        # tangent angle at start and at DWL
        jw = np.argmin(np.abs(Z))
        turn_total = ANG[jw] - ANG[0]
        j150 = np.argmin(np.abs(Z + 150))
        turn150 = ANG[jw] - ANG[j150]
        # 45 deg point
        j45 = np.argmin(np.abs(ANG - 45)); z45 = Z[j45]
        dwl_lean = 90 - ANG[jw]
        # spline vs formula above DWL
        above = (Z > 0) & (Z < zs)
        dev = Y[above] - y_top(Z[above], zs, bd, bw)
        jo = np.argmax(dev)
        # spline vs formula below DWL
        bl = (Z < 0) & (Z > zb)
        devb = Y[bl] - y_under(Z[bl], zb, bw, m)
        rec.update(Rmin=Rmin, zRmin=float(Z[jmax]), turn_total=turn_total, turn150=turn150, z45=float(z45),
                   dwl_lean=dwl_lean, max_out_above=float(dev[jo]), z_out=float(Z[above][jo]),
                   max_abs_below=float(np.abs(devb).max()), infl=infl,
                   dev_above_300=float(np.abs(dev[Z[above] > 300]).max()))
        print(f"{x:6.0f} {len(pts):4d} {Rmin:7.1f} {Z[jmax]:6.1f} {turn_total:6.1f} {turn150:7.1f} {z45:6.0f} {dwl_lean:7.1f} {dev[jo]:6.1f} {Z[above][jo]:5.0f} {len(infl):5d} {[round(v) for v in infl]}  |below dev|max {np.abs(devb).max():.1f}  |dev z>300| {rec['dev_above_300']:.2f}")
    else:
        print(f"{x:6.0f} {len(pts):4d} stem branch; inflections {len(infl)} at {[round(v) for v in infl]}")
        rec.update(infl=infl)
    spl[x] = rec

# point spacing around the DWL for one station
for x in (3975, 7155):
    pts = np.array(C.section(x, n=26))
    i0 = np.argmin(np.abs(pts[:, 1]))
    d = np.hypot(*np.diff(pts, axis=0).T)
    print(f"x={x}: point spacing below DWL (last 4): {np.round(d[i0-4:i0],1)}; above (first 3): {np.round(d[i0:i0+3],1)}")

# bottom_z step at LWL_FWD and loft station classification
print("\nbottom_z(1007.9) =", C.bottom_z(1007.9), " bottom_z(1008.1) =", C.bottom_z(1008.1))
xs = C.stations(40); xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
xs = sorted(set([4.0] + xs + [7850.0, 7910.0] + [P.LOA - 2.0]))
xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0]
nst = sum(1 for x in xs if C.bottom_z(x) >= -1.0)
print("loft stations:", len(xs), " stem-branch:", nst, " underwater-branch:", len(xs) - nst)
print("stations near forefoot:", [round(x) for x in xs if 700 < x < 1600])
print("displaced_volume_m3 =", C.displaced_volume_m3())
json.dump(dict(formula=out, spline=spl, loft_x=xs), open(r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-sections/v_formula.json", "w"), indent=1, default=float)
