"""Egne hjelpere: last STL i baatramme (modell-mm, x fra baugen, kjol paa z=0) -> fullskala."""
import sys, math
import numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b")
from common import load_raw, weld, components, face_normals, corner_normals, look, raster, shade2
from elib import section, chain

def full_tris(path, x_bow=4.0):
    T = load_raw(path).astype(np.float64)
    V = T.reshape(-1, 3)
    T[:, :, 0] -= V[:, 0].min(); T[:, :, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min()); T[:, :, 2] -= V[:, 2].min()
    T *= 30.0
    T[:, :, 0] += x_bow
    T[:, :, 2] -= 1400.0
    return T

def outer_lines(T, axis, c):
    segs = section(T, axis, c)
    if len(segs) == 0:
        return []
    return chain(segs, tol=1e-4)
