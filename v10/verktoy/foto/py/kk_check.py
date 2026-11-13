"""kk_: sjekk av at STL-nettet ligger i modellens ramme (x, z mot kurvene)."""
import numpy as np
import common as c
import geo9374 as G
G.use_model(None)
import kk_lib as L
from hr26 import deckhouse as D  # noqa  (bare kurver, ingen CAD-bygging)
P, C = c.P, c.C
V, F = L.model_mesh()
for x in (1000, 3000, 4500, 5300, 6000, 6800, 7400, 7800):
    s = np.abs(V[:, 0] - x) < 15
    hb = C.deck_half_breadth(x)
    sel = s & (np.abs(V[:, 1]) > hb - 30)
    print(x, "deck_hb %.0f sheer %.0f strake %.0f | mesh max|y| %.0f  z@outer(max z |y|>hb-30) %.0f" % (
        hb, C.sheer_z(x), C.strake_z(x), np.abs(V[s, 1]).max(), V[sel, 2].max() if sel.any() else np.nan))
    if 5600 < x < 6900:
        cw = D.coaming_half_width(x)
        sc = s & (np.abs(np.abs(V[:, 1]) - cw) < 60)
        print("   coaming hw %.0f top %.0f  mesh max z near |y|=hw: %.0f" % (cw, D.coaming_top_z(x), V[sc, 2].max()))
hi = V[:, 2] > 900
print("max x z>900:", V[hi, 0].max(), " transom_x(1000,0)", G.U.transom_x(1000.0, 0.0) if hasattr(G, 'U') else '')
