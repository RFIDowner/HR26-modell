"""Hull segment x 1000-6300 through build_hull's CABIN order (patched code), with
point probes. Usage: cad_seg.py <wc> a|b   (b loads segk_a.brep)"""
import sys, time, os
WC, part = sys.argv[1], sys.argv[2]
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/out"
sys.path.insert(0, WC)
import numpy as np, cadquery as cq
from OCP.BRep import BRep_Tool
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
from hr26 import params as P, hull as H, interior as I, deckhouse as D, build as B, shell as S, cabin as CB, fittings as F, curves as C
t0 = time.time()


def log(m):
    print(f"[{time.time() - t0:6.1f}s] {m}", flush=True)


def info(w, what):
    v = w.val(); mt = max(BRep_Tool.Tolerance_s(e.wrapped) for e in v.Edges())
    log(f"{what}: valid={v.isValid()} solids={len(v.Solids())} vol={v.Volume() / P.SCALE ** 3 / 1000:.2f} cm3 maxEdgeTol={mt:.3f}")


def probe(w, lab, p, exp):
    st = BRepClass3d_SolidClassifier(w.val().wrapped, gp_Pnt(*p), 1e-3).State()
    inside = st == TopAbs_IN
    print(f"PROBE {lab:42s} {'IN ' if inside else 'OUT'} expected {'IN ' if exp else 'OUT'} "
          f"{'ok' if inside == exp else 'MISMATCH'}", flush=True)


if part == "a":
    xs = np.linspace(1000.0, 6300.0, 34)
    w = cq.Workplane("XY").newObject([cq.Solid.makeLoft([H._section_wire(float(x)) for x in xs], ruled=False)]); info(w, "segment (no keel)")
    from hr26 import appendages as A
    w = B.robust_union(w, A.keel(), "kjol")
    info(w, "segment")
    w = B.robust_union(w, D.coaming_block(), "cockpitkarm"); info(w, "karm")
    w = B.robust_union(w, CB.collar(), "krage og kant for lokket"); info(w, "krage og kant")
    w = B.robust_union(w, D.vents(where_only="deck"), "ventil paa dekket"); info(w, "ventil")
    # F.additions skipped: stemhead and two cleats lie outside the segment
    w = B.robust_cut(w, D.cockpit_cut(), "cockpit")
    w = B.robust_cut(w, D.companionway_cut(), "nedgang")
    win_cut, win_keep = D.hull_windows()
    w = B.robust_cut(w, win_cut, "vinduer"); info(w, "cockpit, nedgang, vinduer")
    w = B.robust_cut(w, F.cuts(), "hull for rigg og rekke"); info(w, "hull for rigg og rekke")
    w = B.robust_cut(w, I.opening_cut(), "aapning i dekket", strict=True); info(w, "aapning i dekket")
    if hasattr(CB, "companion_slot"):
        w = B.robust_cut(w, CB.companion_slot(), "nedgang ned i kahytten", strict=True); info(w, "nedgang ned i kahytten")
    w.val().exportBrep(os.path.join(OUT, "segk_a.brep"))
else:
    w = cq.Workplane("XY").newObject([cq.Shape.importBrep(os.path.join(OUT, "segk_a.brep"))])
    win_cut, win_keep = D.hull_windows()
    keep = [D.cockpit_tub(P.HULL_WALL), win_keep, D.mast_post(), I.keep_block()]
    w = S.hollow(w, keep=keep); info(w, "uthult")
    w = B.robust_cut(w, I.cabin_void(log=log, with_opening=False), "kahytt og innredning", strict=True); info(w, "kahytt")
    w = B.robust_cut(w, I.window_holes(), "aapne vinduer", strict=True); info(w, "aapne vinduer")
    log(f"plastforbruk segment {S.material_cm3(w):.0f} cm3")
    w.val().exportBrep(os.path.join(OUT, "segk_final.brep"))
    w.val().exportStl(os.path.join(OUT, "segk_final.stl"), 0.6, 0.15, False, False); log("saved")

sz = CB.split_z
lo, li = CB.lip_planforms()
ym = 0.5 * (lo.half_width(4000.0) + li.half_width(4000.0))
foot = D._coach_planform().half_width(4000.0)
probe(w, "lip x4000 mid", (4000.0, ym, sz(4000.0) + 20.0), True)
probe(w, "above lip x4000", (4000.0, ym, sz(4000.0) + 45.0), False)
probe(w, "collar ledge outside lip x4000", (4000.0, 0.5 * (lo.half_width(4000.0) + foot), sz(4000.0) - 5.0), True)
probe(w, "above collar ledge x4000", (4000.0, 0.5 * (lo.half_width(4000.0) + foot), sz(4000.0) + 5.0), False)
probe(w, "opening x4000 deck level", (4000.0, 0.0, C.deck_z(4000.0, 0.0) - 30.0), False)
probe(w, "threshold collar x5540 (slot: OUT)", (5540.0, 0.0, sz(5540.0) - 5.0), not hasattr(CB, "companion_slot"))
probe(w, "deck beside slot x5540 y400", (5540.0, 400.0, sz(5540.0) - 5.0), True)
probe(w, "coaming bar below notch x5620", (5620.0, 0.0, 1150.0), True)
if part == "b":
    probe(w, "void above top step x5540", (5540.0, 0.0, 800.0), False)
    probe(w, "top step x5540", (5540.0, 0.0, 735.0), True)
probe(w, "above threshold x5540", (5540.0, 0.0, sz(5540.0) + 5.0), False)
probe(w, "coaming notch x5620", (5620.0, 0.0, 1185.0), False)
probe(w, "coaming bar beside notch x5620 y500", (5620.0, 500.0, 1185.0), True)
probe(w, "post socket hole", (3400.0, 0.0, 1060.0), False if part == "b" else False)
probe(w, "below socket", (3400.0, 0.0, 1035.0), True)
probe(w, "post beside hole", (3400.0, 80.0, 1060.0), True if part == "b" else True)
probe(w, "above post top (cabin)", (3400.0, 0.0, 1100.0), False)
log("done")
# keel still attached and closed after the cabin cuts (probes in the keel and its root)
from hr26 import appendages as A2
kp = A2._KeelProfile()
probe(w, "keel mid-depth x4800", (4800.0, 0.0, -900.0), True)
probe(w, "keel root x4800 just below canoe body", (4800.0, 0.0, C.bottom_z(4800.0) - 30.0), True)
z0 = C.bottom_z(5700.0) - 20.0
le0, te0 = kp.edges(z0)
xp = 0.5 * (5662.0 + te0)
print(f"keel TE at z {z0:.0f}: {te0:.0f}; probe x {xp:.0f}")
probe(w, "keel TE root aft of keep_block (chamber region)", (xp, 0.0, z0), te0 > 5665.0)
probe(w, "saloon sole surface x4500 (void above)", (4500.0, 0.0, P.INT_SOLE_Z + 20.0), part != "b")
probe(w, "fill below sole x4500", (4500.0, 0.0, P.INT_SOLE_Z - 40.0), True)
