"""Verify: rotation angle of 01_skrog.stl on the plate (claim: +45, not +44)."""
import numpy as np, sys

FN = r"C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl"
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/"


def load_stl(fn):
    with open(fn, "rb") as f:
        f.read(80)
        n = int(np.frombuffer(f.read(4), np.uint32)[0])
        dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec = np.frombuffer(f.read(n * 50), dt, count=n)
    return rec["v"].astype(np.float64)


tri = load_stl(FN)
print("triangles", len(tri))
V = tri.reshape(-1, 3)
print("bbox", V.min(0), V.max(0))


def rotz(P, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.c_[c * P[:, 0] - s * P[:, 1], s * P[:, 0] + c * P[:, 1], P[:, 2]]


# symmetric hull: per x bin, (ymax+ymin)/2 should be constant for the right angle
for ang in [43.0, 44.0, 44.5, 44.8, 44.9, 45.0, 45.1, 45.2, 45.5, 46.0]:
    R = rotz(V, -ang)
    x = R[:, 0]
    xb = np.linspace(x.min() + 10, x.max() - 10, 60)
    mids = []
    for a, b in zip(xb[:-1], xb[1:]):
        m = (x >= a) & (x < b)
        if m.sum() < 10:
            continue
        mids.append((0.5 * (a + b), 0.5 * (R[m, 1].max() + R[m, 1].min())))
    mids = np.array(mids)
    p = np.polyfit(mids[:, 0], mids[:, 1], 1)
    resid = mids[:, 1] - np.polyval(p, mids[:, 0])
    print(f"angle {ang:5.2f}: midline slope {p[0]*1000:+7.3f} mm/m, mid range {np.ptp(mids[:,1]):6.3f} mm, "
          f"resid max {np.abs(resid).max():.3f}")

# fine search by least squares on slope
def slope(ang):
    R = rotz(V, -ang)
    x = R[:, 0]
    xb = np.linspace(x.min() + 10, x.max() - 10, 60)
    mids = []
    for a, b in zip(xb[:-1], xb[1:]):
        m = (x >= a) & (x < b)
        if m.sum() < 10:
            continue
        mids.append((0.5 * (a + b), 0.5 * (R[m, 1].max() + R[m, 1].min())))
    mids = np.array(mids)
    return np.polyfit(mids[:, 0], mids[:, 1], 1)[0], np.ptp(mids[:, 1])

lo, hi = 44.0, 46.0
for _ in range(30):
    mid = 0.5 * (lo + hi)
    s, _ = slope(mid)
    if s > 0:
        hi = mid
    else:
        lo = mid
print("zero-slope angle:", 0.5 * (lo + hi), slope(0.5 * (lo + hi)))
s44 = slope(44.0)
print("at 44 deg: slope (mm/mm)", s44[0], "-> skew over 265 mm length:", s44[0] * 265, "model mm =", s44[0] * 265 * 30, "full mm (end to end)")
np.save(OUT + "tri.npy", tri)
