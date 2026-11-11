import sys
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from hr26 import hull as H, fittings as F, appendages as A, params as P
w = cq.Workplane("XY").newObject([H.hull_solid(40, 26)]).union(A.keel()).union(H.rubbing_strake().translate((0.37, 0, 0)))
print("base solids", len(w.val().Solids()))
for name, part in (("winch", F.winch_pads()), ("cleats", F.cleats()), ("anchor", F.anchor_roller()), ("name", F.transom_name())):
    u = w.union(part); print(name, "solids", len(u.val().Solids()))
