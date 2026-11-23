import sys, time
sys.path.insert(0, sys.argv[1])
import cadquery as cq
from hr26 import build as B, hull as H
s = H.hull_solid(40, 26)
w = cq.Workplane("XY").newObject([s])
faces = s.Faces()
print("flater:", len(faces))
cand = []
for f in faces:
    c = f.Center(); n = f.normalAt(c)
    bb = f.BoundingBox()
    if bb.xmin > 7600 and n.x > 0.8:
        cand.append((f, c, n, bb))
for f, c, n, bb in cand:
    print(f"akterspeilflate? senter {c.x:.0f},{c.y:.0f},{c.z:.0f} n=({n.x:.2f},{n.y:.2f},{n.z:.2f}) bb z {bb.zmin:.0f}-{bb.zmax:.0f} y {bb.ymin:.0f}-{bb.ymax:.0f} kanter {len(f.Edges())}")
    for e in f.Edges():
        eb = e.BoundingBox()
        print(f"   kant z {eb.zmin:.0f}-{eb.zmax:.0f} y {eb.ymin:.0f}-{eb.ymax:.0f} x {eb.xmin:.0f}-{eb.xmax:.0f} L={e.Length():.0f}")
tf = max(cand, key=lambda t: t[3].ylen * t[3].zlen)[0] if cand else None
if tf is not None:
    top = [e for e in tf.Edges() if e.BoundingBox().zmin > 850]
    print("toppkanter:", len(top))
    for r in (20.0, 15.0, 10.0):
        try:
            out = s.fillet(r, top)
            print(f"fillet {r}: valid={out.isValid()} dV={out.Volume()-s.Volume():.3e}")
        except Exception as e:
            print(f"fillet {r}: feil {type(e).__name__} {e}")
print("--- bare den lange toppkanten")
mid = [e for e in tf.Edges() if e.Length() > 1000 and e.BoundingBox().zmin > 900]
for r in (20.0, 12.0, 8.0):
    try:
        out = s.fillet(r, mid)
        print(f"fillet {r}: valid={out.isValid()} dV={out.Volume()-s.Volume():.3e}")
    except Exception as e:
        print(f"fillet {r}: feil {type(e).__name__}")
print("--- chamfer paa den lange")
for r in (15.0, 10.0):
    try:
        out = s.chamfer(r, None, mid)
        print(f"chamfer {r}: valid={out.isValid()} dV={out.Volume()-s.Volume():.3e}")
    except Exception as e:
        print(f"chamfer {r}: feil {type(e).__name__}")
