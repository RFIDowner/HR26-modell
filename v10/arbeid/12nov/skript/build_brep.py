"""Bygger skroget (som build_hull_only), lagrer BREP i baatkoordinater (modellskala)
og eksporterer STL med flere toleranser.
python build_brep.py <repo> <ut-prefiks> [lin:ang ...]"""
import os, sys, time
root, pre = sys.argv[1], sys.argv[2]
tols = [tuple(float(v) for v in a.split(":")) for a in sys.argv[3:]] or [(0.01, 0.1)]
sys.path.insert(0, root)
import cadquery as cq
from hr26 import build as B
t = time.time()
w = B.build_hull(hollow=True, n_stations=40)
print(f"bygget {time.time()-t:.0f}s", flush=True)
m = B.to_model(w)
bb = m.val().BoundingBox()
m = m.translate((-bb.xmin, -(bb.ymin + bb.ymax) / 2.0, -bb.zmin))
m.val().exportBrep(pre + ".brep")
for lin, ang in tols:
    fn = f"{pre}_{lin:g}_{ang:g}.stl"
    m.val().exportStl(fn, lin, ang, False, False)
    print(f"{fn} {os.path.getsize(fn)/1e6:.1f} MB {time.time()-t:.0f}s", flush=True)
