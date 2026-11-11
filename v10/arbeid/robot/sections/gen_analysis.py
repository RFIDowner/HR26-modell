"""Lens: cross-sections. Analyse hr26.curves.section() and the OCC spline built from it.
Read-only use of the repo (imports only). Full-scale mm everywhere."""
import sys, json, math
import numpy as np
REPO = r"C:/Users/stig/Documents/GitHub/HR26-modell"
sys.path.insert(0, REPO)
from hr26 import curves as C, params as P
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.gp import gp_Pnt, gp_Vec

OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/sections"
N_PTS = 26   # build.py build_hull(n_pts=26)
FR = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def spline_eval(x, pts, n=4000):
    e = cq.Edge.makeSpline([cq.Vector(x, y, z) for (y, z) in pts])
    ad = BRepAdaptor_Curve(e.wrapped)
    u0, u1 = ad.FirstParameter(), ad.LastParameter()
    us = np.linspace(u0, u1, n)
    Y, Z, K, A = [], [], [], []
    for u in us:
        p = gp_Pnt(); v1 = gp_Vec(); v2 = gp_Vec()
        ad.D2(u, p, v1, v2)
        y1, z1, y2, z2 = v1.Y(), v1.Z(), v2.Y(), v2.Z()
        Y.append(p.Y()); Z.append(p.Z())
        # signed curvature: + = left turn walking keel -> deck (convex bilge), - = right turn (hollow)
        K.append((y1 * z2 - z1 * y2) / max((y1 * y1 + z1 * z1) ** 1.5, 1e-30))
        A.append(math.degrees(math.atan2(y1, z1)))   # tangent angle from vertical, + = leaning outward
    # knot/interp params: find parameter of each interpolation point
    return np.array(Y), np.array(Z), np.array(K), np.array(A), us


def analytic(x, n=6000):
    """Same formulas as curves.section(), densely sampled (no spline)."""
    return np.array(C.section(x, n=n))


def info(x):
    zb, zs, bd = C.bottom_z(x), C.sheer_z(x), C.deck_half_breadth(x)
    bw_raw = C.wl_half_breadth(x)
    m = max(C.fullness(x), 1.02)
    bw = min(bw_raw, bd) if zb < -1.0 else min(bw_raw * 0.55, bd * 0.75)
    return dict(zb=zb, zs=zs, bd=bd, bw=bw, m=m, zk=C.strake_z(x), branch="uw" if zb < -1.0 else "stem")


