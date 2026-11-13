"""Hjerteformen akter (trinn 3, kvelden 13.11.2026): varianter av formen under
vann maalt mot IMG_9391 (akterfra), IMG_9388 (forfra) og volumet, uten CAD.

Hver variant er et sett parametre som settes paa hr26.params foer curves lastes
paa nytt. Kjoeres fra denne mappa: python hjerte.py [variant ...]
"""
import sys
import numpy as np
import common as c, uwlib as U

# undervann.patch (kontrollen 13.11)
U_PATCH = dict(
    SECTION_N=[(0.00, 2.4), (0.15, 3.1), (0.30, 3.4), (0.45, 4.0), (0.80, 4.0), (1.00, 3.8)],
    SECTION_DEADRISE=[(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, 4.0), (0.45, 6.0), (0.60, 16.0),
                      (0.75, 26.0), (0.90, 15.0), (1.00, 3.0)],
    DEADWOOD_H=[(5600.0, 0.0), (5900.0, 0.0), (6800.0, 100.0), (7400.0, 170.0), (7800.0, 210.0), (8000.0, 210.0)],
    DEADWOOD_W=180.0,
    CANOE_BOTTOM_HIDDEN=[
        (3250.0, -455.3), (3500.0, -470.0), (3750.0, -465.0), (4000.0, -465.0),
        (4250.0, -465.0), (4500.0, -465.0), (4590.0, -465.0), (4750.0, -465.0),
        (5000.0, -463.0), (5250.0, -460.0), (5500.0, -453.4), (5750.0, -450.1),
        (6000.0, -446.8), (6250.0, -445.2), (6500.0, -439.7), (6750.0, -437.4),
        (7000.0, -433.1), (7250.0, -424.4), (7500.0, -415.5), (7650.0, -410.7),
        (7800.0, -409.6), (7950.0, -408.5)],
)
# V1 oppaa (kontrollen 13.11)
V1 = dict(U_PATCH,
          SECTION_N=[(0.00, 2.4), (0.15, 3.1), (0.30, 3.4), (0.45, 4.5), (0.80, 4.5), (1.00, 4.2)],
          DEADWOOD_H=[(2900.0, 0.0), (3600.0, 80.0), (5900.0, 80.0), (6800.0, 100.0), (7400.0, 170.0),
                      (7800.0, 210.0), (8000.0, 210.0)],
          DEADWOOD_W=[(5900.0, 200.0), (6800.0, 120.0)])

VARIANTS = {"HEAD": {}, "U": U_PATCH, "V1": V1}
_ORIG = {}


def apply(over):
    for k in set(_ORIG) | set(over):
        if k not in _ORIG:
            _ORIG[k] = getattr(c.P, k, None)
    for k, v in _ORIG.items():
        if v is None and hasattr(c.P, k):
            delattr(c.P, k)
        elif v is not None:
            setattr(c.P, k, v)
    for k, v in over.items():
        setattr(c.P, k, v)
    C = c.reload_model()
    U.c.C = C
    return C


def keel_gap(C, x=4750.0, z=-300.0):
    """Vannrett avstand fra kjolens side (halv tykkelse) ut til skroget i hoyden z."""
    p = C._section_geom(float(x))["pts"]
    o = np.argsort(p[:, 1])
    y = float(np.interp(z, p[o, 1], p[o, 0]))
    return y - 0.5 * c.P.KEEL_ROOT_T


def run(name, over):
    import photos as PH
    C = apply(over)
    PH.c.C = C
    V, F = PH.mesh()
    r = PH.summary(name, V, F, extra="| kjol->skrog %.0f mm" % keel_gap(C))
    return r


if __name__ == "__main__":
    names = sys.argv[1:] or list(VARIANTS)
    for n in names:
        run(n, VARIANTS[n])
