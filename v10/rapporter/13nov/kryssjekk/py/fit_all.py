"""Feasibility fit (numeric, no CAD): can one section family satisfy at the
same time (a) IMG_9391 row bands (zc5 camera, as verify-undervann), (b) the
448-5 plan dash-dot line as a LEVEL line at a free height h, (c) DEPL: canoe
body ~2.05 m3 at z -26, (d) canoe LCB ~4600, (e) unchanged topsides (silL)?
Starts from V1; free: deadrise at t .30/.45/.60/.75/.90, N at .30/.45/.80,
midship deadwood H and W.

usage: python fit_all.py <s4_stage> out.json [line_weight]
"""
import sys, json, importlib, time
sys.dont_write_bytecode = True
S4, OUTF = sys.argv[1], sys.argv[2]
LW = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
sys.path.insert(0, S4)
from hr26 import params as P, curves as C
UPY = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/undervann/py"
KK = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/"
sys.path.insert(1, UPY)
import numpy as np
from scipy.optimize import least_squares
import common as c, uwlib as U
import photos as PH

cam = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
sil = json.load(open(c.W + "/out/sil9391.json")); silL = np.array(sil["left"])[:, :2]
tr = json.load(open(KK + "out/dashdot_trace.json"))
dd = np.array(tr["stb"] + tr["port"]); dd[:, 1] = np.abs(dd[:, 1])
LX = [3750, 4000, 4250, 4500, 4750, 5000, 5250]
LY = [float(np.median(dd[(dd[:, 0] >= x - 60) & (dd[:, 0] <= x + 60), 1])) for x in LX]


def z_at(x, y):
    p = C._section_geom(float(x))["pts"]
    for i in range(len(p) - 1):
        if (p[i, 0] - y) * (p[i + 1, 0] - y) <= 0 and p[i + 1, 0] != p[i, 0]:
            t = (y - p[i, 0]) / (p[i + 1, 0] - p[i, 0]); return float(p[i, 1] + t * (p[i + 1, 1] - p[i, 1]))
    return 0.0


def hydro(z0):
    xa = np.linspace(500.0, P.LOA, 1500); bz = np.array([C.bottom_z(v) for v in xa])
    i0 = int(np.argmax(bz < z0)); x_fwd = float(np.interp(z0, [bz[i0], bz[i0 - 1]], [xa[i0], xa[i0 - 1]]))
    xs = np.linspace(x_fwd, P.LOA, 140); area = []
    for x in xs:
        p = C._section_geom(float(x))["pts"]
        if p[0, 1] >= z0 - 0.5:
            area.append(0.0); continue
        zz = np.linspace(p[0, 1], z0, 80); mono = np.maximum.accumulate(p[:, 1])
        yy = np.interp(zz, mono, p[:, 0]); keep = x <= np.array([C.transom_x(float(z), 0.0) for z in zz])
        area.append(2.0 * float(np.trapezoid(np.where(keep, yy, 0.0), zz)))
    area = np.array(area)
    return float(np.trapezoid(area, xs)) / 1e9, float(np.trapezoid(area * xs, xs) / np.trapezoid(area, xs))


B = dict(SECTION_N=list(P.SECTION_N), SECTION_DEADRISE=list(P.SECTION_DEADRISE), DEADWOOD_H=list(P.DEADWOOD_H), DEADWOOD_W=P.DEADWOOD_W)


def apply(q):
    d30, d45, d60, d75, d90, n30, n45, n80, dwh, dww = q
    P.SECTION_DEADRISE = [(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, d30), (0.45, d45), (0.60, d60), (0.75, d75), (0.90, d90), (1.00, 3.0)]
    P.SECTION_N = [(0.00, 2.4), (0.15, 3.1), (0.30, n30), (0.45, n45), (0.80, n80), (1.00, 4.2)]
    P.DEADWOOD_H = [(2900.0, 0.0), (3600.0, dwh), (5900.0, max(dwh, 0.0)), (6800.0, max(dwh, 100.0)), (7400.0, 170.0), (7800.0, 210.0), (8000.0, 210.0)]
    P.DEADWOOD_W = [(3600.0, dww), (5900.0, dww), (6800.0, 120.0)]
    global C
    C = importlib.reload(sys.modules["hr26.curves"]); c.C = C; U.c.C = C


def evaluate(q, full=False):
    apply(q)
    V, F = PH.mesh()
    lo, _ = U.row_extents(cam, V, F, PH.L91[:, 0]); _, hi = U.row_extents(cam, V, F, PH.R91[:, 0])
    eL, eR = PH.L91[:, 1] - lo, hi - PH.R91[:, 1]
    bands = []
    for arr, rows in ((eL, PH.L91[:, 0]), (eR, PH.R91[:, 0])):
        for r0, r1 in ((755, 800), (800, 870), (870, 945)):
            m = (rows >= r0) & (rows < r1)
            bands.append(float(arr[m].mean()) if m.any() else 0.0)
    lo2, _ = U.row_extents(cam, V, F, silL[:, 0])
    s = lo2 - silL[:, 1]; sil600 = float(s[silL[:, 0] >= 600].mean())
    zl = np.array([z_at(x, y) for x, y in zip(LX, LY)])
    v26, lcb = hydro(-26.0)
    if full:
        return dict(bands=[round(b, 1) for b in bands], rmsL=round(float(np.sqrt(np.mean(eL ** 2))), 1),
                    rmsR=round(float(np.sqrt(np.mean(eR ** 2))), 1), sil600=round(sil600, 1),
                    line_z=[round(float(v)) for v in zl], line_h=round(float(zl.mean())), line_sd=round(float(zl.std()), 1),
                    vol26=round(v26, 3), lcb=round(lcb))
    r = list(np.array(bands) / 6.0) + [sil600 / 3.0] + list(LW * (zl - zl.mean()) / 15.0) + [(v26 - 2.05) / 0.05, (lcb - 4600.0) / 50.0]
    dq = np.diff([q[0], q[1], q[2], q[3], q[4]]) / 20.0
    return np.array(r + list(dq))


q0 = np.array([4.0, 6.0, 16.0, 26.0, 15.0, 3.4, 4.5, 4.5, 80.0, 200.0])      # V1
lb = np.array([0.0, 0.0, 0.0, 5.0, 3.0, 2.6, 2.6, 2.6, 0.0, 120.0])
ub = np.array([30.0, 30.0, 35.0, 40.0, 35.0, 5.0, 5.0, 5.0, 180.0, 400.0])
t0 = time.time()
print("V1 start:", evaluate(q0, True), flush=True)
sol = least_squares(evaluate, q0, bounds=(lb, ub), diff_step=0.02, max_nfev=120, verbose=0)
q = sol.x
res = dict(params=dict(zip(["dr30", "dr45", "dr60", "dr75", "dr90", "n30", "n45", "n80", "dw_h_mid", "dw_w_mid"], [round(float(v), 2) for v in q])),
           metrics=evaluate(q, True), cost=float(sol.cost), nfev=int(sol.nfev), line_weight=LW, t=round(time.time() - t0))
print(json.dumps(res, indent=0), flush=True)
json.dump(res, open(OUTF, "w"), indent=1)
