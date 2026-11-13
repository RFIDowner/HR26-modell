"""Trinn 6, kontroll: hovedkameraet for «nye (4).jpeg» (pin_Nc_f850 fra
n4_fprof.json, loest fra listen og stevnen, som trinn 6 ikke endrer) brukt paa
modellen slik arbeidstreet staar naa. Skriver restene for bunn, forfot, ror og
vindu foer (lagret i n4_fprof.json) og etter.

  python ../../../../tools/memcap.py --gb 3 -- python n4_etter.py
"""
import json
import numpy as np
import common as c
import n4_cam as K
import n4_eval as E
import n4_fprof as FP

J = json.load(open(c.W + "/out/n4_fprof.json"))
out = {}
for tag in ("pin_Nc_f850", "pin_Nc_f800", "pin_Nc_f900"):
    d = J["out"][tag]
    cam = K.make_cam(np.array(d["q"], float), d["cm"])
    e = FP.summary(E.evaluate(cam))
    out[tag] = dict(before=d["ans"], after=e)
    f = lambda b: " ".join("-" if x[3] is None else "%+.0f" % x[3] for x in b)
    print(tag)
    print("  bunn  foer %s" % f(d["ans"]["bottom"]))
    print("  bunn  etter %s" % f(e["bottom"]))
    print("  forfot n foer %s | etter %s" % (f(d["ans"]["fore_n"]), f(e["fore_n"])))
    print("  ror z foto %.0f | vindu dx foer %s etter %s" % (e["rud_z"], np.round(d["ans"]["win_dx"], 0), np.round(e["win_dx"], 0)))
c.save_json(out, c.W + "/out/n4_etter.json")
