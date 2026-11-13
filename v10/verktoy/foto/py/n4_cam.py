"""Kamera for «nye (4).jpeg» (babord side paa land, litt forfra, lavt kamera,
1170 x 831, iPhone-skjermklipp: ukjent brennvidde og hovedpunkt).

Ankre (ting spoersmaalene 1-5 ikke endrer), dagens modell (arbeidstreet):

  strake    fenderlistens senter langs hele siden (u 57-1016)
  sedge     listens over- og underkant hver for seg: baandets synlige hoeyde
            avtar med avstanden og maaler perspektivet (hoeyden H er fri,
            bare forholdet langs baaten brukes)
  stem      stevnens silhuett over z ~ +300: rad 338-376 (stem_hi) og
            382-468 (crease). Silhuetten regnes fra skrognettet (min u per
            rad, flater med x < 1500 og z > 200), ikke fra P.STEM_LINE
  send      listens akterende (der listen moeter akterspeilets hjoerne)
  corner    akterspeilets hjoerne under listen (rad 432-470), trinn 4-formen
  (stern    skrogets akterste silhuett over listen, rad 396-426: bare i sett
            D; den passer daarlig, -17..+14 px, trolig dekkshjoernet/beslag)
  btr       bunnstoffets overkant (hvit tynn stripe -> roedt) aktenfor x 2 000:
            bare FORMEN, med fri hoeyde og fri helning (mm/m). Den er nesten
            rett i bildet og sier hvor hoeyt kameraet staar; hoeyden mot listen
            brukes ikke (spoersmaal 5). Den blaa overkanten brukes ikke: det
            blaa baandet er 19 px hoeyt forut og 8 px akter (listen: 7,2 mot
            5,2 px), saa det er bredere forut og ikke en vannrett linje.
  keel      (bare variantene K/KF) kjolens forkant, bakkant og bunn

Avstanden er det svake punktet: liste, stevn og hekk alene bestemmer ikke
brennvidde og avstand (f 460-750 og 3,5-4,3 m, se sett B i
../out/n4_cam_tidlig.json, foerste runde med sett A-D og K). Avstanden kommer fra en av tre kilder, og spredningen mellom dem
er usikkerheten:
  F   f-prior 850 +- 60 px: skjermklippet er 1170 px bredt = hele bildets
      bredde i Bilder-appen (4:3-bildet vises 1170 x 877, klippet til 831 i
      hoeyden), iPhone hovedkamera 24-26 mm ekv. -> f 811-880 px
  R   ingen prior: bare listebaandets tykkelse langs baaten og btr
  K   kjolen som anker (ikke for spoersmaal 3, bare for aa se hvor mye den trekker)

Kameramodeller: pin (hullkamera, hovedpunkt i midten), k1 (+ radial
fortegning), pp (+ hovedpunkt, prior du 0 +- 10, dv 0 +- 25 px: klippet i
hoeyden er hoeyst 46 px).

Lagrer ../out/n4_cam.json (alle varianter, hovedvarianten 'main').

  python ../../../../tools/memcap.py --gb 3 --lock -- python n4_cam.py
"""
import json
import math
import time

import numpy as np
from scipy.optimize import least_squares

import common as c
import uwlib as U
import geo9374 as G

G.use_model(None)                     # arbeidstreet = modellen eieren ser (trinn 5)
P, C = c.P, c.C
T = json.load(open(c.W + "/out/n4_trace.json"))
W_, H_ = T["W"], T["H"]


def arr(k):
    return np.asarray(T[k], float)


Cam = G.Cam9374
CAMX = {"pin": [], "k1": ["k1"], "pp": ["du", "dv"], "ppk1": ["du", "dv", "k1"]}


def make_cam(q, cm):
    kw = dict(zip(CAMX[cm], q[7:7 + len(CAMX[cm])]))
    return Cam(q[:7], W_, H_, **kw)


# ---------------------------------------------------------------- 3D-trekk
STRAKE3 = G.strake3(200.0, None, 400)
SEND3 = STRAKE3[-1:].copy()
H_STRAKE = P.STRAKE_H
VH, FH = U.hull_mesh(220, 60)
_Vf = VH[FH]
F_STEM = FH[(_Vf[:, :, 0].max(1) < 1500.0) & (_Vf[:, :, 2].min(1) > 200.0)]
F_STERN = FH[_Vf[:, :, 0].min(1) > 6800.0]
VK, FK = G.keel_mesh()
BT_X0 = 2000.0
BT_Z0 = 146.0          # blaa overkant (z ved x 1000 i IMG_9370, faller til 125); her bare et startpunkt
BR_Z0 = 38.0           # roedt start (IMG_9370)

