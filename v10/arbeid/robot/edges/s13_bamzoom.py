import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from secplot import plot_sections
W = OUT + "/work"
S = lambda nm: np.load(f"{W}/seg_{nm}.npy")
b3 = S("bam_x3200")
plot_sections([(b3, (0, 60, 220), 2)], (300, 1100, 1150, 1650), W=1000, grid=20, title="bam_x3200 wide", fn=f"{W}/z_bam_x3200_wide.png")
bc = S("bam_cl_front")
plot_sections([(bc, (0, 60, 220), 2)], (900, 2100, 1150, 1650), W=1000, grid=20, title="bam centreline front", fn=f"{W}/z_bam_cl_front_wide.png")
