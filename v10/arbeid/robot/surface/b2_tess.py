"""Chordal error (vs finest mesh) and dihedral stats: relative vs absolute deflection."""
import sys, os, time
import numpy as np
from scipy.spatial import cKDTree
SC = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface"
sys.path.insert(0, SC)
from common import load_raw, weld, face_normals, edges_adjacency
def load(path):
    T = load_raw(path); V, F = weld(T); fn, area = face_normals(V, F); return V, F, fn, area
Vr, Fr, fnr, ar = load(SC + "/loft/loft_t0.002_a0.02.stl")
cr = Vr[Fr].mean(1); tree = cKDTree(cr)
def dist(P):
    dd, ii = tree.query(P, k=6)
    pl = np.abs(np.einsum("ijk,ijk->ij", P[:, None, :] - cr[ii], fnr[ii]))
    return pl[np.arange(len(P)), np.argmin(dd, axis=1)]
rows = []
for path, tag in (("loft_t0.018_a0.12.stl", "relative 0.018 / 0.12 rad (= shipped)"),
                  ("loft_t0.018_a0.01.stl", "relative 0.018 / 0.01 rad"),
                  ("loft_t0.005_a0.03.stl", "relative 0.005 / 0.03 rad"),
                  ("loft_abs_t0.018_a0.12.stl", "ABSOLUTE 0.018 mm / 0.12 rad"),
                  ("loft_abs_t0.005_a0.12.stl", "ABSOLUTE 0.005 mm / 0.12 rad"),
                  ("loft_abs_t0.005_a0.05.stl", "ABSOLUTE 0.005 mm / 0.05 rad"),
                  ("loft_abs_t0.002_a0.05.stl", "ABSOLUTE 0.002 mm / 0.05 rad")):
    V, F, fn, area = load(SC + "/loft/" + path)
    c = V[F].mean(1)
    side = (np.abs(fn[:, 2]) < 0.9) & (c[:, 0] < 7700 / 30) & (c[:, 0] > 15 / 1)
    E, f1, f2, cnt = edges_adjacency(F)
    both = side[f1] & side[f2]
    dih = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", fn[f1], fn[f2]), -1, 1)))[both]
    el = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)[both]
    lmax = np.max(np.stack([np.linalg.norm(V[F[:, i]] - V[F[:, (i + 1) % 3]], axis=1) for i in range(3)], 1), 1)
    asp = lmax / np.maximum(2 * area / np.maximum(lmax, 1e-12), 1e-12)
    d = dist(c[side])
    print(f"{tag:38s} tri {len(F):7d} ({os.path.getsize(SC + '/loft/' + path)/1e6:5.1f} MB) side {side.sum():6d} | longest edge p50 {np.median(lmax[side]):5.2f} max {lmax[side].max():5.1f} mm, aspect>20 {np.mean(asp[side]>20)*100:4.1f}% | "
          f"dihedral p50 {np.percentile(dih,50):.2f} p99 {np.percentile(dih,99):5.2f} max {dih.max():5.1f}, >2deg {np.mean(dih>2)*100:4.1f}% >5deg {np.mean(dih>5)*100:5.2f}% | "
          f"centroid dev p50 {np.median(d):.4f} p95 {np.percentile(d,95):.4f} max {d.max():.3f} mm")
