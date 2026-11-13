"""Kamera for IMG_9389 (3/4 forfra styrbord, lavt, paa land; 2000 x 1500),
loest bare fra trekk som trinn 5 (forkroppen under vann) ikke endrer:

  strake_lo  fenderlistens underkant (moerk -> hvit), (x, y_skrog, z_liste - 29)
  strake_hi  listens overkant der vinduet ikke ligger inntil, (x, y + 26, z + 29)
  window     vinduets forende (ytre ramme), svak vekt
  left_sil   skrogets venstre omriss (akterspeilets hjoerne/ytterste side), rad 388-500
  keel_le    kjolens forkant (silhuett, rad 712-895), keel_te bakkanten (rad 686-870),
  keel_bot   bunnen (A._KeelProfile, 240 mm tykk, fas)
  rud_le/te/bot  roret (silhuett), rader/kolonner der stroppen ikke krysser
  bt_top/bt_red  vannlinjestripen, BARE aktenfor x 4 600 (der trinn 5 ikke
             rokker); hoeyden fri (z0 + dz), som i cam9387.py

Forkroppens omriss under vann og stripen forut brukes IKKE. Trekkene bygges
fra modellen i commit 0976477 (head9389.py), ikke arbeidskopien som endres i
trinn 5. Kjolens forkant brukes bare under hulkilen (z < ca. -740).
Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python cam9389.py
"""
import json
import time

import numpy as np
from scipy.optimize import least_squares

import head9389  # noqa: F401  (fast modell fra commit 0976477 FOER common: se head9389.py)
import common as c
import uwlib as U
import geo9389 as G

P, C = c.P, c.C
W_, H_ = 2000, 1500
T = json.load(open(c.W + "/out/t9389_cam.json"))
BT_X0 = 4600.0


def arr(k):
    return np.asarray(T[k], float)


# ---------------------------------------------------------------- 3D-trekk
def strake_edge3(dz, dy, x0=1500.0, n=240):
    x1 = G.strake_end_x()
    xs = np.linspace(x0, x1, n)
    out = []
    for x in xs:
        z = C.strake_z(x) + dz
        y = G.side_y(x, z)
        if np.isfinite(y):
            out.append((x, y + dy, z))
    return np.array(out)


STRAKE_LO3 = strake_edge3(-0.5 * P.STRAKE_H, 0.0)
STRAKE_HI3 = strake_edge3(+0.5 * P.STRAKE_H, P.STRAKE_PROUD)
WIN3 = G.window_ends()[:1]
VK, FK = G.keel_mesh()
VR, FR = G.rudder_mesh()
VH, FH = U.hull_mesh(260, 60)

# ---------------------------------------------------------------- observasjoner
OBS = {}
st = arr("strake")
OBS["strake_lo"] = st[np.isfinite(st[:, 1]) & (st[:, 0] >= 292)][:, [0, 1]]
OBS["strake_hi"] = st[np.isfinite(st[:, 2])][:, [0, 2]]
OBS["window"] = np.array([T["window_fwd"]], float)
ls = arr("left_sil"); OBS["left_sil"] = ls[np.isfinite(ls[:, 1])]
# kjolens forkant bare under hulkilen (rad >= 776, z under ca. -740): hulkilen
# endres i trinn 5 (KEEL_LE_FILLET_R 340 -> 1000 i arbeidskopien)
kle = arr("keel_le"); OBS["keel_le"] = kle[(kle[:, 0] >= 776) & np.isfinite(kle[:, 1])]
kte = arr("keel_te"); OBS["keel_te"] = kte[(kte[:, 0] >= 686) & np.isfinite(kte[:, 1])]
kbo = arr("keel_bot"); OBS["keel_bot"] = kbo[np.isfinite(kbo[:, 1])]
rl = arr("rudder_left"); OBS["rud_te"] = rl[np.isfinite(rl[:, 1])]
rr = arr("rudder_right"); OBS["rud_le"] = rr[np.isfinite(rr[:, 1])]
rb = arr("rudder_bot"); OBS["rud_bot"] = rb[np.isfinite(rb[:, 1])]
OBS["front"] = np.asarray(json.load(open(c.W + "/out/t9389_forkropp.json"))["front"], float)
_FH = FH[(VH[FH][:, :, 0].min(1) < 2500.0) & (VH[FH][:, :, 2].min(1) < 400.0)]
bt = arr("boottop")
OBS["bt_top"] = bt[np.isfinite(bt[:, 1])][:, [0, 1]]
OBS["bt_red"] = bt[np.isfinite(bt[:, 3])][:, [0, 3]]