# ---------------------------------------------------------------- observasjoner
OBS = {}
_st = arr("strake")
_st = _st[_st[:, 0] >= 100]           # forut for u 100 dykker modellens liste inn i skroget (STRAKE_TAPER)
OBS["strake"] = _st[:, [0, 3]]
OBS["s_top"] = _st[:, [0, 1]]
OBS["s_bot"] = _st[:, [0, 2]]
stem = np.r_[arr("stem_hi"), arr("crease")]
OBS["stem"] = stem[np.argsort(stem[:, 0])]
OBS["stemc"] = OBS["stem"][OBS["stem"][:, 0] >= 380]      # bare crease (z ~ +300..+750)
OBS["send"] = np.array([T["strake_end"]], float)
ste = arr("stern")
OBS["stern"] = ste[(ste[:, 0] >= 396) & (ste[:, 0] <= 426)]
OBS["corner"] = ste[(ste[:, 0] >= 432) & (ste[:, 0] <= 470)]     # under rad 470: rorhodet og V-bunnen
bt = arr("boottop")
OBS["bt_top"] = bt[np.isfinite(bt[:, 1])][:, [0, 1]]
OBS["bt_red"] = bt[np.isfinite(bt[:, 3])][:, [0, 3]]
kle = arr("keel_le"); OBS["keel_le"] = kle[(kle[:, 0] >= 596) & (kle[:, 0] <= 668)]
kte = arr("keel_te"); OBS["keel_te"] = kte[(kte[:, 0] >= 585) & (kte[:, 0] <= 650)]
OBS["keel_bot"] = arr("keel_bot")

SIG = dict(strake=1.0, sedge=1.0, stem=1.0, stemc=1.0, send=1.5, stern=2.0, corner=2.0, bt=1.0, btr=1.0, keel_le=1.5, keel_te=1.5,
           keel_bot=1.5)
SETS = {"A": ["strake", "sedge", "stem", "send", "corner", "bt"],
        "B": ["strake", "sedge", "stem", "send", "corner"],
        "C": ["strake", "stem", "send", "corner", "bt"],
        "D": ["strake", "sedge", "stem", "send", "stern", "corner", "bt"],
        "K": ["strake", "sedge", "stem", "send", "corner", "bt", "keel_le", "keel_te", "keel_bot"],
        "N": ["strake", "sedge", "stem", "send", "corner", "btr"],
        "N0": ["strake", "sedge", "stem", "send", "corner"],
        "NK": ["strake", "sedge", "stem", "send", "corner", "btr", "keel_le", "keel_te", "keel_bot"],
        "Nc": ["strake", "sedge", "stemc", "send", "corner", "btr"],
        "NKc": ["strake", "sedge", "stemc", "send", "corner", "btr", "keel_le", "keel_te", "keel_bot"]}
# ekstra frie parametre per anker: navn, skala, nedre, oevre, start
XP = {"sedge": [("hs", 0.02, 0.5, 2.0, 1.0)],
      "bt": [("bt_dz_top", 10.0, -300.0, 400.0, 0.0), ("bt_dz_red", 10.0, -300.0, 400.0, 0.0),
             ("bt_k", 1.0, -40.0, 40.0, 0.0)],
      "btr": [("bt_dz_red", 10.0, -300.0, 400.0, 0.0), ("bt_k", 1.0, -40.0, 40.0, 0.0)]}


def xnames(cm, aset):
    out = list(CAMX[cm])
    for k in SETS[aset]:
        out += [n for n, *_ in XP.get(k, [])]
    return out


def xval(q, cm, aset, name):
    return float(q[7 + xnames(cm, aset).index(name)])


def curve_resid(cam, X3, obs, cap=20.0):
    u, v, z = cam.project(X3)
    ok = z > 100
    u, v = u[ok], v[ok]
    if len(u) < 2:
        return np.full(len(obs), cap)
    o = np.argsort(u); uu, vv = u[o], v[o]
    inside = (obs[:, 0] > uu[0]) & (obs[:, 0] < uu[-1])
    pred = np.interp(obs[:, 0], uu, vv)
    return np.where(inside, pred - obs[:, 1], cap)


def sil_rows(cam, V, F, obs, side, cap=20.0):
    lo, hi = U.row_extents(cam, V, F, obs[:, 0])
    m = lo if side < 0 else hi
    return np.where(np.isfinite(m), m - obs[:, 1], cap)


