import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
from hr26 import curves as C, params as P, deckhouse as D
for x in [0, 4, 30, 60, 100, 150, 200, 300, 400, 500, 700, 900, 1900, 2200, 2330, 2500, 2900, 3400, 4200, 4900, 5000, 5135, 5500, 5625, 5660, 5700, 5900, 6000, 6150, 6400, 6540, 6800, 6900, 7250, 7500, 7680]:
    hb = C.deck_half_breadth(x)
    print(f"x={x:6.0f} hb={hb:7.1f} sheer={C.sheer_z(x):7.1f} deck0={C.deck_z(x,0):7.1f} camber={C.deck_camber(x):5.1f} roof={D.roof_z(x):7.1f} coachw={D.coach_half_width(x):7.1f} coamw={D.coaming_half_width(x):6.1f} cockw={D.cockpit_half_width(x):6.1f} coamtop={D.coaming_top_z(x):7.1f} bottom={C.bottom_z(x):7.1f}")
