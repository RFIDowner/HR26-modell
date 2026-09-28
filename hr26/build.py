"""Bygger hele modellen og eksporterer STEP og printklare STL-er.

  python -m hr26.build              # alt
  python -m hr26.build --hull       # bare skroget (raskt under utvikling)
  python -m hr26.build --no-hollow  # massivt skrog

Koordinater under bygging: x fra baugen og akterover, y halvbredde,
z fra konstruksjonsvannlinjen - alt i FULLSKALA millimeter. Helt til
slutt skaleres alt med 1/SCALE og legges ned paa byggeplaten.
"""
from __future__ import annotations

import argparse
import math
import os
import time

import cadquery as cq

from . import appendages as A
from . import curves as C
from . import deckhouse as D
from . import fittings as F
from . import hull as H
from . import params as P
from . import plaque as PL
from . import rig as R
from . import shell as S
from . import stand as ST

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
STL_DIR = os.path.join(ROOT, "export", "stl")
STEP_DIR = os.path.join(ROOT, "export", "step")

BED = 256.0           # Bambu Lab A1
BED_MARGIN = 1.5      # sikkerhetsmargin i modell-mm


# --------------------------------------------------------------- bygging
def build_hull(hollow: bool = True, n_stations: int = 40, n_pts: int = 26, log=print):
    t0 = time.time()

    def step(name, wp):
        log(f"  {name:<22s} {time.time() - t0:5.0f}s")
        return wp

    w = cq.Workplane("XY").newObject([H.hull_solid(n_stations, n_pts)])
    step("skrog loftet", w)

    w = w.union(A.keel())
    step("kjol", w)
    w = w.union(D.coaming_block())
    step("cockpitkarm", w)
    w = w.union(D.coachroof())
    step("ruff", w)
    w = w.union(D.sprayhood())
    step("sprayhood", w)
    w = w.union(F.additions())
    step("dekksbeslag", w)

    w = w.cut(D.cockpit_cut())
    step("cockpit utskaaret", w)
    w = w.cut(D.companionway_cut())
    w = w.cut(D.fore_hatch())
    w = w.cut(D.coach_windows())
    step("luker og vinduer", w)
    w = w.cut(F.cuts())
    step("hull for rigg og rekke", w)

    if hollow:
        w = S.hollow(w)
        step("uthult", w)
        log(f"  plastforbruk (skall): {S.material_cm3(w):.0f} cm3")
    return w


def build_parts(hollow: bool = True, **kw):
    """Alle deler i fullskala, i byggekoordinater."""
    parts = {"skrog": build_hull(hollow=hollow, **kw)}
    parts["ror"] = A.rudder()
    parts.update(R.parts())
    parts.update(ST.parts())
    parts.update(PL.parts())
    return parts


# ------------------------------------------------------- print-plassering
def to_model(wp: cq.Workplane) -> cq.Workplane:
    """Fullskala -> modellskala."""
    return wp.newObject([wp.val().scale(1.0 / P.SCALE)])


def lay_flat(wp: cq.Workplane, rotate_z: float = 0.0) -> cq.Workplane:
    """Roterer om Z, legger delen paa z=0 og sentrerer den i origo."""
    if rotate_z:
        wp = wp.rotate((0, 0, 0), (0, 0, 1), rotate_z)
    bb = wp.val().BoundingBox()
    return wp.translate(
        (-(bb.xmin + bb.xmax) / 2.0, -(bb.ymin + bb.ymax) / 2.0, -bb.zmin)
    )


def best_bed_angle(wp: cq.Workplane) -> float:
    """Finner rotasjonen om Z som gir minst fotavtrykk paa platen."""
    best, best_fit = 0.0, 1e9
    for deg in range(0, 91, 1):
        bb = wp.rotate((0, 0, 0), (0, 0, 1), deg).val().BoundingBox()
        fit = max(bb.xlen, bb.ylen)
        if fit < best_fit:
            best, best_fit = float(deg), fit
    return best


def fits_bed(wp: cq.Workplane):
    bb = wp.val().BoundingBox()
    ok = (
        bb.xlen <= BED - BED_MARGIN
        and bb.ylen <= BED - BED_MARGIN
        and bb.zlen <= BED - BED_MARGIN
    )
    return ok, (bb.xlen, bb.ylen, bb.zlen)


