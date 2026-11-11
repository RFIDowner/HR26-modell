"""Baseline STL loader in full-scale boat frame: X from bow (mm), Y to port(+)/stbd, Z above DWL."""
import struct, numpy as np, os
BASE = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/baseline_fine.stl"
CACHE = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/base_full.npz"


def load_raw(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    return rec["v"].astype(np.float64)


def load_full():
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        return z["V"], z["F"]
    T = load_raw(BASE)
    Vv = T.reshape(-1, 3)
    key = np.round(Vv / 1e-4).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    V = Vv[first].copy()
    F = inv.reshape(-1, 3)
    V = V * 30.0
    V[:, 2] -= 1400.0
    np.savez(CACHE, V=V, F=F)
    return V, F


if __name__ == "__main__":
    V, F = load_full()
    print(V.shape, F.shape)
    print("bbox", V.min(0), V.max(0))
