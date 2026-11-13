"""Lid on the stage (after the deck-line fix): validity, volume, precise overlap and minimum distance to lip and collar."""
import sys, time
sys.path.insert(0, sys.argv[1])
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from hr26 import params as P, cabin as CB
def pvol(s):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, g, 1e-6, False); return g.Mass()
t0 = time.time()
lid = CB.lid().val(); print(f"lid valid {lid.isValid()} solids {len(lid.Solids())} vol {pvol(lid)/P.SCALE**3/1000:.2f} cm3 model [{time.time()-t0:.0f}s]", flush=True)
for name, f in (("lip", CB.lip),) if len(sys.argv) > 2 else (("lip", CB.lip), ("collar", CB.collar)):
    o = f().val()
    ov = pvol(lid.intersect(o)) if lid.intersect(o).Solids() else 0.0
    d = BRepExtrema_DistShapeShape(lid.wrapped, o.wrapped); d.Perform()
    p = d.PointOnShape1(1)
    print(f"{name}: overlap {ov:.1f} mm3 full; min distance {d.Value():.3f} mm full ({d.Value()/P.SCALE:.3f} mm model) at ({p.X():.0f},{p.Y():.0f},{p.Z():.0f}) [{time.time()-t0:.0f}s]", flush=True)
print("split plane a,b:", CB.split_plane())
