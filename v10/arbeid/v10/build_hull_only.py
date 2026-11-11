"""Bygger bare skroget (skrog-delen) fra en gitt repo-rot og eksporterer STL i baatkoordinater.

python build_hull_only.py <repo-rot> <ut.stl> [angTol=0.12] [linTol=0.018] [rel|abs] [stations=40]
Utdata: x fra baugen akterover, y tvers, z opp, modellskala (1:SCALE), kjolen paa z=0.
"""
import os, sys, time
root, out = sys.argv[1], sys.argv[2]
ang = float(sys.argv[3]) if len(sys.argv) > 3 else 0.12
lin = float(sys.argv[4]) if len(sys.argv) > 4 else 0.018
rel = (sys.argv[5] != "abs") if len(sys.argv) > 5 else True
nst = int(sys.argv[6]) if len(sys.argv) > 6 else 40
sys.path.insert(0, root)
from hr26 import build as B  # noqa: E402
t = time.time()
w = B.build_hull(hollow=True, n_stations=nst)
print(f"bygget {time.time()-t:.0f}s", flush=True)
m = B.to_model(w)
bb = m.val().BoundingBox()
m = m.translate((-bb.xmin, -(bb.ymin + bb.ymax) / 2.0, -bb.zmin))
m.val().exportStl(out, lin, ang, False, rel)
print(f"eksportert {out} {os.path.getsize(out)/1e6:.1f} MB  {time.time()-t:.0f}s", flush=True)
