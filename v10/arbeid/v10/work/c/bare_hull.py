import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
from hr26 import hull as H
s = H.hull_solid(40, 26)
s.exportStl("C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/c/parts/bare_hull.stl", 0.5, 0.1, False, False)
print("ok")
