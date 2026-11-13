"""Kamera og maal for «nye (3).jpeg» (rett akterfra, staaende oeyehoeyde,
baaten paa bukker). 13.11.2026, akter-maaleren.

BILDET VISER FOLK: bare tall og json i repoet; overlegg gaar til
C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/analyse/.

Kameraet loeses bare fra fenderlisten (tvers over akterspeilet med buen
42 mm opp, og forover paa styrbord side), listens to hjoerner (punkter),
rorhodet som senterlinje (svakt), kjolen (bunn -1 400, kanter) og et svakt
krav til kameraets hoeyde (0 +- 300 over DWL: staaende ved baaten).
Bildet er et skjermklipp med svarte felt; selve bildet er v 514-2017, saa
hovedpunktet antas i midten (585, 1265.5) i 'pin', fritt i 'pp'.

Maal:
  * spoersmaal 4: rorets nederste punkt (z) og avstanden til kjolens bunn
    (tilbakeprojisert til et loddrett plan x = konst. over rorets korde,
    x 7 661-8 150; spennet er usikkerheten)
  * styrbord akterspeilhjoerne (knuckle) -> (y, z) paa akterspeilsflaten

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python n3_cam.py [ovl]
"""
import json
import sys

import numpy as np
from scipy.optimize import least_squares

import common as c
import uwlib as U
import n1_geo as N
from n1_cam import poly_dist

P, C = N.P, N.C
T = json.load(open(c.W + "/out/n3_trace.json"))
W_, H_ = T["W"], T["H"]
DV0 = 1265.5 - H_ / 2.0              # bildets midte i skjermklippet
VK, FK = N.keel_mesh()

OBS = {"strake": np.asarray(T["strake"], float)[:, :2]}
kl = np.asarray(T["keel_l"], float); kr = np.asarray(T["keel_r"], float)
OBS["keel_l"] = kl[(kl[:, 1] >= 1640) & (kl[:, 1] <= 1738)]
OBS["keel_r"] = kr[(kr[:, 1] >= 1640) & (kr[:, 1] <= 1738)]
OBS["keel_bot"] = np.asarray(T["keel_bot"], float)
SIG = dict(strake=2.0, keel_l=2.5, keel_r=2.5, keel_bot=2.5, corners=5.0, rudder=8.0)
# listens hjoerner (der baandet svinger fra akterspeilet til siden), lest av paa 4x-utsnitt
OBS["corners"] = np.array([[27.0, 1060.0], [785.0, 1046.0]])
_sc = N.strake_corner()
CORN3 = np.array([[_sc[0] + 13.0, -(_sc[1] + 13.0), _sc[2]], [_sc[0] + 13.0, _sc[1] + 13.0, _sc[2]]])
# rorhodet (hvitt, vridd) foran akterspeilet: senter u ca. 410 +- 15 for v 1050-1340
OBS["rudder"] = np.c_[np.full(12, 410.0), np.linspace(1050.0, 1340.0, 12)]
RUD3 = np.array([[C.transom_x(z, 0.0) + 15.0, 0.0, z] for z in np.linspace(0.0, 900.0, 40)])
ZCAM = (0.0, 300.0)       # kameraets hoeyde: staaende, bakken ca. -1 500 (kjolen paa kloss)


def strake3():
    a = N.strake_transom(-1.0)
    b = N.strake_transom(1.0)[::-1]
    d = N.strake_side(1.0, 3000.0, 150)[::-1]
    return np.vstack([a, b[1:], d])


S3 = strake3()


def make(q, mode):
    if mode == "pin":
        return N.Cam(q[:7], W_, H_, du=0.0, dv=DV0)
    if mode == "k1":
        return N.Cam(q[:7], W_, H_, du=0.0, dv=DV0, k1=q[7])
    return N.Cam(q[:7], W_, H_, du=q[7], dv=DV0 + q[8])


def residuals(q, mode, parts=False, keel=True):
    cam = make(q, mode)
    g = {"strake": poly_dist(cam, S3, OBS["strake"]) / SIG["strake"]}
    u, v, _ = cam.project(CORN3)
    g["corners"] = np.r_[u - OBS["corners"][:, 0], v - OBS["corners"][:, 1]] / SIG["corners"]
    g["rudder"] = poly_dist(cam, RUD3, OBS["rudder"]) / SIG["rudder"]
    g["zcam"] = np.array([(q[2] - ZCAM[0]) / ZCAM[1]])
    if keel:
        o = OBS["keel_l"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 1])
        g["keel_l"] = np.where(np.isfinite(lo), lo - o[:, 0], 150.0) / SIG["keel_l"]
        o = OBS["keel_r"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 1])
        g["keel_r"] = np.where(np.isfinite(hi), hi - o[:, 0], 150.0) / SIG["keel_r"]
        o = OBS["keel_bot"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0], axis="col")
        g["keel_bot"] = np.where(np.isfinite(hi), hi - o[:, 1], 150.0) / SIG["keel_bot"]
    if mode == "pp":
        g["prior"] = np.array([q[7] / 150.0, q[8] / 150.0]) * 3.0
    if parts:
        return g
    return np.concatenate([v / np.sqrt(max(len(v), 1) / 20.0) if k not in ("prior", "zcam", "corners") else v
                           for k, v in g.items()])


