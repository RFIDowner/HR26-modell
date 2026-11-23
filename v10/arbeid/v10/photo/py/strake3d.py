"""3D curves from the baseline mesh: strake outer edge (max |y| near strake z), hull half-breadth at given z per x."""
import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from stl import load_full
V, F = load_full()


def section_pts(x, half=12.0, side=1):
    m = (np.abs(V[:, 0] - x) < half) & (V[:, 1] * side > 0)
    return V[m]


def max_y_at(x, z, dz=25.0, half=15.0):
    m = (np.abs(V[:, 0] - x) < half) & (np.abs(V[:, 2] - z) < dz) & (V[:, 1] > 0)
    return V[m, 1].max() if m.sum() else np.nan


def silhouette_y(x, z0, z1, half=15.0):
    """max y over z in [z0,z1] at station x and the z where it occurs"""
    m = (np.abs(V[:, 0] - x) < half) & (V[:, 2] >= z0) & (V[:, 2] <= z1) & (V[:, 1] > 0)
    if m.sum() == 0:
        return np.nan, np.nan
    q = V[m]; i = np.argmax(q[:, 1]); return q[i, 1], q[i, 2]
