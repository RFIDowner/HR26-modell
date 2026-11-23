"""Proposed section family, numpy only (no CAD).  Full-scale mm, z from DWL, y half-breadth.

  Corner C = intersection of the bottom line through K=(0,zb) (direction ub=(cos b, sin b), b = deadrise)
             and the side line through D=(bd,zs) (direction us=(sin phi, cos phi), phi = flare at deck edge)
  K = C - a*ub,  D = C + c*us
  P(t) = C - a*(1 - f)*ub + c*(1 - g)*us,   f = sin(t)^(2/n),  g = cos(t)^(2/n),  t in [0, pi/2]
  i.e. the corner rounded by a superellipse |f|^n + |g|^n = 1 drawn in the skew frame (affine map):
  convex for n >= 1, C-infinity inside, zero curvature at both ends for n > 2 (flat floor at the keel,
  straight run into the deck edge).  n is solved per station so the curve passes the WL point (bw, 0).
"""
import sys, math, json
import numpy as np
sys.path.insert(0, r"C:/Users/stig/Documents/GitHub/HR26-modell")
from hr26 import curves as C, params as P
from scipy.interpolate import PchipInterpolator

OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/sections"
FR = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

# ---- smooth parameter tables (fraction of LOA) -> PCHIP (C1, no overshoot); deg
PHI_T = [(0.00, 24.0), (0.10, 19.0), (0.20, 14.5), (0.30, 11.5), (0.45, 9.5), (0.60, 8.5),
         (0.72, 6.0), (0.82, 3.0), (0.90, 1.5), (1.00, 1.5)]          # flare at deck edge
BETA_T = [(0.00, 50.0), (0.127, 30.0), (0.20, 14.0), (0.30, 5.0), (0.40, 0.0), (1.00, 0.0)]  # deadrise at keel
N_FWD = [(0.00, 2.0), (0.127, 2.2)]                                     # fullness where there is no WL point
phi_f = PchipInterpolator([p[0] for p in PHI_T], [p[1] for p in PHI_T])
beta_f = PchipInterpolator([p[0] for p in BETA_T], [p[1] for p in BETA_T])


def frame(x, phi=None, beta=None):
    zb, zs, bd = C.bottom_z(x), C.sheer_z(x), C.deck_half_breadth(x)
    phi = math.radians(float(phi_f(x / P.LOA)) if phi is None else phi)
    beta = math.radians(float(beta_f(x / P.LOA)) if beta is None else beta)
    ub = np.array([math.cos(beta), math.sin(beta)]); us = np.array([math.sin(phi), math.cos(phi)])
    K = np.array([0.0, zb]); D = np.array([bd, zs])
    # K + a ub = D - c us  ->  a ub + c us = D - K
    A = np.array([[ub[0], us[0]], [ub[1], us[1]]])
    a, c = np.linalg.solve(A, D - K)
    Cc = K + a * ub
    return K, D, Cc, a, c, ub, us


def curve(x, n, m=600, phi=None, beta=None):
    K, D, Cc, a, c, ub, us = frame(x, phi, beta)
    t = np.linspace(0.0, math.pi / 2, m)
    f = np.sin(t) ** (2.0 / n); g = np.cos(t) ** (2.0 / n)
    Pp = Cc[None, :] - (a * (1 - f))[:, None] * ub[None, :] + (c * (1 - g))[:, None] * us[None, :]
    return Pp


def y_at(Pp, z):
    i = np.argsort(Pp[:, 1])
    return float(np.interp(z, Pp[i, 1], Pp[i, 0]))


def solve_n(x, bw, lo=1.05, hi=12.0):
    if C.bottom_z(x) >= -1.0 or bw <= 1.0:
        return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if y_at(curve(x, mid, 400), 0.0) < bw:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def bw_current(x):
    zb = C.bottom_z(x)
    return min(C.wl_half_breadth(x), C.deck_half_breadth(x)) if zb < -1.0 else 0.0