def sil_cols(cam, V, F, obs, side, cap=20.0):
    lo, hi = U.row_extents(cam, V, F, obs[:, 0], axis="col")
    m = lo if side < 0 else hi
    return np.where(np.isfinite(m), m - obs[:, 1], cap)


def bt_lines(dt, dr, k):
    """Stripens to kanter paa skrogsiden fra BT_X0: blaa overkant
    z = bt_top_z(x) + dt + k (x - 4000)/1000 og roedt start z = 38 + dr + k (...)."""
    zt = lambda x: G.bt_top_z(x) + dt + k * (x - 4000.0) / 1000.0
    zr = lambda x: BR_Z0 + dr + k * (x - 4000.0) / 1000.0
    return G.zline3(zt, BT_X0, P.LOA, 110), G.zline3(zr, BT_X0, P.LOA, 110)


SEL = {"u_bt": None}         # stripens utvalg (u >= u_bt) holdes fast under en tilpasning


def bt_umin(cam):
    X = G.zline3(lambda x: 100.0, BT_X0, BT_X0 + 1.0, 2)
    u, _, _ = cam.project(X[:1])
    return float(u[0]) + 4.0


def set_selection(q, cm):
    SEL["u_bt"] = bt_umin(make_cam(q, cm))


def parts(q, cm, aset):
    cam = make_cam(q, cm)
    g = {}
    for k in SETS[aset]:
        if k == "strake":
            g[k] = curve_resid(cam, STRAKE3, OBS["strake"])
        elif k == "sedge":
            hs = xval(q, cm, aset, "hs")
            d = np.array([0.0, 0.0, 0.5 * H_STRAKE * hs])
            g[k] = np.r_[curve_resid(cam, STRAKE3 + d, OBS["s_top"]), curve_resid(cam, STRAKE3 - d, OBS["s_bot"])]
        elif k == "stem":
            g[k] = sil_rows(cam, VH, F_STEM, OBS["stem"], -1)
        elif k == "stemc":
            g[k] = sil_rows(cam, VH, F_STEM, OBS["stemc"], -1)
        elif k == "send":
            u, v, _ = cam.project(SEND3)
            g[k] = np.r_[u - OBS["send"][:, 0], v - OBS["send"][:, 1]]
        elif k == "stern":
            g[k] = sil_rows(cam, VH, F_STERN, OBS["stern"], +1)
        elif k == "corner":
            g[k] = sil_rows(cam, VH, F_STERN, OBS["corner"], +1)
        elif k == "bt":
            BT, BR = bt_lines(xval(q, cm, aset, "bt_dz_top"), xval(q, cm, aset, "bt_dz_red"),
                              xval(q, cm, aset, "bt_k"))
            ub = SEL["u_bt"] if SEL["u_bt"] is not None else bt_umin(cam)
            o1 = OBS["bt_top"]; o1 = o1[o1[:, 0] >= ub]
            o2 = OBS["bt_red"]; o2 = o2[o2[:, 0] >= ub]
            g[k] = np.r_[curve_resid(cam, BT, o1), curve_resid(cam, BR, o2)]
        elif k == "btr":
            _, BR = bt_lines(0.0, xval(q, cm, aset, "bt_dz_red"), xval(q, cm, aset, "bt_k"))
            ub = SEL["u_bt"] if SEL["u_bt"] is not None else bt_umin(cam)
            o2 = OBS["bt_red"]; o2 = o2[o2[:, 0] >= ub]
            g[k] = curve_resid(cam, BR, o2)
        elif k == "keel_le":
            g[k] = sil_rows(cam, VK, FK, OBS["keel_le"], -1)
        elif k == "keel_te":
            g[k] = sil_rows(cam, VK, FK, OBS["keel_te"], +1)
        elif k == "keel_bot":
            g[k] = sil_cols(cam, VK, FK, OBS["keel_bot"], +1)
    return g


PRIOR = {"f": None, "pp": (0.0, 10.0, 0.0, 25.0)}      # f: (f0, fs) eller None; pp: du0, dus, dv0, dvs


def residuals(q, cm, aset, f0=None, fs=None):
    g = parts(q, cm, aset)
    out = []
    for k, r in g.items():
        out.append(r / SIG[k] / np.sqrt(max(len(r), 1) / 20.0))
    fp = (f0, fs) if f0 is not None else PRIOR["f"]
    if fp is not None:
        out.append(np.array([(q[6] - fp[0]) / fp[1]]))
    if "du" in CAMX[cm] and PRIOR["pp"] is not None:
        du0, dus, dv0, dvs = PRIOR["pp"]
        out.append(np.array([(xval(q, cm, aset, "du") - du0) / dus, (xval(q, cm, aset, "dv") - dv0) / dvs]))
    return np.concatenate(out)


