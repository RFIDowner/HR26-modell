"""Som build_hull_only.py, men sjekker ogsaa B-rep og lagrer BREP (fullskala).

python build_check.py <repo-rot> <ut-prefiks> [angTol] [linTol]
Lager <prefiks>.stl (modellskala, baatkoordinater, absolutt toleranse) og <prefiks>.brep.
"""
import os, sys, time
root, pre = sys.argv[1], sys.argv[2]
ang = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
lin = float(sys.argv[4]) if len(sys.argv) > 4 else 0.01
sys.path.insert(0, root)
from hr26 import build as B, params as P  # noqa: E402

t = time.time()
w = B.build_hull(hollow=True, n_stations=40, log=lambda s: print(s, flush=True))
s = w.val()
bb = s.BoundingBox()
print(f"bygget {time.time()-t:.0f}s  solider={len(s.Solids())} gyldig={s.isValid()} "
      f"V={s.Volume()/P.SCALE**3/1000:.1f} cm3 (modell)", flush=True)
print(f"bbox fullskala x {bb.xmin:.1f}..{bb.xmax:.1f}  y {bb.ymin:.1f}..{bb.ymax:.1f}  z {bb.zmin:.1f}..{bb.zmax:.1f}", flush=True)
s.exportBrep(pre + ".brep")
m = B.to_model(w)
ok, dims = B.fits_bed(B.lay_flat(m, B.best_bed_angle(m)))
print(f"A1 diagonalt: {ok} {dims}", flush=True)
mb = m.val().BoundingBox()
m = m.translate((-mb.xmin, -(mb.ymin + mb.ymax) / 2.0, -mb.zmin))
m.val().exportStl(pre + ".stl", lin, ang, False, False)
print(f"eksportert {pre}.stl {os.path.getsize(pre + '.stl')/1e6:.1f} MB  {time.time()-t:.0f}s", flush=True)
