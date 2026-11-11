import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from secplot import plot_sections
T = np.load(OUT + "/ours_full.npy"); B = np.load(OUT + "/bambu_full.npy")
W = OUT + "/work"
for x in (1500, 2300, 3200, 4500, 5300, 6300, 7300):
    so = section(T, 0, x)[:, :, [1, 2]]; sb = section(B, 0, x)[:, :, [1, 2]]
    plot_sections([(so, (200, 0, 0), 2), (sb, (0, 60, 220), 2)], (-100, 1500, 300, 1900), W=1000, grid=100,
                  title=f"x={x}: ours red, Bambu blue (y*1.223)", fn=f"{W}/sec_x{x}.png")
# centreline profile, bow / coachroof front / stern
so = section(T, 1, 0.0)[:, :, [0, 2]]; sb = section(B, 1, 0.0)[:, :, [0, 2]]
for nm, box in (("bow", (-100, 1100, 500, 1500)), ("front", (1700, 2900, 900, 1700)), ("stern", (6700, 8100, 300, 1500)), ("all", (-200, 8200, 0, 1900))):
    plot_sections([(so, (200, 0, 0), 2), (sb, (0, 60, 220), 2)], box, W=1200 if nm=="all" else 1000, grid=100,
                  title=f"centreline y=0 ({nm}): ours red, Bambu blue", fn=f"{W}/cl_{nm}.png")
print("ok")
