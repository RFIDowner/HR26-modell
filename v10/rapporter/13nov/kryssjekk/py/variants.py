"""Section-shape variants (numeric, no CAD) on the s4 code (V1 curves.py with
DEADWOOD_W tables): IMG_9391 row bands with the zc5 camera (as in
verify-undervann scan_v1), the 448-5 plan's dash-dot level line (traced, both
sides), hydrostatics at z 0 and -26 vs DEPL 2.36 m3, the 2900/6100 cradle
stations, and the largest change at the strake vs HEAD.

usage: python variants.py <s4_stage> <s0_stage> out.json
"""
import sys, json, importlib, time
sys.dont_write_bytecode = True
S4, S0, OUTF = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, S4)
from hr26 import params as P, curves as C
UPY = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/undervann/py"
KK = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/"
sys.path.insert(1, UPY)
import numpy as np
import common as c, uwlib as U
import photos as PH

cams = json.load(open(c.W + "/out/cam9391.json"))
cam = U.Cam(cams["zc5"]["p"][:7], 1500, 2000)
sil = json.load(open(c.W + "/out/sil9391.json")); silL = np.array(sil["left"])[:, :2]
ro = np.array(json.load(open(c.W + "/out/t9391.json"))["red_outline"])
frows = np.arange(950.0, 1001.0, 5.0)
tr = json.load(open(KK + "out/dashdot_trace.json"))
dd = np.array(tr["stb"] + tr["port"]); dd[:, 1] = np.abs(dd[:, 1])
LX = [3750, 4000, 4250, 4500, 4750, 5000, 5250]
LY = [float(np.median(dd[(dd[:, 0] >= x - 60) & (dd[:, 0] <= x + 60), 1])) for x in LX]

# HEAD tables (s0) for reference
s0p = {}
exec(open(S0 + "/hr26/params.py", encoding="utf-8").read(), s0p)

def hb_at(x, z):
    p = C._section_geom(float(x))["pts"]
    for i in range(len(p) - 1):
        if (p[i, 1] - z) * (p[i + 1, 1] - z) <= 0 and p[i + 1, 1] != p[i, 1]:
            t = (z - p[i, 1]) / (p[i + 1, 1] - p[i, 1]); return float(p[i, 0] + t * (p[i + 1, 0] - p[i, 0]))
    return float("nan")

def z_at(x, y):
    p = C._section_geom(float(x))["pts"]
    for i in range(len(p) - 1):
        if (p[i, 0] - y) * (p[i + 1, 0] - y) <= 0 and p[i + 1, 0] != p[i, 0]:
            t = (y - p[i, 0]) / (p[i + 1, 0] - p[i, 0]); return float(p[i, 1] + t * (p[i + 1, 1] - p[i, 1]))
    return float("nan")

def hydro(z0):
    xa = np.linspace(500.0, P.LOA, 3000); bz = np.array([C.bottom_z(v) for v in xa])
    i0 = int(np.argmax(bz < z0)); x_fwd = float(np.interp(z0, [bz[i0], bz[i0 - 1]], [xa[i0], xa[i0 - 1]]))
    xs = np.linspace(x_fwd, P.LOA, 300); area = []
    for x in xs:
        p = C._section_geom(float(x))["pts"]
        if p[0, 1] >= z0 - 0.5:
            area.append(0.0); continue
        zz = np.linspace(p[0, 1], z0, 160); mono = np.maximum.accumulate(p[:, 1])
        yy = np.interp(zz, mono, p[:, 0]); keep = x <= np.array([C.transom_x(float(z), 0.0) for z in zz])
        area.append(2.0 * float(np.trapezoid(np.where(keep, yy, 0.0), zz)))
    area = np.array(area)
    return float(np.trapezoid(area, xs)) / 1e9, float(np.trapezoid(area * xs, xs) / np.trapezoid(area, xs)), float(area.max()) / 1e6

def metrics():
    V, F = PH.mesh()
    lo, _ = U.row_extents(cam, V, F, PH.L91[:, 0]); _, hi = U.row_extents(cam, V, F, PH.R91[:, 0])
    eL, eR = PH.L91[:, 1] - lo, hi - PH.R91[:, 1]
    m = {}
    for r0, r1 in ((755, 800), (800, 870), (870, 945)):
        a = (PH.L91[:, 0] >= r0) & (PH.L91[:, 0] < r1); b = (PH.R91[:, 0] >= r0) & (PH.R91[:, 0] < r1)
        m["L%d" % r0] = round(float(eL[a].mean()), 1); m["R%d" % r0] = round(float(eR[b].mean()), 1) if b.any() else None
    m["rmsL"] = round(float(np.sqrt(np.mean(eL ** 2))), 1); m["rmsR"] = round(float(np.sqrt(np.mean(eR ** 2))), 1)
    lo2, _ = U.row_extents(cam, V, F, silL[:, 0])
    s = lo2 - silL[:, 1]; sel = silL[:, 0] >= 600
    m["silL600"] = round(float(s[sel].mean()), 1)
    lo3, hi3 = U.row_extents(cam, V, F, frows)
    olL = np.interp(frows, ro[:, 0], ro[:, 1]); olR = np.interp(frows, ro[:, 0], ro[:, 2])
    bl = np.where(np.isfinite(lo3), olL - lo3, -99); br = np.where(np.isfinite(hi3), hi3 - olR, -99)
    m["footL"] = round(float(bl.max()), 1); m["footR"] = round(float(br.max()), 1)
    # 448-5 dash-dot level line
    zl = [z_at(x, y) for x, y in zip(LX, LY)]
    m["line_z"] = [round(v) for v in zl]
    m["line_z_mean"] = round(float(np.mean(zl))); m["line_z_sd"] = round(float(np.std(zl)))
    m["hb300_minus_line"] = [round(hb_at(x, -300.0) - y) for x, y in zip(LX, LY)]
    v0, l0, a0 = hydro(0.0); v26, l26, _ = hydro(-26.0)
    m.update(vol0=round(v0, 3), vol26=round(v26, 3), lcb26=round(l26), amax=round(a0, 3))
    m["cradle2900"] = [round(hb_at(2900, z)) for z in (-300, -200, -100, 0)]
    m["cradle6100"] = [round(hb_at(6100, z)) for z in (-300, -200, -100, 0)]
    m["strake"] = [(x, round(hb_at(x, C.strake_z(x)))) for x in (1000, 2000, 3000, 4000, 5000, 6000, 7000, 7600)]
    return m