def rms(v):
    return float(np.sqrt(np.mean(np.square(v)))) if len(v) else float("nan")


def look_angles(Cpos, target):
    d = np.asarray(target, float) - np.asarray(Cpos, float)
    yaw = math.degrees(math.atan2(d[1], d[0]))
    pitch = math.degrees(math.atan2(-d[2], math.hypot(d[0], d[1])))
    return yaw, pitch


XS7 = [100, 100, 50, 0.5, 0.5, 0.5, 30]
LB7 = [-np.inf] * 6 + [300.0]
UB7 = [np.inf] * 6 + [6000.0]
XSX = dict(du=10.0, dv=10.0, k1=0.05)
LBX = dict(du=-300.0, dv=-300.0, k1=-0.6)
UBX = dict(du=300.0, dv=300.0, k1=0.6)


def bounds(cm, aset):
    xs, lb, ub = list(XS7), list(LB7), list(UB7)
    for k in CAMX[cm]:
        xs.append(XSX[k]); lb.append(LBX[k]); ub.append(UBX[k])
    for a in SETS[aset]:
        for n, s, lo, hi, _ in XP.get(a, []):
            xs.append(s); lb.append(lo); ub.append(hi)
    return np.array(xs, float), np.array(lb, float), np.array(ub, float)


def pad(q, cm, aset, src=None):
    """Startvektor for (cm, aset) fra q (7 kamera + valgfritt ekstra med navn
    fra src = (cm0, aset0)); manglende ekstra faar startverdien."""
    q = list(q)
    old = {}
    if src is not None:
        for i, n in enumerate(xnames(*src)):
            old[n] = q[7 + i]
    out = q[:7]
    start = dict(du=0.0, dv=0.0, k1=0.0)
    for a in XP.values():
        for n, s, lo, hi, s0 in a:
            start[n] = s0
    for n in xnames(cm, aset):
        out.append(old.get(n, start[n]))
    return np.array(out, float)


def solve(starts, cm, aset, nfev=600, f0=None, fs=None):
    xs, lb, ub = bounds(cm, aset)
    best = None
    for s in starts:
        s = np.clip(s, lb + 1e-9, ub - 1e-9)
        try:
            r = least_squares(lambda q: residuals(q, cm, aset, f0, fs), s, x_scale=xs, loss="soft_l1", f_scale=2.0,
                              max_nfev=nfev, bounds=(lb, ub), diff_step=1e-5)
        except Exception as e:          # noqa
            print("  start feilet:", e, flush=True)
            continue
        if best is None or r.cost < best.cost:
            best = r
    return best


def uncertainty(r):
    J = r.jac
    dof = max(len(r.fun) - len(r.x), 1)
    s2 = float(np.sum(r.fun ** 2) / dof)
    try:
        return np.sqrt(np.abs(np.diag(np.linalg.pinv(J.T @ J) * s2)))
    except np.linalg.LinAlgError:
        return np.full(len(r.x), np.nan)


def summarize(r, cm, aset):
    g = parts(r.x, cm, aset)
    sd = uncertainty(r)
    return dict(q=r.x, cmode=cm, aset=aset, names=["Cx", "Cy", "Cz", "yaw", "pitch", "roll", "f"] + xnames(cm, aset),
                extra=dict(zip(xnames(cm, aset), r.x[7:])), sd=sd,
                rms={k: rms(v) for k, v in g.items()}, mean={k: float(np.mean(v)) for k, v in g.items()},
                n={k: len(v) for k, v in g.items()}, cost=float(r.cost))


def show(tag, d):
    q = d["q"]
    print("%-8s C=(%.0f, %.0f, %.0f) yaw %.2f pitch %.2f roll %.2f f %.0f  %s  cost %.1f"
          % (tag, q[0], q[1], q[2], q[3], q[4], q[5], q[6], {k: round(float(v), 3) for k, v in d["extra"].items()},
             d["cost"]))
    print("         sd", np.round(d["sd"], 3).tolist())
    print("         rms", {k: round(v, 2) for k, v in d["rms"].items()},
          " mean", {k: round(v, 2) for k, v in d["mean"].items()}, flush=True)


def load(tag=None):
    """(kamera, dict) fra ../out/n4_cam.json; tag=None gir hovedvarianten."""
    J = json.load(open(c.W + "/out/n4_cam.json"))
    d = J["modes"][tag or J["main"]]
    return make_cam(np.asarray(d["q"], float), d["cmode"]), d