def solve(mode):
    ex = {"pin": [], "k1": [0.0], "pp": [0.0, 0.0]}[mode]
    lb = [8500, -3000, -1500, 150, -30, -20, 300] + {"pin": [], "k1": [-1.0], "pp": [-400, -400]}[mode]
    ub = [25000, 3000, 2500, 210, 40, 20, 8000] + {"pin": [], "k1": [1.0], "pp": [400, 400]}[mode]
    xs = [60, 30, 30, 0.3, 0.3, 0.3, 20] + {"pin": [], "k1": [0.03], "pp": [5, 5]}[mode]
    best = None
    for X, Z, f in ((11000, 200, 1300), (12500, 300, 1700), (14000, 0, 2200), (10500, 500, 1100)):
        s = [X, 0.0, Z, 180.0, 5.0, 0.0, f] + ex
        r = least_squares(lambda q: residuals(q, mode), s, bounds=(lb, ub), x_scale=xs, loss="soft_l1",
                          f_scale=2.0, max_nfev=600)
        if best is None or r.cost < best.cost:
            best = r
    g = residuals(best.x, mode, True)
    rms = {k: round(float(np.sqrt(np.mean(np.square(v * SIG.get(k, 1.0))))), 2) for k, v in g.items()}
    return best, rms


def ray_z_at_x(cam, u, v, x):
    d = cam.ray(np.array([u]), np.array([v]))[0]
    t = (x - cam.C[0]) / d[0]
    X = cam.C + t * d
    return float(X[1]), float(X[2])


def on_transom_mm(cam, u, v):
    X = N.on_transom(cam, u, v)
    return None if X is None else (abs(float(X[1])), float(X[2]))


if __name__ == "__main__":
    out = {"W": W_, "H": H_, "modes": {}}
    tip = T["rudder_tip"]
    ZG = np.arange(-420.0, 900.0, 5.0)
    YM = np.array([(N.corner_y(float(z)) or (0, 0))[1] for z in ZG])
    for mode in ("pin", "k1", "pp"):
        best, rms = solve(mode)
        cam = make(best.x, mode)
        q = best.x
        print(f"{mode:4s} C=({q[0]:7.0f},{q[1]:6.0f},{q[2]:6.0f}) yaw {q[3]:6.2f} pitch {q[4]:6.2f} roll {q[5]:5.2f} "
              f"f {q[6]:6.0f} ekstra {np.round(q[7:], 3).tolist()} | rms px {rms}")
        # rorets bunn: z der strålen gjennom spissen krysser x = konst over korden
        zs = {int(x): ray_z_at_x(cam, tip[0], tip[1], x) for x in (7661.0, 7800.0, 7950.0, 8150.0)}
        zr = [zs[k][1] for k in zs]
        # kjolens bunn i bildet (modell -1 400) mot sporet
        o = OBS["keel_bot"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0], axis="col")
        kb_res = float(np.nanmean(hi - o[:, 1]))
        # modellens ror (bunn -1 094) og Enderleins (-1 047): forkant og bakkant i bildet
        mr = {}
        for zb in (-1094.0, -1047.0):
            X = np.array([[C.transom_x(zb, 0.0) + P.RUDDER_GAP, 0.0, zb], [P.RUDDER_TE_X, 0.0, zb]])
            u, v, _ = cam.project(X)
            mr[str(int(zb))] = [[float(u[0]), float(v[0])], [float(u[1]), float(v[1])]]
        print(f"     rorets spiss (u {tip[0]:.0f}, v {tip[1]:.0f}): z ved x 7661/7800/7950/8150 = "
              f"{', '.join('%.0f' % z for z in zr)} (y {', '.join('%.0f' % zs[k][0] for k in zs)}) | "
              f"kjolbunn rest {kb_res:+.1f} px")
        print(f"     modellens ror -1094: forkant v {mr['-1094'][0][1]:.0f}, bakkant v {mr['-1094'][1][1]:.0f}; "
              f"-1047: {mr['-1047'][0][1]:.0f} / {mr['-1047'][1][1]:.0f}")
        kn = []
        for u, v, _g in T["knuckle"]:
            r = on_transom_mm(cam, u, v)
            if r:
                kn.append([u, v, r[0], r[1], float(np.interp(r[1], ZG, YM))])
        kn = np.array(kn)
        for z0, z1 in ((150, 250), (250, 350), (350, 450), (450, 550), (550, 650), (650, 750)):
            s = kn[(kn[:, 3] >= z0) & (kn[:, 3] < z1)] if len(kn) else []
            if len(s):
                print(f"     hjoerne z {z0}-{z1}: n {len(s):2d} y foto {np.mean(s[:, 2]):4.0f} modell "
                      f"{np.mean(s[:, 4]):4.0f} diff {np.mean(s[:, 2] - s[:, 4]):+5.0f} mm")
        bt = np.asarray(T["bt_top"], float)
        bz = [on_transom_mm(cam, u, v) for u, v in bt if 470 <= u <= 560]
        bz = [b for b in bz if b]
        if bz:
            print(f"     stripens overkant paa akterspeilet (u 470-560): z {np.mean([b[1] for b in bz]):.0f}")
        out["modes"][mode] = dict(q=best.x, rms=rms, rudder_tip_z=zr, rudder_tip_x=[7661, 7800, 7950, 8150],
                                  keel_bot_res_px=kb_res, model_rudder_px=mr, knuckle=kn,
                                  stripe_z=float(np.mean([b[1] for b in bz])) if bz else None)
    c.save_json(out, c.W + "/out/n3_cam.json")
