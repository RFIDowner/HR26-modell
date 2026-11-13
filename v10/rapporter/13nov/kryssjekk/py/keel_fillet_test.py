"""On one stage: keel with several KEEL_FILLET values -> exposed root width,
ledge at the widest flare ring, and union with a hull segment (x 2950-6150,
H._section_wire sections like the undervann CAD test).

usage: python keel_fillet_test.py <stage_dir> <tag> 90,45,20,0
"""
import sys, json, time
STAGE, TAG, VALS = sys.argv[1], sys.argv[2], [float(v) for v in sys.argv[3].split(",")]
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/"
sys.path.insert(0, STAGE)
import numpy as np
import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from hr26 import params as P, curves as C, appendages as AP, hull as H, stand as ST


def pvol(s):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, g, 1e-6, False); return g.Mass()


def ok(s):
    return BRepCheck_Analyzer(s.wrapped).IsValid()


def bottom_curve(x):
    sec = np.asarray(C.section(float(x), 160), dtype=float)
    i = int(np.argmax(sec[:, 0])); b = sec[: i + 1]
    keep = [0]
    for j in range(1, len(b)):
        if b[j, 0] > b[keep[-1], 0]:
            keep.append(j)
    return b[keep]


t0 = time.time()
xs2 = list(np.linspace(2950, 6150, 14))
seg = cq.Solid.makeLoft([H._section_wire(float(x), 26) for x in xs2], ruled=False)
vseg = pvol(seg)
print(f"[{TAG}] segment valid {ok(seg)} vol {vseg/1e9:.4f} m3 {time.time()-t0:.1f}s", flush=True)
res = {}
for kf in VALS:
    P.KEEL_FILLET = kf
    t1 = time.time()
    k = AP.keel(); kv = k.val()
    r = dict(valid=ok(kv), vol=round(pvol(kv) / 1e9, 4))
    worst = {}
    for x in (3400, 3600, 4000, 4600, 5000, 5300, 5500, 5650):
        sl = k.intersect(cq.Workplane("YZ").workplane(offset=x).rect(4000, 4000).extrude(0.3))
        pts = []
        for e in sl.edges().vals():
            for t in np.linspace(0, 1, 60):
                p = e.positionAt(t)
                if abs(p.x - x) < 0.01:
                    pts.append((p.y, p.z))
        if not pts:
            continue
        pts = np.array(pts); bot = bottom_curve(x)
        zh = np.interp(np.abs(pts[:, 0]), bot[:, 0], bot[:, 1])
        out = pts[pts[:, 1] < zh - 1.0]
        if len(out) == 0:
            continue
        zz = np.round(out[:, 1] / 10.0) * 10.0
        prof = {}
        for zv, yv in zip(zz, np.abs(out[:, 0])):
            prof[zv] = max(prof.get(zv, 0.0), yv)
        zs = sorted(prof); hw = np.array([prof[z] for z in zs])
        worst[x] = (round(float(hw.max()), 0), round(float(hw.max() - hw[-1]), 0))
    r["exposed_hw_and_ledge"] = worst
    u = cq.Workplane("XY").newObject([seg]).union(k)
    us = u.val().Solids()
    uv = sum(pvol(s) for s in us)
    fa = min(f.Area() for f in u.val().Faces()); ed = min(e.Length() for e in u.val().Edges())
    r.update(union_solids=len(us), union_valid=all(ok(s) for s in us), added=round((uv - vseg) / 1e9, 4),
             min_face_mm2=round(fa, 1), min_edge_mm=round(ed, 2), t=round(time.time() - t1, 1))
    res[kf] = r
    print(f"[{TAG}] KEEL_FILLET {kf}: {r}", flush=True)
json.dump(res, open(OUT + f"out/keel_fillet_{TAG}.json", "w"), indent=1)
print(f"done {time.time()-t0:.1f}s")
