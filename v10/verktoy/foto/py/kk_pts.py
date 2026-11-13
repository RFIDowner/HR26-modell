"""kk_: modellpunkter (dekkskant, liste, karmtopp, rekkefot) projisert i nye (6) og nye (4)."""
import json
import numpy as np
import common as c
import geo9374 as G
G.use_model(None)
import n6_cam as K6
import n4_ovl as O
from hr26 import deckhouse as D
P, C = c.P, c.C
J = json.load(open(c.W + "/out/n6_cam.json"))
d = J["modes"]["pin_keel"]
cam6 = K6.make_cam(np.asarray(d["q"], float), "pin")
cam4, _ = O.load("fprof:pin_Nc_f850")
for name, cam, sg in (("n6", cam6, 1.0), ("n4", cam4, -1.0)):
    print(name)
    for x in (5000, 5150, 5400, 5650, 5800, 6000, 6300, 6700, 7000, 7300, 7600, 7850):
        hb = C.deck_half_breadth(x)
        pts = [[x, sg * G.side_y(x, C.strake_z(x)), C.strake_z(x)], [x, sg * hb, C.sheer_z(x)],
               [x, sg * (hb - 70), D.deck_z(x, hb - 70)]]
        if 5580 < x < 6900:
            pts.append([x, sg * D.coaming_half_width(x), D.coaming_top_z(x)])
        u, v, z = cam.project(np.array(pts))
        print("  x %5d  strake (%5.0f,%5.1f) sheer (%5.0f,%5.1f) stanchbase v %5.1f %s  mm/px %.2f" % (
            x, u[0], v[0], u[1], v[1], v[2], ("coam (%5.0f,%5.1f)" % (u[3], v[3])) if len(u) > 3 else "",
            z[1] / cam.f))