# Vekter (px). Roret er svakt: det kan staa utslaatt paa land, og bunnen er
# 12-20 px for dyp i modellen ogsaa i IMG_9387 (Enderlein -1 047, modellen
# -1 094). Vinduets forende avviker 18-37 px ogsaa i IMG_9387. Listens
# overkant er avrundet/skyggelagt (baandet er ~9 px tynnere enn modellens 58 mm).
# Med kameraet loest uten roret ligger modellens ror 15-30 px feil (bunnen
# 30 px for lavt), saa roret, listens overkant og rorets forkant er bare
# kontroll (sigma 1e9 = ikke i loesningen).
# 'front' (forfotens omriss ved vannlinjen, rad 352-440, fra t9389_forkropp.json)
# er bare med i variantene *_forfot: den endres litt i trinn 5 (ca. 20 mm).
# Vinduets forende ligger 60-100 px fra modellens i alle kameraer (forenden
# synes ca. 300-400 mm lenger forut enn P.WIN_X0), saa den er bare kontroll.
# Venstre omriss (skrogsiden ved x ~ 7 000, hjerteformen akter) har en trend
# paa +-8 px som ingen kameraer fjerner: svak vekt (6 px).
SIG = dict(strake_lo=1.5, strake_hi=1e9, window=1e9, left_sil=6.0, keel_le=2.0, keel_te=2.0, keel_bot=2.5,
           rud_le=1e9, rud_te=1e9, rud_bot=1e9, bt_top=1.5, bt_red=1.5, front=1e9)
MODES = dict(fri=dict(bt=True, free=True), bt38=dict(bt=True, free=False), utenbt=dict(bt=False, free=False),
             stripe=dict(bt=True, free=True, full=True))
# 'stripe': hele stripen (begge kanter, ogsaa forut) med felles hoeydeforskyvning
# per kant og felles helning k (mm per m, prior K0 +- KS): stripen antas parallell
# med DWL (IMG_9370 flytende: roedt fra +38 hele veien; IMG_9387: -3,4 mm/m).
# Linjene ligger paa skrogsiden i z ~ 150-300; et utslag i halvbredden paa 30 mm
# flytter dem ca. 3 px her, hoeyden 10 mm flytter dem 4-7 px.
K0, KS = 0.0, 4.0


def curve_resid(cam, X3, obs, along="u"):
    """X3 er ordnet forut -> akter. Linja kuttes der den gaar rundt skrogets
    omriss (minste u): resten ligger paa baksiden og er skjult."""
    u, v, z = cam.project(X3)
    ok = z > 100
    u, v = u[ok], v[ok]
    if along == "u" and len(u) > 2:
        k = int(np.argmin(u)) + 1
        u, v = u[:k], v[:k]
    if len(u) < 2:
        return np.full(len(obs), 30.0)
    if along == "u":
        o = np.argsort(u); uu, vv = u[o], v[o]
        inside = (obs[:, 0] > uu[0]) & (obs[:, 0] < uu[-1])
        return np.where(inside, np.interp(obs[:, 0], uu, vv) - obs[:, 1], 30.0)
    o = np.argsort(v); uu, vv = u[o], v[o]
    inside = (obs[:, 0] > vv[0]) & (obs[:, 0] < vv[-1])
    return np.where(inside, np.interp(obs[:, 0], vv, uu) - obs[:, 1], 30.0)


_LINES = {}


def bt_lines(dt, dr, k=0.0, full=False):
    key = (float(dt), float(dr), float(k), full)
    L = _LINES.get(key)
    if L is None:
        x0 = 500.0 if full else BT_X0 - 800.0
        n = 240 if full else 120
        L = (G.zline3(lambda x: G.bt_top_z(x) + dt + k * (x - 4000.0) / 1000.0, x0, P.LOA, n),
             G.zline3(lambda x: 38.0 + dr + k * (x - 4000.0) / 1000.0, x0, P.LOA, n))
        if len(_LINES) > 200:
            _LINES.clear()
        _LINES[key] = L
    return L


