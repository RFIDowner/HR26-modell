import sys, time, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import load_raw, weld, look, raster, face_normals, corner_normals, shade2, components
t = time.time()
V, F = weld(load_raw(sys.argv[1]))
lab = components(len(V), F); ul, cnt = np.unique(lab, return_counts=True); F = F[lab == ul[np.argmax(cnt)]]
fn, area = face_normals(V, F); keep = area > 1e-12; F, fn = F[keep], fn[keep]
print("prep", f"{time.time()-t:.1f}s", len(F)); t = time.time()
cn = corner_normals(V, F, fn); print("cn", f"{time.time()-t:.1f}s"); t = time.time()
R = look(148.0, 14.0); rr = raster(V, F, R, 790); print("raster", f"{time.time()-t:.1f}s")
