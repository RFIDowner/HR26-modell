"""Klaring mellom roret og det printede skroget (V12, 15.11.2026).

Skroget hentes fra export/stl/01_skrog.stl (lagt tilbake fra platen som i
tools/sammensetning.py), roret bygges fra hr26.appendages.rudder(). For hver
hoeyde z snittes begge, og avstanden i snittplanet skrives ut (modell-mm i
full skala; 9 mm = 0,3 mm i print). Negativ avstand = roret skjaerer skroget.
Rortappene er ment aa gaa inn i skroget og holdes utenfor.

Skriver ogsaa skrogets akterste x innenfor rorets bredde (|y| < 60) per
hoeyde, saa en ser fenderlisten tvers over akterspeilet.

    python tools/memcap.py --gb 3 --lock -- python tools/ror_klaring.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import trimesh                                     # noqa: E402
from shapely.geometry import Polygon, box         # noqa: E402
from shapely.ops import unary_union                # noqa: E402

import sammensetning as S                          # noqa: E402
from hr26 import appendages as A                   # noqa: E402
from hr26 import params as P                       # noqa: E402


def mesh(T):
    m = trimesh.Trimesh(vertices=T.reshape(-1, 3), faces=np.arange(len(T) * 3).reshape(-1, 3), process=True)
    return m


def polys(m, z):
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return None
    T = np.eye(4)
    T[2, 3] = -z
    p2, _ = sec.to_2D(T)
    ps = [p for p in p2.polygons_full if p.is_valid and p.area > 0]
    return unary_union(ps) if ps else None


def main():
    s = P.SCALE
    hull = mesh(S.hull_from_plate(P) * s)
    rud_wp = A.rudder()
    rud = mesh(S.tess(rud_wp, 1.0))
    # tappene: hold dem utenfor (de skal inn i hullene)
    pin_zone = [(z - 0.6 * P.RUDDER_PIN_D - 5.0, z + 0.6 * P.RUDDER_PIN_D + 5.0) for z in P.RUDDER_PIN_Z]
    print("ror: bbox x %.0f..%.0f  y %.0f..%.0f  z %.0f..%.0f  volum %.1f l  vanntett %s" % (
        *np.ravel(np.c_[rud.bounds[0], rud.bounds[1]]), rud.volume / 1e6, rud.is_watertight))
    print("\n   z   skrog_x_maks(|y|<60)  ror_forkant  klaring   (negativ = skjaerer)")
    worst = (1e9, None)
    for z in np.arange(-1000.0, P.RUDDER_HEAD_Z + 1.0, 10.0):
        hp = polys(hull, z)
        rp = polys(rud, z)
        if rp is None:
            continue
        if any(a <= z <= b for a, b in pin_zone):
            rp = rp.intersection(box(A.rudder_le_upper(z) + 2.0, -500, 9000, 500))
        hx = np.nan
        d = np.nan
        if hp is not None:
            strip = hp.intersection(box(7000, -60, 9000, 60))
            if not strip.is_empty:
                hx = strip.bounds[2]
            if hp.intersects(rp):
                d = -np.sqrt(hp.intersection(rp).area)
            else:
                d = hp.distance(rp)
        if d < worst[0]:
            worst = (d, z)
        if int(z) % 30 == 0 or (np.isfinite(d) and d < 12.0):
            print("%6.0f   %8.0f          %8.0f    %7.1f" % (z, hx, rp.bounds[0], d))
    print("\nminste klaring %.1f mm (%.2f mm i print) ved z %.0f" % (worst[0], worst[0] / s, worst[1]))


if __name__ == "__main__":
    main()
