import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
T = np.load(OUT + "/ours_full.npy")
n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); A = 0.5 * np.linalg.norm(n, axis=1); n /= (2 * A[:, None] + 1e-12)
c = T.mean(1)
# coachroof wall (vertical faces) between x 2200 and 3200 on starboard side, z 1225-1340
m = (np.abs(n[:, 2]) < 0.05) & (c[:, 0] > 2195) & (c[:, 0] < 3300) & (c[:, 1] > -1) & (c[:, 2] > 1225) & (c[:, 2] < 1345) & (A > 1)
az = np.degrees(np.arctan2(n[m, 1], n[m, 0]))
order = np.argsort(c[m, 0])
azs = np.unique(np.round(az, 1))
print("coachroof wall triangles", m.sum(), " distinct normal azimuths:", len(azs))
d = np.diff(np.sort(azs))
print(" azimuth steps between facets (deg): median %.1f  max %.1f" % (np.median(d), d.max()))
# vertical extent of those triangles: do they span full wall height?
h = T[m][:, :, 2].max(1) - T[m][:, :, 2].min(1)
print(" triangle heights (mm): median %.0f max %.0f; lengths along wall median %.0f" % (np.median(h), h.max(), np.median(np.ptp(T[m][:, :, 0], axis=1))))
