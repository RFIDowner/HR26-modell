"""Kameraet for IMG_9395 (baaten i travelliften, forfra-nedenfra paa babord baug, 2400 x 1800).

Loeses KUN fra trekk som trinn 5 (forkroppen under vann) ikke flytter:
  strake  fenderlistens underkant (svart -> hvit topside), z = strake_z - 29 + dz_s, y = skrogflaten + dy_s
  stem    venstre silhuett, rad 355-545 (stevnen og baugen over z +700, dannes av skroget over z +300)
  keelL / keelR / keelB   kjolens forkant, bakkant og bunn (NACA-snitt, 240 mm tykk, appendages._KeelProfile)
  rudR / rudB             rorets bakkant og bunn
Kamera p = [Cx, Cy, Cz, yaw, pitch, roll, f] (uwlib.Cam), prior f = 1800 +- 100 (iPhone 26 mm).

Brukes IKKE i kameraet (bare som kontroll, se rapporten i main):
  stripen (vannlinjestripen): med fast hoeyde fra IMG_9370 (146/38) er den 33 px (ca. 100 mm)
      i utakt med fenderlisten, kjolen og roret, jevnt langs hele lengden og ogsaa paa stevnen.
      IMG_9391 viste det samme (ca. 120 mm, V10.md trinn 4). Stripen ligger altsaa hoeyere paa
      baaten i opptaksbildene enn i IMG_9370; hoeyden maales her paa stevnen (stripe_dz).
  aftR (babord hekk, hoeyre silhuett): stroppen ligger langs kanten og fenderlisten stikker ut.
  rudL (rorets forkant): rorets korde i modellen er usikker; 13 px av med alle kameraer.

Kjoeres fra denne mappa: python ../../../../tools/memcap.py --gb 3 -- python cam9395.py
Skriver out/cam9395.json.
"""
import json
import time

import numpy as np
from scipy.optimize import least_squares

import common as c
import geo9395 as G
import uwlib as U

P, C = c.P, c.C
W_, H_ = 2400, 1800
T = json.load(open(c.W + "/out/t9395_raw.json"))


def arr(k):
    return np.asarray(T[k], float)


st = arr("strake")
ok = (st[:, 0] >= 886) & (st[:, 0] <= 1735) & ~((st[:, 0] >= 1568) & (st[:, 0] <= 1622))
STRAKE = st[ok][:, [0, 2]]
sp = arr("stripe")
okt = ~((sp[:, 0] >= 1515) & (sp[:, 0] <= 1600)) & (sp[:, 0] <= 1680)
TOP = sp[okt][:, [0, 1]]
RED_ALL = sp[okt][:, [0, 3]]
left = arr("left")
ar = arr("aft_right")
AFTR = ar[(ar[:, 0] >= 842) & (ar[:, 0] <= 940)]
KL = arr("keel_left"); KL = KL[KL[:, 0] >= 1075]
KR = arr("keel_right")
KB = arr("keel_bot")
RL = arr("rud_left"); RL = RL[RL[:, 0] >= 1120]
RR = arr("rud_right"); RR = RR[RR[:, 0] >= 1100]
RB = arr("rud_bot")

XS = np.r_[np.linspace(60.0, 1000.0, 48), np.linspace(1020.0, 7900.0, 140)]
for _x in XS:
    G.section(_x)
VH, FH = U.hull_mesh(220, 60)
FH_HI = FH[(VH[FH][:, :, 2] > 300.0).all(1)]       # bare skroget over z +300
VK, FK = G.keel_mesh()
VR, FR = G.rudder_mesh()
KEYS = ["x", "y", "z", "yaw", "pitch", "roll", "f", "dz_strake", "dy_strake"]
PRI = dict(f=(1800.0, 100.0), dz_strake=15.0, dy_strake=30.0)
USE = ["strake", "stem", "keelL", "keelR", "keelB", "rudR", "rudB"]
STEM_ROWS = (355, 545)   # under rad ~560 er silhuetten baugens flare (z 300-650), der modellen er ~20 px for full
STEM_ALL = left[(left[:, 0] >= STEM_ROWS[0]) & (left[:, 0] <= STEM_ROWS[1])]
STEM = STEM_ALL


def curve_res(cam, X3, obs):
    u, v, _ = cam.project(X3)
    return G.poly_dist(obs, np.c_[u, v])


def ext(cam, V, F, rows, which, axis="row"):
    lo, hi = U.row_extents(cam, V, F, rows, axis=axis)
    return lo if which == "lo" else hi


def fin(e, o):
    return np.where(np.isfinite(e), e - o, 60.0)


def residuals(q, parts=False, use=None, diag=False):
    cam = U.Cam(q[:7], W_, H_)
    g = {}
    Xs = G.hull_line(lambda x: C.strake_z(x) - 29.0 + q[7], XS, dy=q[8])
    g["strake"] = curve_res(cam, Xs, STRAKE)
    g["stem"] = fin(ext(cam, VH, FH, STEM[:, 0], "lo"), STEM[:, 1])
    g["keelL"] = fin(ext(cam, VK, FK, KL[:, 0], "lo"), KL[:, 1])
    g["keelR"] = fin(ext(cam, VK, FK, KR[:, 0], "hi"), KR[:, 1])
    g["keelB"] = fin(ext(cam, VK, FK, KB[:, 0], "hi", axis="col"), KB[:, 1])
    g["rudR"] = fin(ext(cam, VR, FR, RR[:, 0], "hi"), RR[:, 1])
    g["rudB"] = fin(ext(cam, VR, FR, RB[:, 0], "hi", axis="col"), RB[:, 1])
    if diag:
        g["aftR"] = fin(ext(cam, VH, FH, AFTR[:, 0], "hi"), AFTR[:, 1])
        g["rudL"] = fin(ext(cam, VR, FR, RL[:, 0], "lo"), RL[:, 1])
        g["top146"] = curve_res(cam, G.hull_line(G.z_top, XS), TOP)
        g["red38"] = curve_res(cam, G.hull_line(lambda x: G.Z_RED, XS), RED_ALL)
    g["prior"] = np.array([(q[6] - PRI["f"][0]) / PRI["f"][1], q[7] / PRI["dz_strake"],
                           q[8] / PRI["dy_strake"]]) * 3.0
    if parts:
        return g
    use = use or USE
    return np.concatenate([g[k] / np.sqrt(max(len(g[k]), 1) / 30.0) for k in use] + [g["prior"]])


