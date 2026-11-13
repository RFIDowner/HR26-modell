"""Proevebiter foer det store skroget: print dem og sjekk paa en time det som
ellers foerst vises etter 16 timer.

  python tools/memcap.py --gb 7 --lock -- python tools/proevebiter.py

Lager tre STL-er i export/test/ (ikke i export/stl, saa delnumrene staar):

* test-vindusbro.stl: et stykke av skrogsiden rundt styrbord vindu, med
  sidedekket som bygger bro over den aapne aapningen (ca. 42 mm i 1:30).
  Printes staaende som i skroget, med brim. Henger broen, sett
  WIN_TIE = True i hr26/params.py.
* test-lokk-skrog.stl og test-lokk-tak.stl: fremste del av aapningen i
  dekket med kanten, og fremste del av ruff-taket med sporet. Sjekk at
  taket glir ned over kanten (klaring 0,22-0,25 mm) uten slark.

Bitene er skaaret ut av de ferdige delene, saa de er like de ekte.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

import cadquery as cq  # noqa: E402

from hr26 import build as B  # noqa: E402
from hr26 import cabin as CB  # noqa: E402
from hr26 import curves as C  # noqa: E402
from hr26 import params as P  # noqa: E402

OUT = os.path.join(B.ROOT, "export", "test")


def _box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def _one(w: cq.Workplane, what: str) -> cq.Workplane:
    s = w.val().Solids()
    if not s:
        raise RuntimeError(f"{what}: tomt utsnitt")
    big = max(s, key=lambda v: v.Volume())
    if len(s) > 1:
        print(f"  {what}: beholdt den stoerste av {len(s)} biter")
    return cq.Workplane("XY").newObject([big])


def _save(w: cq.Workplane, name: str, rot_y: float = 0.0):
    m = B.to_model(w)
    if rot_y:
        m = m.rotate((0, 0, 0), (0, 1, 0), rot_y)
    m = B.lay_flat(m)
    bb = m.val().BoundingBox()
    fn = os.path.join(OUT, name)
    B.write_stl(m, fn)
    print(f"  {name:22s} {bb.xlen:6.1f} x {bb.ylen:5.1f} x {bb.zlen:5.1f} mm  "
          f"{m.val().Volume() / 1000.0:5.2f} cm3")


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    if not P.CABIN:
        raise SystemExit("CABIN er av i params.py: ingen kahytt, lokk eller aapne vinduer aa teste")
    hull = B.build_hull(hollow=True)
    print(f"skroget bygget ({time.time() - t0:.0f} s)")

    # vindusbroen: styrbord vindu med 150 mm skrog paa hver side, fra litt
    # under vinduet til over dekket
    xm = 0.5 * (P.WIN_X0 + P.WIN_X1)
    hb = C.deck_half_breadth(xm)
    z_deck = C.sheer_z(xm)
    win = hull.intersect(_box(P.WIN_X0 - 150.0, P.WIN_X1 + 150.0, hb - 420.0, hb + 200.0,
                              z_deck - 330.0, z_deck + 200.0))
    _save(_one(win, "vindusbro"), "test-vindusbro.stl")

    # lokkets fremre hjoerne: fra spissen av aapningen 450 mm akterover
    x0 = CB.opening_planform().p[0, 0] - 250.0
    x1 = x0 + 700.0
    zc = C.deck_z(x0 + 350.0, 0.0)
    box = _box(x0, x1, -900.0, 900.0, zc - 90.0, zc + 900.0)
    _save(_one(hull.intersect(box), "lokk-skrog"), "test-lokk-skrog.stl")
    lid = CB.lid()
    _save(_one(lid.intersect(box), "lokk-tak"), "test-lokk-tak.stl", rot_y=CB.print_tilt_deg())
    print(f"ferdig ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
