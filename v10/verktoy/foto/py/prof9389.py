"""Profil over brennvidden for IMG_9389: kameraet loeses med f laast
(1400-1800) og alt annet fritt (hovedmodusen 'stripe'), og forkroppens rester regnes
for hver. Viser hvor godt bildet bestemmer f, og hvor mye forkroppens rester
avhenger av den. Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python prof9389.py"""
import json

import numpy as np

import head9389  # noqa: F401
import common as c
import cam9389 as K
import e9389 as E
import photos
import uwlib as U

V, F = photos.mesh()
base = json.load(open(c.W + "/out/cam9389_modes.json"))["modes"]["stripe"]["q"]
print("modell:", c.P.__file__)
out = []
q = np.asarray(base, float)
for f in (1450.0, 1500.0, 1525.0, 1550.0, 1575.0, 1600.0, 1650.0, 1700.0):
    K.F0, K.FS = f, 1.0
    q0 = q.copy(); q0[6] = f
    r = K.solve("stripe", [q0])
    K.U_BT = K.u_limit(U.Cam(r.x[:7], 2000, 1500))
    r = K.solve("stripe", [r.x])
    g = K.residuals(r.x, True, "stripe")
    K.U_BT = None
    cost_nopri = float(np.sum(np.square(K.residuals(r.x, False, "stripe")[:-2])))
    E.set_cam(r.x[:7], r.x[8], r.x[7], r.x[9])
    rb, rf = E.parts(V, F)
    D = E._diag(V, F)
    xb = D["xb"][:, 0]
    row = dict(f=f, p=r.x[:7], dz=r.x[7:9], k=float(r.x[9]), cost=float(r.cost), chi2=cost_nopri,
               rms={k: float(np.sqrt(np.mean(np.square(v)))) for k, v in g.items()}, front=float(rf.mean()))
    for a, b in ((0, 1500), (1500, 2000), (2000, 2500), (2500, 3400)):
        m = (xb >= a) & (xb < b)
        row["b%d" % a] = float(rb[m].mean()) if m.any() else float("nan")
        row["mm%d" % a] = float((rb * D["mmb"])[m].mean()) if m.any() else float("nan")
    rbt = E.resid_bt(V, F); ok = rbt != E.CAP
    row["bt"] = float(rbt[ok].mean())
    rbt2 = E.resid_bt_top(V, F); ok2 = rbt2 != E.CAP
    row["bt_top"] = float(rbt2[ok2].mean())
    out.append(row)
    print("f %4.0f k %+4.1f chi2 %7.1f | strake %.2f venstre %.2f kjol %.2f/%.2f/%.2f vindu %5.1f ror %4.1f/%4.1f | dz %3.0f | "
          "front %+6.1f bunn <1500 %+6.1f 1500-2000 %+6.1f 2000-2500 %+6.1f 2500+ %+6.1f | stripe forut roedt %+5.1f blaa %+5.1f | C %s"
          % (f, r.x[9], cost_nopri, row["rms"]["strake_lo"], row["rms"]["left_sil"], row["rms"]["keel_le"], row["rms"]["keel_te"],
             row["rms"]["keel_bot"], row["rms"]["window"], row["rms"]["rud_te"], row["rms"]["rud_bot"], r.x[8],
             row["front"], row["b0"], row["b1500"], row["b2000"], row["b2500"], row["bt"], row["bt_top"],
             np.round(r.x[:6], 1).tolist()), flush=True)
    q = r.x.copy()
c.save_json(out, c.W + "/out/prof9389.json")
