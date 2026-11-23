import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from PIL import Image
from lib import *
from secplot import plot_sections
T = np.load(OUT + "/ours_full.npy"); B = np.load(OUT + "/bambu_full_nostretch.npy")
W = OUT + "/work"
jobs = [
  ("ours_x3200", T, 0, 3200, (1, 2), (600, 1450, 950, 1450)),
  ("bam_x3200", B, 0, 3200, (1, 2), (500, 1200, 950, 1450)),
  ("ours_x6300", T, 0, 6300, (1, 2), (300, 1400, 900, 1350)),
  ("bam_x6300", B, 0, 6300, (1, 2), (200, 1200, 1000, 1450)),
  ("ours_cl_front", T, 1, 0.0, (0, 2), (2050, 2550, 1150, 1450)),
  ("bam_cl_front", B, 1, 0.0, (0, 2), (1200, 2000, 1150, 1500)),
  ("ours_stern_cl", T, 1, 0.0, (0, 2), (7500, 8050, 500, 1250)),
  ("bam_stern_cl", B, 1, 0.0, (0, 2), (7400, 8100, 300, 1450)),
  ("ours_plan_z600", T, 2, 600.0, (0, 1), (7300, 8000, 500, 1200)),
  ("bam_plan_z600", B, 2, 600.0, (0, 1), (7200, 8000, 300, 1100)),
]
for nm, M, ax, c, uv, box in jobs:
    s = section(M, ax, c)[:, :, list(uv)]
    np.save(f"{W}/seg_{nm}.npy", s)
    plot_sections([(s, (200, 0, 0) if nm.startswith("ours") else (0, 60, 220), 2)], box, W=1000, grid=20,
                  title=nm, fn=f"{W}/z_{nm}.png")
print("ok")
