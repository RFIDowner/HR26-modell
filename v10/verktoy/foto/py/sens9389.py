"""Hva maaler IMG_9389? Foelsomheten til e9389.resid for enkle endringer av
forkroppen (x 1 000-3 400, under DWL) i nettet, med hovedkameraet:

  dypere      z - 20 mm under DWL (senterlinjen og hele bunnen ned)
  bredere     y x 1,10 under DWL (fyldigere spant, samme dybde)
  V5          bunnreisning +5 grader: z + |y| tan 5 (kjolen staar, kimingen loeftes)
  flat5       bunnreisning -5 grader: z - |y| tan 5 (flatere/fyldigere bunn)
  forfot+20   x - 20 mm for x < 1 300 (forfoten lenger forut)

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python sens9389.py
"""
import numpy as np

import head9389  # noqa: F401
import common as c
import e9389 as E
import photos

V0, F = photos.mesh()


def region(V, x0=1000.0, x1=3400.0):
    return (V[:, 0] > x0) & (V[:, 0] < x1) & (V[:, 2] < 0.0)


def ramp(V, x0=1000.0, x1=3400.0, w=300.0):
    """1 inne i [x0, x1], glatt ned til 0 over w mm i hver ende."""
    x = V[:, 0]
    a = np.clip((x - (x0 - w)) / w, 0, 1) * np.clip(((x1 + w) - x) / w, 0, 1)
    return a * (V[:, 2] < 0.0)


PERT = {
    "dypere": lambda V: V + np.c_[0 * V[:, 0], 0 * V[:, 0], -20.0 * ramp(V)],
    "bredere": lambda V: V * np.c_[np.ones(len(V)), 1.0 + 0.10 * ramp(V), np.ones(len(V))],
    "V5": lambda V: V + np.c_[0 * V[:, 0], 0 * V[:, 0], np.abs(V[:, 1]) * np.tan(np.radians(5.0)) * ramp(V)],
    "flat5": lambda V: V - np.c_[0 * V[:, 0], 0 * V[:, 0], np.abs(V[:, 1]) * np.tan(np.radians(5.0)) * ramp(V)],
    "forfot+20": lambda V: V - np.c_[20.0 * ramp(V, 0.0, 1300.0, 200.0), 0 * V[:, 0], 0 * V[:, 0]],
}

if __name__ == "__main__":
    rb0, rf0 = E.parts(V0, F)
    D = E._diag(V0, F)
    xb = D["xb"][:, 0]
    bins = [(0, 1500), (1500, 2000), (2000, 2500), (2500, 3400)]
    print("modell", head9389.REF, "kamera f %.0f" % E.CAM.f)
    print("%-10s %8s %8s %8s %8s %8s %8s" % ("endring", "front", "x<1500", "1500-2000", "2000-2500", "2500+", "stripe"))
    rbt0 = E.resid_bt(V0, F)
    for name, fn in PERT.items():
        V = fn(V0)
        rb, rf = E.parts(V, F)
        rbt = E.resid_bt(V, F)
        ok = (rbt != E.CAP) & (rbt0 != E.CAP)
        cells = ["%+8.1f" % (rf - rf0).mean()]
        for a, b in bins:
            m = (xb >= a) & (xb < b)
            cells.append("%+8.1f" % (rb - rb0)[m].mean())
        cells.append("%+8.2f" % (rbt - rbt0)[ok].mean())
        print("%-10s %s" % (name, " ".join(cells)), flush=True)
