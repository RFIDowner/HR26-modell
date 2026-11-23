"""Trinn 9 «magen» (14.11.2026): maal et forslag mot bildene og formkravene.

For et sett tillegg til spanttabellene (opt_mage.install) skriver det:
  * «nye 1» (aktenfra, nedenfra): omrisset mot himmelen per radbelte, px og
    mm, + = bildet stikker lenger ut enn modellen (n1_meas.run)
  * IMG_9395 (forfra, nedenfra), IMG_9389 (skraatt bakfra) og IMG_9391
    (akterfra): + = modellen utenfor bildets omriss
  * vannlinjer, spantareal og kanobunnens volum

  python ../../../../tools/memcap.py --gb 3 -- python mage_eval.py [json ...]

Uten argument maales formen foer trinn 9 (tilleggene satt til null). Et json-argument er en fil fra
opt_mage.py --skriv (eller samme form) i ../out/.
"""
import contextlib
import io
import json
import sys

import numpy as np

import common as c
import uwlib as U
import opt_mage as M
import n1_meas as N1
import e9395
import e9389
import photos as PH

VAR_N1 = ("ppk1_corn", "ppk12", "pp_corn")


def load(path):
    d = json.load(open(path))
    k = len(M.KNOTS)
    p = np.zeros(3 * k)
    p[:k], p[k:2 * k], p[2 * k:] = d["deadrise"], d["n"], d["flare"]
    return p


def measure(tag, p=None):
    M.install(np.zeros(3 * len(M.KNOTS)) if p is None else p)
    V, F = U.hull_mesh(220, 60)
    res = {"tag": tag}
    # nye 1
    lines = []
    for var in VAR_N1:
        with contextlib.redirect_stdout(io.StringIO()):
            sil = N1.run(var)["sil"]
        for key in ("sil_l", "sil_r"):
            rows = [q for q in sil[key] if q is not None and not q["strap"]]
            for v0, v1 in ((1250, 1400), (1400, 1550), (1550, 1700), (1700, 1860)):
                s = [q for q in rows if v0 <= q["v"] < v1]
                if s:
                    res[f"n1_{var}_{key}_{v0}"] = float(np.mean([q["out_mm"] for q in s]))
                    lines.append(f"    {var:10s} {key} v {v0}-{v1}: ut {np.mean([q['out_px'] for q in s]):+6.1f} px"
                                 f" = {np.mean([q['out_mm'] for q in s]):+5.0f} mm  (x {np.mean([q['x'] for q in s]):5.0f},"
                                 f" z {np.mean([q['z'] for q in s]):5.0f}, |y| {np.mean([abs(q['y']) for q in s]):4.0f})")
    # IMG_9395, 9389, 9391
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        s95 = e9395.summary(V, F, tag)
        s89 = e9389.summary(V, F, tag)
    a, b = PH.e9391(V, F)
    res.update(e9395_wrms=s95["wrms"], e9395_rows=float(np.mean(s95["rows"])), e9395_cols=float(np.mean(s95["cols"])),
               e9391_L=float(np.mean(a)), e9391_R=float(np.mean(b)),
               e9391_rms=float(np.sqrt(np.mean(np.r_[a, b] ** 2))))
    kr = e9395.resid_keelroot(V, F)
    kr = kr[np.isfinite(kr)]
    res["e9395_keelroot"] = float(np.mean(kr)) if len(kr) else float("nan")
    res["e9389_bottom"] = float(np.mean(s89["bottom"]))
    Y = M.waterlines()
    A = M.area_curve()
    res["vol"] = c.C.displaced_volume_m3()
    res["Amax"] = float(A.max())
    res["xAmax"] = float(M.XS[A.argmax()])
    print(f"=== {tag}: kanobunn {res['vol']:.3f} m3, stoerste spant {A.max():.3f} m2 ved x {M.XS[A.argmax()]:.0f}")
    print("  nye 1 (+ = bildet utenfor modellen):")
    print("\n".join(lines))
    print("  IMG_9391 L %+.1f R %+.1f rms %.1f px (+ = modellen utenfor)" % (res["e9391_L"], res["e9391_R"], res["e9391_rms"]))
    print("  " + buf.getvalue().replace("\n", "\n  ").rstrip())
    print("  areal:", " ".join("%5.0f:%.3f" % (x, a_) for x, a_ in zip(M.XS[::8], A[::8])))
    for i, z in enumerate(M.ZS):
        print("  z %5.0f:" % z, " ".join("%4.0f" % v for v in Y[i, ::8]))
    return res


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a.endswith(".json")]
    out = [measure("foer trinn 9")]
    for a in args:
        out.append(measure(a, load(a if "/" in a or "\\" in a else c.W + "/out/" + a)))
    if len(out) > 1:
        print("\nendring (forslag - foer trinn 9):")
        for k in out[0]:
            if k == "tag":
                continue
            print("  %-28s " % k + "  ".join("%+8.2f" % (o[k] - out[0][k]) for o in out[1:]))
