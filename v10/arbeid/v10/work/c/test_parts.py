import sys, time
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
from hr26 import deckhouse as D, fittings as F, params as P
OUT = "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/c/parts/"
which = sys.argv[1:] or ["coachroof", "sprayhood", "coaming_block", "hatches", "winches", "cleats", "stemhead"]
print("roof_z(3400) =", D.roof_z(3400.0), " roof_z(2735)", D.roof_z(2735.0), "roof_z(4646)", D.roof_z(4646.0))
for name in which:
    t = time.time()
    fn = getattr(D, name, None) or getattr(F, name)
    try:
        wp = fn()
        s = wp.val()
        print(f"{name:14s} valid={s.isValid()} solids={len(wp.solids().vals())} V={s.Volume()/1e9:.4f} m3 t={time.time()-t:.1f}s bb={s.BoundingBox().xmin:.0f}..{s.BoundingBox().xmax:.0f} y {s.BoundingBox().ymin:.0f}..{s.BoundingBox().ymax:.0f} z {s.BoundingBox().zmin:.0f}..{s.BoundingBox().zmax:.0f}", flush=True)
        s.exportStl(OUT + name + ".stl", 1.0, 0.1, False, False)
    except Exception as e:
        import traceback; traceback.print_exc()
        print(name, "FEIL", e, f"t={time.time()-t:.1f}s")