rows = []
for f in FR:
    x = f * P.LOA
    I = info(x)
    pts = np.array(C.section(x, n=N_PTS))
    npt = len(pts)
    Y, Z, K, A, us = spline_eval(x, pts)
    zb, zs, bd, bw, m = I["zb"], I["zs"], I["bd"], I["bw"], I["m"]
    r = dict(f=f, x=round(x), **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in I.items()}, npts=npt)
    # spacing of input points just below/above DWL
    if I["branch"] == "uw":
        iw = int(np.argmin(np.abs(pts[:, 1])))           # DWL point index
        r["iw"] = iw
        r["dz_below"] = round(pts[iw, 1] - pts[iw - 1, 1], 1)
        r["dz_above"] = round(pts[iw + 1, 1] - pts[iw, 1], 1)
        # chord angles of the polyline segments either side of DWL (deg from vertical)
        sb = pts[iw] - pts[iw - 1]; sa = pts[iw + 1] - pts[iw]
        r["chord_ang_below"] = round(math.degrees(math.atan2(sb[0], sb[1])), 1)
        r["chord_ang_above"] = round(math.degrees(math.atan2(sa[0], sa[1])), 1)
        # spline tangent angle at DWL and curvature profile around it
        j = int(np.argmin(np.abs(Z)))
        r["spl_ang_at_dwl"] = round(A[j], 1)
        # tangent angle 30 mm below and above DWL on the spline
        for dz in (-100, -30, 30, 100):
            jj = int(np.argmin(np.abs(Z - dz)))
            r[f"spl_ang_{dz:+d}"] = round(A[jj], 1)
            r[f"spl_R_{dz:+d}"] = round(1.0 / K[jj], 0) if abs(K[jj]) > 1e-9 else None
        # analytic tangent angle & curvature from the dense formula
        an = analytic(x)
        da = np.gradient(an, axis=0)
        d2 = np.gradient(da, axis=0)
        ka = (da[:, 0] * d2[:, 1] - da[:, 1] * d2[:, 0]) / np.maximum((da[:, 0] ** 2 + da[:, 1] ** 2) ** 1.5, 1e-30)
        aa = np.degrees(np.arctan2(da[:, 0], da[:, 1]))
        for dz in (-100, -30, -10, 10, 30, 100):
            jj = int(np.argmin(np.abs(an[:, 1] - dz)))
            r[f"an_ang_{dz:+d}"] = round(aa[jj], 1)
            r[f"an_R_{dz:+d}"] = round(1.0 / ka[jj], 0) if abs(ka[jj]) > 1e-9 else None
        # inflection points of the spline (sign changes of curvature), z positions
        sgn = np.sign(K); ch = np.nonzero(np.diff(sgn) != 0)[0]
        r["spline_inflections_z"] = [round(float(Z[c]), 0) for c in ch if abs(Z[c] - zb) > 5]
        # bilge: tangent angle from horizontal = 90 - A ; turn from 20..70 deg from horizontal
        below = Z <= 0.0
        ah = 90.0 - A
        sel = below & (ah >= 20) & (ah <= 70)
        if sel.sum() > 3:
            s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(Y[sel]), np.diff(Z[sel])))])
            r["bilge_R_mean_20_70"] = round(s[-1] / math.radians(ah[sel].max() - ah[sel].min()), 0)
            j45 = np.nonzero(below)[0][np.argmin(np.abs(ah[below] - 45))]
            r["z_at_45deg"] = round(float(Z[j45]), 0)
            r["R_at_45deg"] = round(1 / K[j45], 0)
        kb = K[below & (Z > zb + 0.3 * abs(zb))]
        r["R_min_below_dwl"] = round(1 / kb.max(), 0) if kb.max() > 0 else None
        r["z_of_R_min"] = round(float(Z[below & (Z > zb + 0.3 * abs(zb))][np.argmax(kb)]), 0)
        # how much turning (deg) happens within 150 mm below DWL vs whole bilge
        jb = below & (Z > -150)
        r["turn_last150_below_deg"] = round(float(ah[jb].max() - ah[jb].min()), 1)
        r["turn_total_below_deg"] = round(float(ah[below].max() - ah[below].min()), 1)
        # topsides: WL point -> deck edge
        top = Z >= 0.0
        y0, z0 = Y[top][0], Z[top][0]
    else:
        top = np.ones_like(Z, bool)
        y0, z0 = Y[0], Z[0]
        r["spline_inflections_z"] = []
    # straightness of topsides w.r.t. chord (WL/stem point -> deck edge); + = convex (outside chord)
    yt, zt = Y[top], Z[top]
    cy, cz = bd - y0, zs - z0
    L = math.hypot(cy, cz)
    nrm = np.array([cz, -cy]) / L                       # outward normal of chord
    dev = (yt - y0) * nrm[0] + (zt - z0) * nrm[1]
    jmax = int(np.argmax(np.abs(dev)))
    r["topside_dev_mm"] = round(float(dev[jmax]), 1)
    r["topside_dev_at_z"] = round(float(zt[jmax]), 0)
    r["topside_dev_model_mm"] = round(float(dev[jmax]) / P.SCALE, 2)
    r["chord_flare_deg"] = round(math.degrees(math.atan2(cy, cz)), 1)
    r["flare_deck_spline_deg"] = round(A[-1], 1)
    r["flare_deck_analytic_deg"] = round(math.degrees(math.atan(1.45 * (bd - y0) / (zs - z0))), 1)
    # topside curvature: inflections above DWL
    kt = K[top]
    r["topside_R_min_mm"] = round(1 / np.abs(kt[5:-5]).max(), 0)
    # hull half-breadth at strake centre and strake outer face vs deck edge
    yk = float(np.interp(I["zk"], Z, Y))
    r["y_at_strake"] = round(yk, 0)
    r["strake_face_minus_deck"] = round(yk + P.STRAKE_PROUD - bd, 0)
    rows.append(r)

json.dump(rows, open(OUT + "/gen_rows.json", "w"), indent=1)
keys = ["f", "x", "branch", "zb", "zs", "zk", "bd", "bw", "m", "dz_below", "dz_above", "chord_ang_below", "chord_ang_above",
        "spl_ang_at_dwl", "spl_ang_-30", "spl_ang_+30", "an_R_-30", "an_R_-10", "an_R_+10", "an_R_+30", "spl_R_-30", "spl_R_+30",
        "spline_inflections_z", "turn_last150_below_deg", "turn_total_below_deg", "bilge_R_mean_20_70", "z_at_45deg", "R_min_below_dwl", "z_of_R_min",
        "topside_dev_mm", "topside_dev_at_z", "topside_dev_model_mm", "chord_flare_deg", "flare_deck_spline_deg", "flare_deck_analytic_deg",
        "topside_R_min_mm", "y_at_strake", "strake_face_minus_deck"]
for k in keys:
    print(f"{k:>26s}: " + " | ".join(str(r.get(k, "-")) for r in rows))

# loft stations used by build (n_stations=40)
xs = C.stations(40)
xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
xs = sorted(set([4.0] + xs + [7850.0, 7910.0] + [P.LOA - 2.0]))
xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0]
print("loft stations", len(xs), [round(v) for v in xs])
print("branch per loft station:", ["S" if C.bottom_z(v) >= -1 else "U" for v in xs])
print("zb around LWL_FWD:", [(v, round(C.bottom_z(v), 1)) for v in (900, 1000, 1007.9, 1008.1, 1050, 1100, 1200)])
print("bw around LWL_FWD:", [(v, round(C.wl_half_breadth(v), 1)) for v in (1008.1, 1050, 1100, 1200, 1400)])
print("displaced volume (code) m3:", round(C.displaced_volume_m3(), 3))
