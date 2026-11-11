"""Render baseline mesh with a pinhole camera; save mask/shade/depth npz.  argv: name f Xc Yc Zc yaw pitch roll W H [hullonly]"""
import sys, json, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from stl import load_full
from cam import generic_rot, pinhole, raster_uv, face_normals, shade
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
name = sys.argv[1]
f, Xc, Yc, Zc, yaw, pitch, roll = map(float, sys.argv[2:9]); W, H = int(sys.argv[9]), int(sys.argv[10])
V, F = load_full()
fwd = np.array([np.cos(np.radians(pitch)) * np.cos(np.radians(yaw)), np.cos(np.radians(pitch)) * np.sin(np.radians(yaw)), np.sin(np.radians(pitch))])
R = generic_rot(fwd, roll=roll)
uv, z = pinhole(V, R, np.array([Xc, Yc, Zc]), f, W / 2, H / 2)
fid, zb = raster_uv(uv, z, F, W, H)
fn = face_normals(V, F)
sh = shade(fid, fn, R)
np.savez_compressed(f"{D}/render_{name}.npz", fid=fid, shade=sh, depth=zb)
print("rendered", name, (fid >= 0).sum())
