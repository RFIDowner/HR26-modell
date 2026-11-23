import os, sys, time
import cadquery as cq
src, pre = sys.argv[1], sys.argv[2]
s = cq.Shape.importBrep(src)
for a in sys.argv[3:]:
    lin, ang = (float(v) for v in a.split(":"))
    fn = f"{pre}_{lin:g}_{ang:g}.stl"
    t = time.time()
    s.exportStl(fn, lin, ang, False, False)
    print(f"{fn} {os.path.getsize(fn)/1e6:.1f} MB {time.time()-t:.0f}s", flush=True)