def metrics(Pp, x):
    """tangent angle from vertical, curvature, topside chord deviation, bilge radius, strake."""
    d1 = np.gradient(Pp, axis=0); d2 = np.gradient(d1, axis=0)
    k = (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.maximum((d1 ** 2).sum(1) ** 1.5, 1e-30)
    ang = np.degrees(np.arctan2(d1[:, 0], d1[:, 1]))
    Z = Pp[:, 1]; Y = Pp[:, 0]
    zs, bd, zk = C.sheer_z(x), C.deck_half_breadth(x), C.strake_z(x)
    out = {}
    if Z.min() < 0:
        y0 = y_at(Pp, 0.0)
        top = Z >= 0
        j0 = int(np.argmin(np.abs(Z)))
        out["flare_at_WL"] = round(float(ang[j0]), 1)
    else:
        y0 = Y[0]; top = np.ones_like(Z, bool)
        out["flare_at_WL"] = None
    z0 = max(Z.min(), 0.0)
    cy, cz = bd - y0, zs - z0; L = math.hypot(cy, cz); nrm = np.array([cz, -cy]) / L
    dev = (Y[top] - y0) * nrm[0] + (Z[top] - z0) * nrm[1]
    out["topside_dev"] = round(float(dev[np.argmax(np.abs(dev))]), 1)
    out["flare_deck"] = round(float(ang[-1]), 1)
    out["inflections"] = int(((np.diff(np.sign(k[3:-3])) != 0)).sum())
    ah = 90.0 - ang
    j45 = int(np.argmin(np.abs(ah - 45.0)))
    out["z_45"] = round(float(Z[j45]), 0)
    out["R_45"] = round(float(1.0 / k[j45]), 0)
    kk = k[3:-3]
    out["R_min"] = round(float(1.0 / kk.max()), 0)
    out["z_Rmin"] = round(float(Z[3:-3][np.argmax(kk)]), 0)
    yk = y_at(Pp, zk)
    out["y_strake"] = round(yk, 0)
    out["strake_face_minus_deck"] = round(yk + P.STRAKE_PROUD - bd, 0)
    out["y_WL"] = round(y0, 1)
    return out


def area_below_dwl(Pp):
    Z = Pp[:, 1]
    if Z.min() >= 0:
        return 0.0
    i = np.argsort(Z)
    zz = np.linspace(Z.min(), 0.0, 200)
    yy = np.interp(zz, Z[i], Pp[i, 0])
    return 2.0 * float(np.trapezoid(yy, zz))


def area_current(x):
    zb = C.bottom_z(x)
    if zb >= -1.0:
        return 0.0
    bw = min(C.wl_half_breadth(x), C.deck_half_breadth(x)); m = max(C.fullness(x), 1.02)
    zz = np.linspace(zb, 0.0, 200); t = 1.0 - zz / zb
    f = np.clip(1.0 - (1.0 - t) ** m, 0.0, None)
    return 2.0 * float(np.trapezoid(bw * f ** (1.0 / m), zz))


if __name__ == "__main__":
    # 1) solve n per station along the hull (dense) so the curve passes (bw, 0)
    xs = np.arange(1050.0, 7801.0, 25.0)
    n_raw = np.array([solve_n(x, bw_current(x)) for x in xs], dtype=float)
    # 2) smooth n(x): cubic fit in x (keeps the loft fair) -> bw then deviates a little from the table
    cf = np.polyfit(xs / P.LOA, n_raw, 4)
    n_s = np.polyval(cf, xs / P.LOA)
    print("n raw range", np.nanmin(n_raw).round(2), np.nanmax(n_raw).round(2), " smooth-fit residual max", np.nanmax(np.abs(n_s - n_raw)).round(2))

    def n_of(x):
        t = x / P.LOA
        if C.bottom_z(x) >= -1.0:
            return float(np.interp(t, [p[0] for p in N_FWD], [p[1] for p in N_FWD]))
        if x < 1050:
            return float(np.polyval(cf, 1050 / P.LOA))
        return float(np.polyval(cf, min(t, 7800 / P.LOA)))

    # forward of the WL entry n is prescribed: blend smoothly into the fit at 1050
    rows = []
    store = {}
    for f in FR:
        x = f * P.LOA
        nn = n_of(x)
        Pp = curve(x, nn)
        r = dict(f=f, x=round(x), phi=round(float(phi_f(f)), 1), beta=round(float(beta_f(f)), 1), n=round(nn, 2))
        nraw = solve_n(x, bw_current(x))
        r["n_exact"] = round(nraw, 2) if nraw else None
        r.update(metrics(Pp, x))
        r["bw_table"] = round(bw_current(x), 1)
        r["dbw_mm"] = round(r["y_WL"] - bw_current(x), 1) if bw_current(x) > 0 else None
        # current section metrics for the same items
        cur = np.array(C.section(x, n=4000))
        rc = metrics(cur, x)
        r["cur_R_min"] = rc["R_min"]; r["cur_z_Rmin"] = rc["z_Rmin"]; r["cur_topside_dev"] = rc["topside_dev"]
        r["cur_flare_deck"] = rc["flare_deck"]; r["cur_inflections"] = rc["inflections"]
        r["cur_y_strake"] = rc["y_strake"]
        r["area_new"] = round(area_below_dwl(Pp) / 1e6, 4); r["area_cur"] = round(area_current(x) / 1e6, 4)
        rows.append(r)
        store[str(f)] = dict(new=Pp.tolist(), cur=cur.tolist())
    keys = ["f", "x", "phi", "beta", "n", "n_exact", "flare_at_WL", "flare_deck", "cur_flare_deck", "topside_dev", "cur_topside_dev",
            "inflections", "cur_inflections", "R_45", "z_45", "R_min", "z_Rmin", "cur_R_min", "cur_z_Rmin",
            "y_WL", "bw_table", "dbw_mm", "y_strake", "cur_y_strake", "strake_face_minus_deck", "area_new", "area_cur"]
    for k in keys:
        print(f"{k:>22s}: " + " | ".join(str(r.get(k, "-")) for r in rows))

    # displacement (canoe body), same integration span as curves.displaced_volume_m3
    xv = np.linspace(P.LWL_FWD, max(P.LWL_AFT, P.TRANSOM_WL_X), 200)
    a_new = np.array([area_below_dwl(curve(x, n_of(x), 300)) for x in xv])
    a_cur = np.array([area_current(x) for x in xv])
    V_new = float(np.trapezoid(a_new, xv)) / 1e9; V_cur = float(np.trapezoid(a_cur, xv)) / 1e9
    print(f"canoe-body volume: current {V_cur:.3f} m3, proposal {V_new:.3f} m3 ({(V_new / V_cur - 1) * 100:+.1f} %)")
    bw_new = np.array([y_at(curve(x, n_of(x), 400), 0.0) if C.bottom_z(x) < -1 else 0.0 for x in xv])
    bw_cur = np.array([bw_current(x) for x in xv])
    print(f"max WL half-breadth: current {bw_cur.max():.0f}, proposal {bw_new.max():.0f} ({(bw_new.max() / bw_cur.max() - 1) * 100:+.1f} %); "
          f"max |dbw| along hull {np.abs(bw_new - bw_cur).max():.1f} mm at x={xv[np.argmax(np.abs(bw_new - bw_cur))]:.0f}")
    print("WL area: current", round(2 * np.trapezoid(bw_cur, xv) / 1e6, 3), "m2  proposal", round(2 * np.trapezoid(bw_new, xv) / 1e6, 3), "m2")
    print("poly coeffs n(t):", np.round(cf, 4).tolist())
    # n at the 15 stations from the fit vs exact
    json.dump(dict(rows=rows, store=store, poly=cf.tolist(), V_cur=V_cur, V_new=V_new), open(OUT + "/proposal.json", "w"))
