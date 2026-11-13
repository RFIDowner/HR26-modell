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
from . import cabin as CB
from . import curves as C
from . import deckhouse as D
from . import fittings as F
from . import hull as H
from . import interior as I
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

# STL-eksport med ABSOLUTT toleranse (modell-mm og radianer). CadQuerys
# standard er relativ toleranse, som gjorde den 263 mm lange dekkskanten til
# 16 rette stykker med knekk i hvert punkt (V10-analysen).
STL_TOL = 0.02
STL_ANG = 0.12        # 0,02 mm / 0,12 rad (V10 trinn 4, foer 0,15): finere i de krumme
                      # laaringene akter; ca. 23 MB for skroget

# Faste delnumre, saa et delvis bygg (--only) ikke endrer nummereringen.
PART_NO = {
    "skrog": 1, "ror": 2, "mast-354mm-A1": 3, "mast-365mm-ikke-A1": 4,
    "mastefot": 5, "masttopp": 6, "saling": 7, "bom": 8, "bom-med-seil": 9,
    "rekkepaaler": 10, "boyemal": 11, "stativ-vugge1": 12, "stativ-vugge2": 13,
    "stativ-bjelke": 14, "skilt": 15, "ruff-tak": 16,
}


# ------------------------------------------------- robuste boolske operasjoner
DEBRIS_CM3 = 0.001     # 1 mm3 i 1:30: mindre loesrevne biter etter et kutt er fliser
NUDGES = (0.0, 0.37, -0.37, 0.73, -0.73)   # smaa forskyvninger i x, fullskala-mm


def _n_solids(wp) -> int:
    return len(wp.val().Solids())


