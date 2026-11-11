import sys, time
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines")
import numpy as np
import cadquery as cq
from hr26 import shell as S, params as P, curves as C
t = time.time()
bays = S.compartments()
print("bays", len(bays), f"{time.time()-t:.1f}s")
b0 = bays[0].val()
print("bay0 valid", b0.isValid(), "faces", len(b0.Faces()), "vol", b0.Volume())
fn = "bay0.stl"
b0.scale(1/30).exportStl(fn, 0.01, 0.05, False, False)
import struct
d = open(fn, "rb").read(); n = struct.unpack("<I", d[80:84])[0]
rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
T = rec["v"].astype(np.float64)
ar = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
print("bay0 tris", n, "degenerate", int((ar < 1e-10).sum()))
for i, f in enumerate(b0.Faces()):
    bb = f.BoundingBox()
    print(i, f.geomType(), f"x {bb.xmin:.0f}-{bb.xmax:.0f} z {bb.zmin:.0f}-{bb.zmax:.0f} area {f.Area():.0f}")
