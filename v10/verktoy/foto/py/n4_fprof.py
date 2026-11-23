"""Profil over brennvidden for «nye (4).jpeg»: kameraet loeses med f laast
(650-1000 px) for ankersettet N (liste, listebaand, stevn, listeende, hekkens
hjoerne, bunnstoffkantens form) med pin og k1, for NK (N + kjolen) med pin, og
for Nc/NKc der stevnen bare er raden 380-468 (z ~ +300..+750; over den kan
baugens utfall/fendere skjeve silhuetten).
For hver f: kostnaden (hvor godt ankrene passer) og svarene paa spoersmaal 1-5
(n4_eval.evaluate).

Avstanden er det svake punktet i bildet (se n4_cam.py): skrogsiden og stevnen
alene vil ha f ca. 690-790, kjolen vil ha 900-940, og et uzoomet skjermklipp av
et iPhone-bilde (hovedkamera 24-26 mm ekv.) gir 811-880. Denne profilen viser
hvor mye svarene flytter seg over det spennet.

  python ../../../../tools/memcap.py --gb 3 --lock -- python n4_fprof.py

Ut: ../out/n4_fprof.json
"""
import time

import numpy as np

import common as c
import n4_cam as K
import n4_eval as E

FS = [650.0, 700.0, 750.0, 800.0, 850.0, 900.0, 950.0, 1000.0]
RUNS = [("pin", "N"), ("k1", "N"), ("pin", "NK"), ("pin", "Nc"), ("pin", "NKc")]


def summary(e):
    b = e["q1"]["bins"]
    q3 = e["q3"]
    r4 = e["q4"]
    m = r4["chord"]["z"] < -700
    s = e["q5s"]
    return dict(
        bottom=[(d["x0"], d["x1"], d["n"], d["mean"]) for d in b],
        fore_n=[(d["x0"], d["x1"], d["n"], d["mean"]) for d in e["q2"]["bins_n"]],
        fore_x=[(d["x0"], d["x1"], d["n"], d["mean"]) for d in e["q2"]["bins"]],
        keel_dmm=q3["depth"]["dmm"], keel_depth=q3["depth"]["photo"], keel_le=float(np.nanmedian(q3["le"]["mm"])),
        keel_te=float(np.nanmedian(q3["te"]["mm"])),
        rud_z=r4["bot"]["z_photo"], rud_le=float(np.nanmedian(r4["le"]["mm"])),
        rud_te=float(np.nanmedian(r4["te"]["mm"])),
        rud_chord_photo=float(np.nanmean(r4["chord"]["photo"][m])),
        rud_chord_model=float(np.nanmean(r4["chord"]["model"][m])),
        win=e["q5w"]["photo_x"], win_dx=e["q5w"]["dx"],
        stripe={n: s[n]["at"]["4600"] for n in ("blue_top", "blue_bot", "red_top")})


if __name__ == "__main__":
    t0 = time.time()
    cam0, d0 = K.load("pin_F")
    K.SEL["u_bt"] = d0["u_bt"]
    out = {}
    prev = {}
    for cm, aset in RUNS:
        for f in FS:
            tag = "%s_%s_f%d" % (cm, aset, f)
            K.PRIOR["f"] = (f, 0.5)
            src = prev.get((cm, aset))
            q0 = np.array(d0["q"], float); q0[6] = f
            starts = [K.pad(q0, cm, aset, ("pin", "N"))]
            if src is not None:
                q = np.array(src, float); q[6] = f
                starts.append(q)
            r = K.solve(starts, cm, aset, nfev=600)
            prev[(cm, aset)] = r.x
            d = K.summarize(r, cm, aset)
            # kostnad uten f-prioren: bare ankrene
            K.PRIOR["f"] = None
            res = K.residuals(r.x, cm, aset)
            cost = float(np.sum(4.0 * (np.sqrt(1.0 + (res / 2.0) ** 2) - 1.0)))      # = least_squares-kosten
            cam = K.make_cam(r.x, cm)
            e = summary(E.evaluate(cam))
            out[tag] = dict(cm=cm, aset=aset, f=f, q=r.x, rms=d["rms"], cost=cost, extra=d["extra"], ans=e)
            b = e["bottom"]
            print("%-14s cost %6.1f  C=(%.0f, %.0f, %.0f)  rms %s" % (tag, cost, r.x[0], r.x[1], r.x[2],
                  {k: round(v, 1) for k, v in d["rms"].items()}))
            print("      bunn mm %s | forfot n %s | kjol %+.0f (dybde %.0f) le %+.0f te %+.0f | ror z %.0f korde %.0f/%.0f"
                  " | vindu %+.0f/%+.0f | roedt %.0f under liste" % (
                      " ".join("-" if x[3] is None else "%+.0f" % x[3] for x in b),
                      " ".join("-" if x[3] is None else "%+.0f" % x[3] for x in e["fore_n"]),
                      e["keel_dmm"], e["keel_depth"], e["keel_le"], e["keel_te"], e["rud_z"], e["rud_chord_photo"],
                      e["rud_chord_model"], e["win_dx"][0], e["win_dx"][1], e["stripe"]["red_top"]["under_strake"]),
                  flush=True)
    c.save_json(dict(fs=FS, runs=RUNS, out=out, note="Kostnad = soft_l1 (f_scale 2) paa de vektede ankerrestene, "
                     "uten f-prior. ans: se n4_fprof.summary."), c.W + "/out/n4_fprof.json")
    print("ferdig %.0fs" % (time.time() - t0))
