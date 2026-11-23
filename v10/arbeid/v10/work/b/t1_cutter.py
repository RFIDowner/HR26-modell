import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from hr26 import hull as H, params as P
t = time.time()
pl = H._stern_plans()
print("plans %.1fs" % (time.time() - t))
for z, yt, R, a in pl[::3]:
    print(f"  z={z:6.0f} yt={yt:6.1f} R={R:6.0f} a={a*57.3:5.1f}")
t = time.time()
c = H._rounded_cutter()
s = c.val()
print("cutter %.1fs valid=%s vol=%.3g faces=%d" % (time.time() - t, s.isValid(), s.Volume(), len(s.Faces())))
t = time.time()
hs = H.hull_solid(40, 26)
print("hull_solid %.1fs valid=%s vol=%.6g faces=%d" % (time.time() - t, hs.isValid(), hs.Volume(), len(hs.Faces())))
P.TRANSOM_CORNER_L = 0.0
hs0 = H.hull_solid(40, 26)
print("old hull vol=%.6g  diff %.3f L" % (hs0.Volume(), (hs0.Volume() - hs.Volume()) / 1e6))
from cadquery import exporters
hs.scale(1/30).exportStl(WT + "/../../v10/work/b/t1_bare_new.stl", 0.01, 0.05, False, False)
hs0.scale(1/30).exportStl(WT + "/../../v10/work/b/t1_bare_old.stl", 0.01, 0.05, False, False)