def u_limit(cam, dt=0.0):
    """u for stripen ved x = BT_X0 (bare punkter til venstre for denne brukes)."""
    X = G.zline3(lambda x: G.bt_top_z(x) + dt, BT_X0, BT_X0 + 1, 2)
    return float(cam.project(X[:1])[0][0])


U_BT = None


F0, FS = 1500.0, 150.0          # f-prior: iPhone hovedkamera, 26 mm ekv. (ca. 0,6 x diagonalen)


def keel_enderlein():
    """Kjolen skalert loddrett mellom roten (z -450) og bunnen slik at bunnen
    staar i Enderleins -1 326 i stedet for -1 400 (variant til foelsomhet)."""
    V = VK0.copy()
    m = V[:, 2] < -450.0
    V[m, 2] = -450.0 + (V[m, 2] + 450.0) * (1326.0 - 450.0) / (1400.0 - 450.0)
    return V


VK0 = VK.copy()


def residuals(q, parts=False, mode="fri", f0=None, fs=None):
    f0 = F0 if f0 is None else f0
    fs = FS if fs is None else fs
    m = MODES[mode]
    cam = U.Cam(q[:7], W_, H_)
    g = {}
    g["strake_lo"] = curve_resid(cam, STRAKE_LO3, OBS["strake_lo"])
    g["strake_hi"] = curve_resid(cam, STRAKE_HI3, OBS["strake_hi"])
    u, v, _ = cam.project(WIN3)
    g["window"] = np.r_[u - OBS["window"][:, 0], v - OBS["window"][:, 1]]
    o = OBS["left_sil"]; lo, hi = U.row_extents(cam, VH, FH, o[:, 0])
    g["left_sil"] = np.where(np.isfinite(lo), lo - o[:, 1], 30.0)
    o = OBS["keel_le"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0])
    g["keel_le"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    o = OBS["keel_te"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0])
    g["keel_te"] = np.where(np.isfinite(lo), lo - o[:, 1], 30.0)
    o = OBS["keel_bot"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0], axis="col")
    g["keel_bot"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    o = OBS["front"]; lo, hi = U.row_extents(cam, VH, _FH, o[:, 0])
    g["front"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    o = OBS["rud_le"]; lo, hi = U.row_extents(cam, VR, FR, o[:, 0])
    g["rud_le"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    o = OBS["rud_te"]; lo, hi = U.row_extents(cam, VR, FR, o[:, 0])
    g["rud_te"] = np.where(np.isfinite(lo), lo - o[:, 1], 30.0)
    o = OBS["rud_bot"]; lo, hi = U.row_extents(cam, VR, FR, o[:, 0], axis="col")
    g["rud_bot"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    if m.get("full"):
        BT, BR = bt_lines(float(q[7]), float(q[8]), float(q[9]), True)
        g["bt_top"] = curve_resid(cam, BT, OBS["bt_top"])
        g["bt_red"] = curve_resid(cam, BR, OBS["bt_red"])
    elif m["bt"]:
        ub = U_BT if U_BT is not None else u_limit(cam)
        if m["free"]:
            BT, BR = bt_lines(float(q[7]), float(q[8]))
        else:
            BT, BR = bt_lines(0.0, 0.0)
        o = OBS["bt_top"]; o = o[o[:, 0] <= ub - 5]
        g["bt_top"] = curve_resid(cam, BT, o)
        o = OBS["bt_red"]; o = o[o[:, 0] <= ub - 5]
        g["bt_red"] = curve_resid(cam, BR, o)
    g["prior"] = np.array([(q[6] - f0) / fs] + ([(q[9] - K0) / KS] if m.get("full") else []))
    if parts:
        return g
    out = []
    for k, v in g.items():
        if k == "prior":
            out.append(v * 3.0)
        elif SIG.get(k, 1.0) < 1e8:
            out.append(v / SIG[k] / np.sqrt(max(len(v), 1) / 20.0))
    return np.concatenate(out)


def rms(v):
    return float(np.sqrt(np.mean(np.square(v)))) if len(v) else float("nan")


XS = [100, 100, 50, 0.5, 0.5, 0.5, 30, 20, 20, 2]


def solve(mode, starts, nfev=400):
    npar = (10 if MODES[mode].get("full") else 9) if MODES[mode]["free"] else 7
    lb = [-np.inf] * 7 + [-250.0, -250.0, -40.0]
    ub = [np.inf] * 7 + [400.0, 400.0, 40.0]
    global U_BT
    best = None
    fixed = U_BT is not None
    for s in starts:
        s = (list(s[:7]) + [100.0, 100.0, 0.0][:npar - 7] if len(s) < 9 else list(s[:9]) + [0.0])[:npar]             if len(s) < npar else list(s[:npar])
        if not fixed:
            U_BT = u_limit(U.Cam(s[:7], W_, H_))       # fast utvalg under loesningen
        r = least_squares(lambda q: residuals(q, mode=mode), s, x_scale=XS[:npar], loss="soft_l1", f_scale=2.0,
                          max_nfev=nfev, bounds=(lb[:npar], ub[:npar]), diff_step=1e-5)
        if best is None or r.cost < best.cost:
            best = r
    if not fixed:
        U_BT = None
    return best


def uncertainty(r):
    J = r.jac
    dof = max(len(r.fun) - len(r.x), 1)
    s2 = float(np.sum(r.fun ** 2) / dof)
    try:
        return np.sqrt(np.diag(np.linalg.inv(J.T @ J) * s2))
    except np.linalg.LinAlgError:
        return np.full(len(r.x), np.nan)


P_SCORE = [1202.9, 1570.5, -523.5, -30.0, 2.62, -3.55, 1563.4]

HOVED = "stripe"
VARIANTS = {
    # navn: (modus, sigma-endringer, kjol, f-prior, k-prior)
    "stripe": ("stripe", {}, "modell", None, (0.0, 4.0)),              # HOVEDKAMERAET
    "stripe_k0": ("stripe", {}, "modell", None, (0.0, 0.5)),            # stripen laast parallell med DWL
    "stripe_k-3": ("stripe", {}, "modell", None, (-3.4, 0.5)),         # helning som IMG_9387
    "stripe_f1500": ("stripe", {}, "modell", (1500.0, 15.0), (0.0, 4.0)),
    "stripe_uten_kjolbunn": ("stripe", {"keel_bot": 1e9}, "modell", None, (0.0, 4.0)),
    "stripe_uten_venstre": ("stripe", {"left_sil": 1e9}, "modell", None, (0.0, 4.0)),
    "stripe_venstre2": ("stripe", {"left_sil": 2.0}, "modell", None, (0.0, 4.0)),
    "stripe_med_vindu": ("stripe", {"window": 30.0}, "modell", None, (0.0, 4.0)),
    "stripe_kjol1326": ("stripe", {}, "enderlein", None, (0.0, 4.0)),
    "stripe_med_ror": ("stripe", {"rud_te": 4.0, "rud_bot": 6.0}, "modell", None, (0.0, 4.0)),
    "stripe_forfot": ("stripe", {"front": 6.0}, "modell", None, (0.0, 4.0)),
    "stripe_k0_forfot": ("stripe", {"front": 6.0}, "modell", None, (0.0, 0.5)),
    "fri_forfot": ("fri", {"front": 6.0}, "modell", None),
    "fri": ("fri", {}, "modell", None),                                # stripen bare akter, hoeyden fri
    "utenbt": ("utenbt", {}, "modell", None),
    "bt38": ("bt38", {}, "modell", None),
    "fri_f1500": ("fri", {}, "modell", (1500.0, 15.0)),
    "fri_vindu_sterk": ("fri", {"window": 3.0}, "modell", None),
    "fri_venstre2_vindu30": ("fri", {"left_sil": 2.0, "window": 30.0}, "modell", None),
}

if __name__ == "__main__":
    import sys
    t0 = time.time()
    s0 = json.load(open(c.W + "/out/s9389.json"))
    starts = [np.asarray(d["x"], float) for d in s0[:5]]
    names = sys.argv[1:] or list(VARIANTS)
    try:
        out = json.load(open(c.W + "/out/cam9389_modes.json"))["modes"]
    except (OSError, KeyError):
        out = {}
    sig0 = dict(SIG)
    for name in names:
        mode, sover, keel, fpr = VARIANTS[name][:4]
        K0, KS = VARIANTS[name][4] if len(VARIANTS[name]) > 4 else (0.0, 4.0)
        SIG.clear(); SIG.update(sig0); SIG.update(sover)
        VK = keel_enderlein() if keel == "enderlein" else VK0
        F0, FS = fpr if fpr else (1500.0, 150.0)
        t1 = time.time()
        st = starts if name == "utenbt" or "utenbt" not in out else [np.asarray(out["utenbt"]["q"])]
        if mode != "utenbt" and "fri" in out and name != "bt38":
            st = [np.asarray(out["fri"]["q"])] + st[:1]
        if mode == "stripe":
            # flat dal langs f: start fra alle tidligere stripe-loesninger og velg laveste kost
            st = [np.asarray(v["q"], float) for v in out.values() if v.get("mode") == "stripe"] + st
        r = solve(mode, st)
        U_BT = u_limit(U.Cam(r.x[:7], W_, H_))
        r = solve(mode, [r.x])
        g = residuals(r.x, True, mode)
        sd = uncertainty(r)
        out[name] = dict(q=r.x, p=r.x[:7], sd=sd, rms={k: rms(v) for k, v in g.items()},
                         mean={k: float(np.mean(v)) for k, v in g.items()}, n={k: len(v) for k, v in g.items()},
                         u_bt_max=U_BT, cost=float(r.cost), mode=mode, sig=dict(SIG), keel=keel, fprior=[F0, FS],
                         kprior=[K0, KS])
        U_BT = None
        print(name, np.round(r.x, 2).tolist(), "sd", np.round(sd, 2).tolist(), "%.0fs" % (time.time() - t1))
        print("   rms", {k: round(rms(v), 2) for k, v in g.items()})
        print("   mean", {k: round(float(np.mean(v)), 2) for k, v in g.items()}, flush=True)
    SIG.clear(); SIG.update(sig0); VK = VK0; F0, FS = 1500.0, 150.0; K0, KS = 0.0, 4.0
    c.save_json(dict(modes=out, keys=["Cx", "Cy", "Cz", "yaw", "pitch", "roll", "f"], W=W_, H=H_),
                c.W + "/out/cam9389_modes.json")
    m = out[HOVED]
    q = np.asarray(m["q"], float)
    res = dict(p=q[:7], keys=["Cx", "Cy", "Cz", "yaw", "pitch", "roll", "f"], W=W_, H=H_, variant=HOVED,
               bt_dz_top=float(q[7]), bt_dz_red=float(q[8]), bt_slope_per_m=float(q[9]), sd=m["sd"], rms=m["rms"],
               mean=m["mean"], n=m["n"], model_ref=head9389.REF,
               variants={k: dict(p=v["p"], q=v["q"], rms=v["rms"]) for k, v in out.items()},
               note=("uwlib.Cam(p, 2000, 1500). Hovedkamera 'stripe', loest paa modellen i commit 0976477 "
                     "(head9389.py) fra fenderlistens underkant, kjolen under hulkilen (A._KeelProfile, 240 mm), "
                     "skrogets venstre omriss (rad 388-500, svak: sigma 6 px) og hele "
                     "vannlinjestripen med fri hoeyde og helning (prior 0 +- 4 mm/m; gir +7 mm/m): blaa overkant "
                     "z = bt_top_z(x) + bt_dz_top, roedt fra z = 38 + bt_dz_red (+ bt_slope_per_m (x-4000)/1000). "
                     "Roret, vinduet, listens overkant og forfoten er bare kontroll; forfoten ved vannlinjen "
                     "(rad 352-440) treffer innen 4 px uten aa vaere med. f er ikke godt bestemt av liste og kjol "
                     "alene (1 500-1 750 passer nesten like godt); stripen over hele lengden laaser den til ca. "
                     "1 560. Se cam9389.py, prof9389.py og vurder9389.py."))
    c.save_json(res, c.W + "/out/cam9389.json")
