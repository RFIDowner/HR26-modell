import sys
sys.path.insert(0, sys.argv[1])
import numpy as np
from hr26 import params as P, curves as C, interior as I, cabin as CB, deckhouse as D
for x in (2925.0, 2950.0, 2975.0, 3000.0):
    w, zc = I.ceiling_ref(x)
    op = I.opening_plan().half_width(x) if I.opening_plan().p[0, 0] <= x else float("nan")
    print(f"x {x:.0f}: deck hb {C.deck_half_breadth(x):.1f}  coach foot {D.coach_half_width(x):.1f}  opening hw {op:.1f}  "
          f"ceiling_ref w {w:.1f} z {zc:.1f}  deck_z(y=750) {C.deck_z(x, 750.0):.1f}  underside {C.deck_z(x, 750.0)-P.DECK_THICK:.1f}  "
          f"y_in(z=1108) {I.y_in(x, 1108.0):.1f}  y_in(z=1060) {I.y_in(x, 1060.0):.1f}  split {CB.split_z(x):.1f}")
print("INT_WC_LOCKER_Y", P.INT_WC_LOCKER_Y, "BH fwd/aft", P.INT_BH_WC_FWD, P.INT_BH_WC_AFT, "GAP", I.GAP if hasattr(I, "GAP") else None)
