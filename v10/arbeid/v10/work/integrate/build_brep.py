"""Bygger det integrerte skroget (V10) og lagrer BREP i fullskala byggekoordinater
og i modellskala baatkoordinater (x fra baugtuppen, kjolen paa z=0).

python build_brep.py <repo-rot> <utmappe> [stations=40]
"""
import os, sys, time
root, outdir = sys.argv[1], sys.argv[2]
nst = int(sys.argv[3]) if len(sys.argv) > 3 else 40
sys.path.insert(0, root)
from hr26 import build as B  # noqa: E402
t = time.time()
w = B.build_hull(hollow=True, n_stations=nst)
print(f"bygget {time.time()-t:.0f}s", flush=True)
s = w.val()
print("solids", len(w.val().Solids()), "valid", s.isValid(), flush=True)
s.exportBrep(os.path.join(outdir, "hull_full.brep"))
m = B.to_model(w)
bb = m.val().BoundingBox()
print("model bbox", bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax, flush=True)
m = m.translate((-bb.xmin, -(bb.ymin + bb.ymax) / 2.0, -bb.zmin))
m.val().exportBrep(os.path.join(outdir, "hull_model_boat.brep"))
print(f"ferdig {time.time()-t:.0f}s", flush=True)