def setp(**kw):
    global C
    for k, v in kw.items():
        setattr(P, k, v)
    C = importlib.reload(sys.modules["hr26.curves"]); c.C = C; U.c.C = C

B4 = dict(SECTION_N=list(P.SECTION_N), SECTION_DEADRISE=list(P.SECTION_DEADRISE), DEADWOOD_H=list(P.DEADWOOD_H),
          DEADWOOD_W=P.DEADWOOD_W, CANOE_BOTTOM_HIDDEN=list(P.CANOE_BOTTOM_HIDDEN))
DW_AFT = [(5600.0, 0.0), (5900.0, 0.0), (6800.0, 100.0), (7400.0, 170.0), (7800.0, 210.0), (8000.0, 210.0)]
WTAB = [(5900.0, 200.0), (6800.0, 120.0)]
VAR = {
    "HEAD(s0)": dict(SECTION_N=s0p["SECTION_N"], SECTION_DEADRISE=s0p["SECTION_DEADRISE"],
                     DEADWOOD_H=[(0.0, 0.0), (8000.0, 0.0)], DEADWOOD_W=180.0, CANOE_BOTTOM_HIDDEN=s0p["CANOE_BOTTOM_HIDDEN"]),
    "U7(s3)": dict(SECTION_N=[(0.00, 2.4), (0.15, 3.1), (0.30, 3.4), (0.45, 4.0), (0.80, 4.0), (1.00, 3.8)],
                   DEADWOOD_H=DW_AFT, DEADWOOD_W=180.0),
    "V1(s4)": dict(),
    "C1 flat mid, V aft": dict(
        SECTION_DEADRISE=[(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, 2.0), (0.62, 2.0), (0.70, 12.0), (0.78, 24.0), (0.90, 15.0), (1.00, 3.0)],
        SECTION_N=[(0.00, 2.4), (0.15, 3.1), (0.35, 3.4), (0.60, 3.5), (0.80, 4.2), (1.00, 4.2)],
        DEADWOOD_H=DW_AFT, DEADWOOD_W=WTAB),
    "C2 = C1, N mid 3.2": dict(
        SECTION_DEADRISE=[(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, 2.0), (0.62, 2.0), (0.70, 12.0), (0.78, 24.0), (0.90, 15.0), (1.00, 3.0)],
        SECTION_N=[(0.00, 2.4), (0.15, 3.0), (0.35, 3.1), (0.60, 3.2), (0.80, 4.2), (1.00, 4.2)],
        DEADWOOD_H=DW_AFT, DEADWOOD_W=WTAB),
    "C3 = C1, dr mid 6": dict(
        SECTION_DEADRISE=[(0.00, 45.0), (0.127, 15.0), (0.20, 5.0), (0.30, 6.0), (0.62, 6.0), (0.70, 14.0), (0.78, 24.0), (0.90, 15.0), (1.00, 3.0)],
        SECTION_N=[(0.00, 2.4), (0.15, 3.1), (0.35, 3.4), (0.60, 3.5), (0.80, 4.2), (1.00, 4.2)],
        DEADWOOD_H=DW_AFT, DEADWOOD_W=WTAB),
}
res = {}
for name, kw in VAR.items():
    setp(**B4); setp(**kw)
    t0 = time.time()
    m = metrics()
    res[name] = m
    print(f"{name:20s} 9391 L {m['L755']:+.0f}/{m['L800']:+.0f}/{m['L870']:+.0f} R {m['R755']:+.0f}/{m['R800']:+.0f}/{m['R870'] if m['R870'] is not None else 0:+.0f} "
          f"rms {m['rmsL']}/{m['rmsR']} silL600 {m['silL600']:+.0f} foot {m['footL']:+.0f}/{m['footR']:+.0f} | line z {m['line_z_mean']}+-{m['line_z_sd']} "
          f"hb(-300)-line {m['hb300_minus_line']} | vol z0 {m['vol0']} z-26 {m['vol26']} LCB {m['lcb26']} Amax {m['amax']} | "
          f"cradle6100 {m['cradle6100']} ({time.time()-t0:.0f}s)", flush=True)
# strake change vs HEAD
h = dict(res["HEAD(s0)"]["strake"])
for name, m in res.items():
    d = [abs(v - h[x]) for x, v in m["strake"]]
    m["strake_max_change_vs_head"] = round(max(d), 1)
    print(f"{name:20s} largest half-breadth change at the strake vs HEAD: {max(d):.1f} mm")
json.dump(res, open(OUTF, "w"), indent=1)