# ----------------------------------------------------------------- export
def export(parts: dict, log=print):
    os.makedirs(STL_DIR, exist_ok=True)
    os.makedirs(STEP_DIR, exist_ok=True)
    # rydd bort STL-er fra forrige bygg, ellers blir gammel nummerering staaende
    for f in os.listdir(STL_DIR):
        if f.endswith(".stl"):
            os.remove(os.path.join(STL_DIR, f))

    # rotasjoner som legger delen gunstig paa platen: liste av (akse, grader)
    ROT = {
        "ror": [("Y", 90.0)],
        "rekkepaaler": [("Y", 90.0)],
        "stativ-vugge1": [("Y", 90.0)],
        "stativ-vugge2": [("Y", 90.0)],
    }
    # mastene: lengden langs X, den brede 4 mm-siden ned, 3 mm hoy
    for name in parts:
        if name.startswith("mast-"):
            ROT[name] = [("X", 90.0), ("Z", 90.0)]
    AXIS = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}

    order = [
        "skrog",
        "ror",
        *sorted(n for n in parts if n.startswith("mast-")),
        "mastefot",
        "masttopp",
        "saling",
        "bom",
        "bom-med-seil",
        "rekkepaaler",
        "boyemal",
        "stativ-vugge1",
        "stativ-vugge2",
        "stativ-bjelke",
        "skilt",
    ]
    names = [n for n in order if n in parts] + [n for n in parts if n not in order]

    report = []
    for i, name in enumerate(names, start=1):
        wp = to_model(parts[name])
        for axis, deg in ROT.get(name, []):
            wp = wp.rotate((0, 0, 0), AXIS[axis], deg)
        # legg delen rett paa platen; passer den ikke slik, prov aa dreie den
        ang = 0.0
        flat = lay_flat(wp, 0.0)
        ok, dims = fits_bed(flat)
        if not ok or name == "skrog":
            best = best_bed_angle(wp)
            turned = lay_flat(wp, best)
            ok2, dims2 = fits_bed(turned)
            if ok2 or name == "skrog":
                ang, flat, ok, dims = best, turned, ok2, dims2
        wp = flat
        fn = os.path.join(STL_DIR, f"{i:02d}_{name}.stl")
        cq.exporters.export(wp, fn, tolerance=0.018, angularTolerance=0.12)
        report.append((name, dims, ang, ok, fn))
        log(
            f"  {name:<16s} {dims[0]:6.1f} x {dims[1]:6.1f} x {dims[2]:6.1f} mm"
            f"  rot {ang:4.0f} gr  {'OK' if ok else 'trenger storre plate enn A1'}"
        )

    asm = cq.Assembly()
    for name, wp in parts.items():
        asm.add(to_model(wp), name=name)
    asm.save(os.path.join(STEP_DIR, "hr26.step"))
    log(f"  STEP: {os.path.join(STEP_DIR, 'hr26.step')}")
    return report


def main():
    ap = argparse.ArgumentParser(description="Bygger HR 26-modellen")
    ap.add_argument("--hull", action="store_true", help="bare skroget")
    ap.add_argument("--no-hollow", action="store_true", help="massivt skrog")
    ap.add_argument("--stations", type=int, default=40)
    args = ap.parse_args()

    print(f"HR 26 i 1:{P.SCALE:.0f}  (LOA {P.LOA / P.SCALE:.1f} mm)")
    t = time.time()
    if args.hull:
        parts = {"skrog": build_hull(hollow=not args.no_hollow, n_stations=args.stations)}
    else:
        parts = build_parts(hollow=not args.no_hollow, n_stations=args.stations)
    print(f"Bygget paa {time.time() - t:.0f}s. Eksporterer:")
    export(parts)
    print(
        f"Mast: {R.mast_length_model_mm():.0f} mm synlig, ovalt "
        f"{P.MAST_SECTION_X / P.SCALE:.1f} x {P.MAST_SECTION_Y / P.SCALE:.1f} mm "
        f"(hull {P.MAST_HOLE_X / P.SCALE:.1f} x {P.MAST_HOLE_Y / P.SCALE:.1f} mm). "
        f"To varianter: med {P.MAST_SOCKET / P.SCALE:.0f} mm sokkel (trenger storre plate) "
        f"og uten sokkel (passer A1 diagonalt)."
    )
    print(f"Ferdig paa {time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
