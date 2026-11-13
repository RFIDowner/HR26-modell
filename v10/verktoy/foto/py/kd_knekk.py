"""Kontroll av trinn 8 («kanten»): modellens nye dekkskant (roed) og knekklinjen
(blaa prikker, hver 100 mm der den ligger under dekkskanten) over et bilde.

  python ../../../../tools/memcap.py --gb 2 -- python kd_knekk.py n4|9374|9387|n6 u0 v0 u1 v1 skala ut.png
"""
import sys

import numpy as np

import kd_lib as L
import kd_ovl as O
import kd_render as KR

if __name__ == "__main__":
    a = sys.argv[1:]
    name = a[0]
    box = tuple(int(v) for v in a[1:5])
    side = O.SIDE[name]
    C = L.C
    xs = [x for x in np.arange(5000.0, 7850.0, 100.0) if C.knuckle_drop(x) > 0.0]
    K = np.array([L.on_side(x, C.knuckle_z(x), side) for x in xs])
    cam, _w, _h = KR.cam_named(name)
    u, v, _ = cam.project(K)
    O.overlay(name, box, float(a[5]), a[6], extra=[(list(zip(u, v)), (0, 90, 255))])