def _volume(wp) -> float:
    """Volum med toleranse. OCCs vanlige Volume() kan bomme med titalls liter
    paa trimmede B-spline-flater (glatte lofter som fenderlisten, kjolen og
    det rundede akterspeilet) og gi falske avvisninger i robust_union. Den
    presise beregningen tar flere titalls sekunder, saa den brukes bare
    naar den raske sier nei."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(wp.val().wrapped, g, 1e-6, False)
    return g.Mass()


def robust_union(base, part, what: str):
    """Union som nekter aa feile i stillhet.

    OCC kan returnere begge delene som separate solider - eller miste den
    ene - naar en flate i den ene delen faller noyaktig paa en soem i den
    andre. Det skjedde for ruffen mot skroget ved enkelte stasjonstall.
    Vi provde derfor smaa forskyvninger av delen, og gir opp hoylytt om
    ingen av dem gir ett sammenhengende volum.
    """
    before = _n_solids(base)
    for dx in NUDGES:
        cand = base.union(part.translate((dx, 0.0, 0.0)) if dx else part)
        if _n_solids(cand) <= before and (
            cand.val().Volume() > base.val().Volume() + 1.0
            or _volume(cand) > _volume(base) + 1.0       # treg, men presis
        ):
            return cand
    raise RuntimeError(f"union av '{what}' ga ikke ett volum - delen ville falt bort")


def robust_cut(base, cutter, what: str, strict: bool = False):
    """Kutt som nekter aa feile i stillhet. OCC kan gi et tomt resultat
    (0 solider) eller et ugyldig volum uten feilmelding; da stopper vi.
    `strict` krever ogsaa et gyldig volum (brukes for kahytten)."""
    before = _n_solids(base)
    out = base.cut(cutter)
    n = _n_solids(out)
    if n == 0:
        raise RuntimeError(f"kutt '{what}' ga et tomt resultat")
    if n > before:
        # Loesrevne fliser uten volum (flater som nesten faller sammen) kastes;
        # alt med mer enn DEBRIS_CM3 volum er en ekte deling og stopper bygget.
        sol = sorted(out.val().Solids(), key=lambda s: -s.Volume())
        tiny = [s for s in sol[before:] if s.Volume() < DEBRIS_CM3 * 1000.0 * P.SCALE ** 3]
        if len(tiny) == n - before:
            print(f"  kutt '{what}': kastet {len(tiny)} loesreven(e) flis(er) uten volum "
                  f"({sum(s.Volume() for s in tiny) / P.SCALE ** 3:.4f} mm3 i 1:30)")
            out = cq.Workplane("XY").newObject(
                [sol[0] if before == 1 else cq.Compound.makeCompound(sol[:before])])
            n = before
        else:
            raise RuntimeError(f"kutt '{what}' delte modellen i {n} biter")
    if strict and not out.val().isValid():
        raise RuntimeError(f"kutt '{what}' ga et ugyldig volum")
    return out


# --------------------------------------------------------------- bygging
def build_hull(hollow: bool = True, n_stations: int = 40, n_pts: int = 26, log=print):
    t0 = time.time()

    def step(name, wp):
        log(f"  {name:<22s} {time.time() - t0:5.0f}s")
        return wp

    w = cq.Workplane("XY").newObject([H.hull_solid(n_stations, n_pts)])
    step("skrog loftet", w)

    w = robust_union(w, A.keel(), "kjol")
    step("kjol", w)
    name = F.transom_name()
    if name is not None:
        # foer fenderlisten: etterpaa gir unionen et korrupt volum
        w = robust_union(w, name, "navn paa akterspeilet")
        step("navn", w)
    w = robust_union(w, H.rubbing_strake(), "fenderlist")
    step("fenderlist", w)
    w = H.round_transom_top(w)
    step("akterspeilets overkant", w)
    if P.CABIN:
        # Ruffen er et eget lokk (16_ruff-tak, cabin.lid). Paa skroget staar
        # bare kragen under skjoeten (ruff og sprayhood kappet ved
        # skjoeteflaten) og kanten lokket tres over. (Aa unionere hele ruffen
        # og saa skjaere bort lokket ga en kant med 93 mm toleranse ved
        # x 5574, der sprayhood, ruff og karm moeter skjoeteflaten, og alle
        # boolske operasjoner etterpaa feilet - kontroll 13.11.)
        w = robust_union(w, D.coaming_block(), "cockpitkarm")
        w = robust_union(w, CB.collar(), "krage og kant for lokket")
        w = robust_union(w, D.vents(where_only="deck"), "ventil paa dekket")
        step("krage, kant og karm", w)
    else:
        w = robust_union(w, D.coachroof(), "ruff")
        step("ruff", w)
        w = robust_union(w, D.hatches(), "luker")
        w = robust_union(w, D.vents(), "ventiler")
        step("luker og ventiler", w)
        w = robust_union(w, D.coaming_block(), "cockpitkarm")
        w = robust_union(w, D.sprayhood(), "sprayhood")
        step("karm og sprayhood", w)
    w = robust_union(w, F.additions(), "dekksbeslag")
    step("dekksbeslag", w)

    w = robust_cut(w, D.cockpit_cut(), "cockpit")
    w = robust_cut(w, D.companionway_cut(), "nedgang")
    win_cut, win_keep = D.hull_windows()
    w = robust_cut(w, win_cut, "vinduer")
    step("cockpit, nedgang, vinduer", w)
    w = robust_cut(w, F.cuts(), "hull for rigg og rekke")
    step("hull for rigg og rekke", w)
    if P.CABIN:
        # aapningen i dekket innenfor kanten, som eget kutt foer uthulingen
        w = robust_cut(w, I.opening_cut(), "aapning i dekket", strict=True)
        # nedgangen i lokket ser ned i kahytten, ikke paa terskelen
        w = robust_cut(w, CB.companion_slot(), "nedgang ned i kahytten", strict=True)
        step("aapning i dekket", w)
    if _n_solids(w) != 1:
        raise RuntimeError(f"skroget bestaar av {_n_solids(w)} solider etter sammenstilling")

    if hollow:
        # spares fra uthulingen: cockpitkaret (gulv og vegger), veggen bak
        # vinduene og soylen under masten - og med kahytt hele kahyttens
        # omraade, som er massivt rundt hulrommet (interior.py)
        keep = [D.cockpit_tub(P.HULL_WALL), win_keep, D.mast_post()]
        if P.CABIN:
            keep.append(I.keep_block())
        w = S.hollow(w, keep=keep)
        step("uthult", w)
    if P.CABIN:
        # kahytten med innredning, aapningen i dekket og doerene; saa
        # vinduene som aapninger gjennom veggen (etter hulrommet, saa de
        # bare gaar gjennom veggen)
        w = robust_cut(w, I.cabin_void(log=log, with_opening=False), "kahytt og innredning",
                       strict=True)
        step("kahytt", w)
        w = robust_cut(w, I.window_holes(), "aapne vinduer", strict=True)
        step("aapne vinduer", w)
    if hollow or P.CABIN:
        log(f"  plastforbruk (skall og innredning): {S.material_cm3(w):.0f} cm3")
    return w


def build_parts(hollow: bool = True, only=None, **kw):
    """Alle deler i fullskala, i byggekoordinater. `only` er et sett med
    delnavn; da bygges bare de."""
    def want(name):
        return not only or name in only

    parts = {}
    if want("skrog"):
        parts["skrog"] = build_hull(hollow=hollow, **kw)
    if want("ror"):
        parts["ror"] = A.rudder()
    if P.CABIN and want("ruff-tak"):
        parts["ruff-tak"] = CB.lid()
    for src in (R.parts, ST.parts, PL.parts):
        parts.update({k: v for k, v in src().items() if want(k)})
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
def _part_no(name: str, fallback: int) -> int:
    return PART_NO.get(name, fallback)


def write_stl(wp: cq.Workplane, fn: str):
    """Alle solidene i `wp` som en STL, med absolutt toleranse."""
    shapes = [v for v in wp.vals() if isinstance(v, cq.Shape)]
    shape = shapes[0] if len(shapes) == 1 else cq.Compound.makeCompound(shapes)
    shape.exportStl(fn, STL_TOL, STL_ANG, False, False)
    _drop_collapsed_triangles(fn)


STL_WELD = 1e-4       # modell-mm (0,1 mikrometer): punkter naermere enn dette er samme punkt
                      # (samme toleranse som tools/meshcheck.py)


def _drop_collapsed_triangles(fn: str) -> int:
    """Fjerner trekanter der to hjoerner er samme punkt (null areal).

    OCC-trianguleringen lager av og til slike ved soemmer (f.eks. overkanten
    av akterspeilet). De gjoer nettet ikke-manifold (kanten brukes tre-fire
    ganger) uten aa ha noe volum. Punktene skrives sveiset (STL_WELD), saa
    alle programmer ser de samme hjoernene. Returnerer antall fjernet."""
    import numpy as np

    with open(fn, "rb") as f:
        head = f.read(84)
        n = int.from_bytes(head[80:84], "little")
        rec = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        a = np.frombuffer(f.read(n * 50), dtype=rec).copy()
    q = np.round(a["v"].reshape(-1, 3).astype(np.float64) / STL_WELD).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True)
    t = inv.reshape(-1, 3)
    keep = (t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])
    a["v"] = (q * STL_WELD).reshape(-1, 3, 3).astype(np.float32)
    a = a[keep]
    with open(fn, "wb") as f:
        f.write(head[:80] + int(len(a)).to_bytes(4, "little"))
        f.write(a.tobytes())
    return int((~keep).sum())


def export(parts: dict, log=print, partial: bool = False):
    os.makedirs(STL_DIR, exist_ok=True)
    os.makedirs(STEP_DIR, exist_ok=True)
    # Rydd bort STL-er fra forrige bygg, ellers blir gammel nummerering
    # staaende. Ved et delvis bygg ryddes bare de delene som bygges.
    mine = {f"{_part_no(n, 0):02d}_{n}.stl" for n in parts}
    for f in os.listdir(STL_DIR):
        if f.endswith(".stl") and (not partial or f in mine):
            os.remove(os.path.join(STL_DIR, f))

    # rotasjoner som legger delen gunstig paa platen: liste av (akse, grader)
    ROT = {
        "ror": [("Y", 90.0)],
        "rekkepaaler": [("Y", 90.0)],
        "stativ-vugge1": [("Y", 90.0)],
        "stativ-vugge2": [("Y", 90.0)],
        # lokket staar paa skjoeteplanet, som heller litt for-akter
        "ruff-tak": [("Y", CB.print_tilt_deg())],
    }
    # mastene: lengden langs X, den brede 4 mm-siden ned, 3 mm hoy
    for name in parts:
        if name.startswith("mast-"):
            ROT[name] = [("X", 90.0), ("Z", 90.0)]
    AXIS = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}

    order = [
        "skrog",
        "ruff-tak",
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
    for k, name in enumerate(names, start=1):
        i = _part_no(name, 100 + k)
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
        write_stl(wp, fn)
        report.append((name, dims, ang, ok, fn))
        log(
            f"  {name:<16s} {dims[0]:6.1f} x {dims[1]:6.1f} x {dims[2]:6.1f} mm"
            f"  rot {ang:4.0f} gr  {'OK' if ok else 'trenger storre plate enn A1'}"
            f"  {os.path.getsize(fn) / 1e6:5.1f} MB"
        )

    if partial:
        return report
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
    ap.add_argument("--only", default="",
                    help="kommaliste med deler, f.eks. skrog,stativ-vugge1,stativ-vugge2;"
                         " andre STL-er blir liggende")
    args = ap.parse_args()

    print(f"HR 26 i 1:{P.SCALE:.0f}  (LOA {P.LOA / P.SCALE:.1f} mm)")
    t = time.time()
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    if args.hull:
        only = {"skrog"}
    parts = build_parts(hollow=not args.no_hollow, only=only or None, n_stations=args.stations)
    print(f"Bygget paa {time.time() - t:.0f}s. Eksporterer:")
    export(parts, partial=bool(only))
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