def rms(v):
    return float(np.sqrt(np.mean(np.square(v))))


LB = [-12000, -12000, -8000, -40, -60, -40, 1200, -80, -150]
UB = [3000, 2000, 1500, 80, 30, 40, 3000, 80, 150]
XSC = [200, 200, 200, 1, 1, 1, 30, 10, 10]


def solve(starts, use=None, nfev=300, verbose=True):
    best = None
    for s in starts:
        t0 = time.time()
        r = least_squares(lambda q: residuals(q, use=use), s, bounds=(LB, UB), x_scale=XSC,
                          loss="soft_l1", f_scale=3.0, max_nfev=nfev)
        if verbose:
            g = residuals(r.x, True)
            print("->", np.round(r.x, 2).tolist(), "cost %.1f" % r.cost,
                  {k: round(rms(v), 1) for k, v in g.items()}, "%.0fs" % (time.time() - t0), flush=True)
        if best is None or r.cost < best.cost:
            best = r
    return best


def stem_rows_above300(q):
    """Rader der modellens venstre silhuett dannes av skroget over z +300."""
    cam = U.Cam(q[:7], W_, H_)
    lo, _ = U.row_extents(cam, VH, FH, STEM_ALL[:, 0])
    lo2, _ = U.row_extents(cam, VH, FH_HI, STEM_ALL[:, 0])
    return np.abs(lo - lo2) < 0.5


def stripe_dz(q):
    """Stripens hoeyde: felles forskyvning dz av linjene 146/38 (IMG_9370) som passer best
    med de forreste 60 px av stripen (x ca. 850-1150, smal baug, formen nesten gitt av stevnen)."""
    cam = U.Cam(q[:7], W_, H_)
    out = {}
    for name, obs, zf in (("top", TOP, G.z_top), ("red", RED_ALL, lambda x: G.Z_RED)):
        o = obs[obs[:, 0] <= obs[0, 0] + 60]
        best = None
        for dz in np.arange(-40.0, 220.0, 2.0):
            X = G.hull_line(lambda x: zf(x) + dz, np.linspace(700, 2000, 160))
            if len(X) < 5:
                continue
            r = rms(curve_res(cam, X, o))
            if best is None or r < best[1]:
                best = (dz, r)
        out[name] = dict(dz=best[0], rms=best[1], n=len(o))
    return out


if __name__ == "__main__":
    p0 = [-3787.4, -2845.9, -1544.8, 26.2, -12.3, 1.2, 1816.0, 0.0, 0.0]
    t0 = time.time(); residuals(p0); print("one residual call %.2fs" % (time.time() - t0))
    k = stem_rows_above300(p0)
    STEM = STEM_ALL[k]
    print("stem rows used: %d of %d (%.0f-%.0f)" % (k.sum(), len(k), STEM[:, 0].min(), STEM[:, 0].max()))
    starts = [p0]
    for dx, dy, dz in ((800, 0, 0), (-800, 0, 0), (0, 800, 0), (0, -800, 0), (0, 0, 600), (0, 0, -600)):
        s = list(p0); s[0] += dx; s[1] += dy; s[2] += dz
        starts.append(s)
    best = solve(starts)
    # stem-radene paa nytt med det endelige kameraet
    k = stem_rows_above300(best.x)
    STEM = STEM_ALL[k]
    best = solve([best.x], verbose=False)
    q = best.x
    g = residuals(q, True, diag=True)
    # usikkerhet: Jacobi-matrisen ved loesningen (residualer i px, uten vekting), sigma = rms
    J = best.jac
    rr = residuals(q)
    s2 = float(np.sum(rr ** 2) / max(len(rr) - len(q), 1))
    try:
        cov = np.linalg.inv(J.T @ J) * s2
        sd = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        sd = np.full(len(q), np.nan)
    # utelat ett trekk om gangen
    loo = {}
    for drop in USE:
        use = [u for u in USE if u != drop]
        r = solve([q], use=use, verbose=False)
        loo[drop] = r.x.tolist()
        print("uten %-7s" % drop, np.round(r.x, 1).tolist(), flush=True)
    sdz = stripe_dz(q)
    out = dict(p=q[:7], q=q, keys=KEYS, W=W_, H=H_, sd=sd, rms={kk: rms(v) for kk, v in g.items()},
               n={kk: len(v) for kk, v in g.items()}, cost=best.cost, stem_rows=[float(STEM[:, 0].min()), float(STEM[:, 0].max())],
               use=USE, leave_one_out=loo, stripe_dz=sdz,
               note="p for uwlib.Cam(p, 2400, 1800). Stripen er ikke brukt; stripe_dz er stripens forskyvning "
                    "fra IMG_9370-hoeydene (146/38) maalt paa baugen med dette kameraet.")
    c.save_json(out, c.W + "/out/cam9395.json")
    print("BEST", np.round(q, 2).tolist())
    print("sd  ", np.round(sd, 2).tolist())
    print("rms ", {kk: round(rms(v), 2) for kk, v in g.items()})
    print("stripe dz", sdz)
