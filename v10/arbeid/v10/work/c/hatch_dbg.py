import sys, time
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
from hr26 import deckhouse as D, params as P
c = D.coachroof(); h = D.hatches()
print("coach valid", c.val().isValid(), "hatch valid", h.val().isValid(), "hatch solids", len(h.solids().vals()))
for dx in (0.0, 0.37, -0.37):
    u = c.union(h.translate((dx, 0, 0)) if dx else h)
    print("dx", dx, "solids", len(u.solids().vals()), "dV", round(u.val().Volume() - c.val().Volume()), "valid", u.val().isValid())
for i, part in enumerate(h.solids().vals()):
    import cadquery as cq
    u = c.union(cq.Workplane("XY").newObject([part]))
    print("hatch", i, "bb x", round(part.BoundingBox().xmin), round(part.BoundingBox().xmax), "-> solids", len(u.solids().vals()), "dV", round(u.val().Volume() - c.val().Volume()))