def tags():
    J = json.load(open(c.W + "/out/n4_cam.json"))
    return J["main"], list(J["modes"].keys())


def coarse():
    """Grov start fra haandleste punkter (ikke ankre, bare for aa finne dalen):
    stevn ved listen, listens ende, kjolens bunnhjoerner, rorets bunn,
    vinduets ender, stevnen ved stripen."""
    X0 = np.array([[135, 0, 1000], SEND3[0], [4300, 0, -1400], [5720, 0, -1380], [8150, 0, -1094],
                   [3691, -1223, 1015], [5335, -1303, 912], [828, 0, 130]], float)
    UV0 = np.array([[40, 336], T["strake_end"], [640, 686], [780, 675], [974, 607], [651.5, 385], [832, 400.5],
                    [187, 497]], float)

    def r0(q):
        u, v, _ = make_cam(q, "pin").project(X0)
        return np.r_[u - UV0[:, 0], v - UV0[:, 1]]
    res = []
    for cx in (1000.0, 2500.0, 4000.0):
        for cy in (-5000.0, -8000.0, -12000.0):
            for f in (800.0, 1200.0, 1800.0):
                Cp = (cx, cy, 100.0)
                yaw, pitch = look_angles(Cp, (4000.0, 0.0, 0.0))
                res.append(least_squares(r0, [cx, cy, 100.0, yaw, pitch, 0.0, f], x_scale=XS7))
    res.sort(key=lambda r: r.cost)
    return res


F_PRIOR = (850.0, 60.0)
# navn -> (kamera, sett, f-prior)
VARIANTS = {"pin_F": ("pin", "N", True), "k1_F": ("k1", "N", True), "pp_F": ("pp", "N", True),
            "pin_R": ("pin", "N", False), "k1_R": ("k1", "N", False), "pp_R": ("pp", "N", False),
            "pin_K": ("pin", "NK", False), "k1_K": ("k1", "NK", False), "pp_K": ("pp", "NK", False),
            "pin_KF": ("pin", "NK", True),
            "pin_F0": ("pin", "N0", True), "k1_F0": ("k1", "N0", True),
            "pin_R0": ("pin", "N0", False)}


if __name__ == "__main__":
    t0 = time.time()
    res = coarse()
    print("grov: beste kost", [round(r.cost, 1) for r in res[:4]], np.round(res[0].x, 1).tolist(), flush=True)
    set_selection(res[0].x, "pin")
    PRIOR["f"] = F_PRIOR
    sols = [solve([pad(r.x[:7], "pin", "N")], "pin", "N", nfev=300) for r in res[:3]]
    sols.sort(key=lambda r: r.cost)
    print("pin_F starter:", [round(r.cost, 1) for r in sols], "%.0fs" % (time.time() - t0), flush=True)
    set_selection(sols[0].x, "pin")
    out = {}
    for tag, (cm, aset, fp) in VARIANTS.items():
        PRIOR["f"] = F_PRIOR if fp else None
        st = [pad(sols[0].x, cm, aset, ("pin", "N"))]
        for t, d in out.items():
            st.append(pad(d["q"], cm, aset, (d["cmode"], d["aset"])))
        st = st[:5]
        r = solve(st, cm, aset, nfev=800)
        set_selection(r.x, cm)
        r = solve([r.x], cm, aset, nfev=400)
        out[tag] = summarize(r, cm, aset)
        out[tag]["u_bt"] = SEL["u_bt"]
        out[tag]["fprior"] = list(F_PRIOR) if fp else None
        show(tag, out[tag])
    J = dict(W=W_, H=H_, keys=["Cx", "Cy", "Cz", "yaw", "pitch", "roll", "f"], main="pin_F", modes=out,
             sig=SIG, sets=SETS, bt_x0=BT_X0, variants=VARIANTS, f_prior=F_PRIOR, pp_prior=PRIOR["pp"],
             note=("Kamera = geo9374.Cam9374(q[:7], W, H, **kamera-ekstra). Ankre og varianter: se n4_cam.py. "
                   "Modellen = arbeidstreet (trinn 5). bt_dz_red/bt_k: bunnstoffkantens frie hoeyde (mm over 38) og "
                   "helning (mm/m). F = f-prior 850 +- 60, R = uten, K = med kjolen, 0 = uten bunnstoffkanten."))
    c.save_json(J, c.W + "/out/n4_cam.json")
    print("ferdig %.0fs" % (time.time() - t0))
