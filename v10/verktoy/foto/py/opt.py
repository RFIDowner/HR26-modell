"""Fit aft/mid section shape + deadwood to IMG_9391 (+ IMG_9388 secondary) and a volume prior."""
import sys, json, time; sys.path.insert(0, '.')
import numpy as np
from scipy.optimize import least_squares
import common as c, uwlib as U, cands, dw, photos as PH

XS_TOP = np.arange(300, 7801, 250.0)
def topsides(C):
    out = []
    for x in XS_TOP:
        p = np.array(C.section(float(x), 400)); zs = C.strake_z(float(x))
        m = p[:, 1] >= zs - 30
        out.append(p[m])
    return out
cands.apply()
TOP0 = topsides(c.C)

def top_change(C):
    worst = 0.0
    for x, p0 in zip(XS_TOP, TOP0):
        p = np.array(C.section(float(x), 400))
        y = np.interp(p0[:, 1], p[:, 1], p[:, 0])
        worst = max(worst, float(np.max(np.abs(y - p0[:, 0]))))
    return worst

def build(q, H=None):
    d20, d30, d45, d60, d75, d90, d100, n45, n80, zc68, zc78, wdw = q
    DR = [(0.00, 45.0), (0.127, 15.0), (0.20, d20), (0.30, d30), (0.45, d45), (0.60, d60), (0.75, d75), (0.90, d90), (1.00, d100)]
    SN = [(0.00, 2.4), (0.15, 3.1), (0.30, 3.4), (0.45, n45), (0.80, n80), (1.00, n80 - 0.2)]
    C = cands.apply(CANOE_BOTTOM_HIDDEN=H or cands.hidden_aft("E"), SECTION_DEADRISE=DR, SECTION_N=SN)
    prof = C.bottom_z
    zc_tab = np.array([(5900.0, None), (6800.0, zc68), (7800.0, zc78)], dtype=object)
    def h(x):
        if x <= 5900.0:
            return 0.0
        zp = prof(x)
        zc = np.interp(x, [5900.0, 6800.0, 7800.0, 8000.0], [prof(5900.0), zc68, zc78, zc78])
        return max(0.0, zc - zp)
    dw.install(C, h, lambda x: wdw)
    return C

W91, W88S, W88B, VOLT, VOLS = 1.0, 0.4, 0.3, 2.55, 0.15
def resid(q, parts=False):
    C = build(q)
    V, F = PH.mesh()
    a, b = PH.e9391(V, F); l8, r8, b8 = PH.e9388(V, F)
    vol = U.hydro()["vol"]
    tc = top_change(C)
    d = np.array(q[:7])
    g = dict(e91=np.r_[a, b] * W91 / np.sqrt(len(a) + len(b)) * 5, e88s=np.r_[l8, r8] * W88S / np.sqrt(len(l8) + len(r8)) * 5,
             e88b=b8 * W88B / np.sqrt(len(b8)) * 5, vol=np.array([(vol - VOLT) / VOLS * 10.0]),
             top=np.array([max(0.0, tc - 10.0) * 5.0]), smooth=np.diff(d, 2) * 0.5)
    if parts:
        return g, dict(vol=vol, top=tc, e91=(a, b), e88=(l8, r8, b8))
    return np.concatenate(list(g.values()))

if __name__ == "__main__":
    q0 = [6.0, 10.0, 16.0, 16.0, 16.0, 16.0, 16.0, 3.5, 3.3, -390.0, -300.0, 300.0]
    lb = [0, 0, 0, 0, 0, 0, 0, 2.2, 2.2, -460, -420, 150]
    ub = [30, 35, 35, 40, 45, 50, 55, 6.0, 6.0, -250, -200, 500]
    t0 = time.time()
    r = least_squares(resid, q0, bounds=(lb, ub), x_scale=[2, 2, 2, 2, 2, 2, 2, 0.2, 0.2, 15, 15, 30], diff_step=1e-3, max_nfev=60, loss="soft_l1", f_scale=3.0)
    g, info = resid(r.x, True)
    print("q", np.round(r.x, 2).tolist(), "cost", round(r.cost, 1), "%.0fs" % (time.time() - t0))
    a, b = info["e91"]; l8, r8, b8 = info["e88"]
    f = lambda e: f"{np.mean(e):+6.1f}/{np.sqrt(np.mean(e**2)):5.1f}"
    print("9391 L", f(a), "R", f(b), "| 9388 L", f(l8), "R", f(r8), "bot", f(b8), "| vol %.3f top %.1f" % (info["vol"], info["top"]))
    c.save_json(dict(q=r.x, vol=info["vol"], top=info["top"]), c.W + "/out/opt1.json")
