import sys
sys.path.insert(0, ".")
import cadquery as cq
from cleat_mesh2 import count, test
L, W, H = 180.0, 45.0, 60.0
hb = 0.4 * H                                    # stangens hoyde
bar = cq.Workplane("XY").box(L, W, hb).translate((0, 0, H - 0.5 * hb)).edges().fillet(0.45 * hb)
foot = (cq.Workplane("XY").workplane(offset=-25.0).rect(0.4 * L, 0.78 * W).extrude(25.0 + H - 0.5 * hb)
        .edges("|Z").fillet(0.3 * W))
c = bar.union(foot)
s = test("bar+fot", c.val())
s.exportStl("parts/cleat_bar.stl", 0.3, 0.05, False, False)
