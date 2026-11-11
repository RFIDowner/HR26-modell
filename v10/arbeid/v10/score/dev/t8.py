import sys; sys.path.insert(0, "..")
import numpy as np, score as S
SP = "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/"
WL = np.load(SP + "brep_waterlines.npz")
print(list(WL.keys()), {k: WL[k].shape for k in WL.keys()})
V = np.load("V_fine.npy"); F = np.load("F_fine.npy")
fn, *_ = S.face_geom(V, F)
slz = S.Slicer(V, F, 2, 10.0)
Vs = np.load("V_skrog.npy"); Fs = np.load("F_skrog.npy")
fns, *_ = S.face_geom(Vs, Fs)
slzs = S.Slicer(Vs, Fs, 2, 10.0)
def count(x, y, sig, thr, lo=600, hi=7400):
    m = (x >= lo) & (x <= hi) & np.isfinite(y)
    xx, yy = x[m], y[m]
    k, _ = S.curvature_graph(xx, yy, sig)
    c = int(2 * sig / (xx[1] - xx[0]))
    k = k[c:-c]
    return S.sign_changes(k, thr)[0]
for key, z in (("z150", 150.), ("z400", 400.), ("z700", 700.), ("z900", 900.)):
    p = WL[key]
    o = np.argsort(p[:, 0]); p = p[o]
    xg = np.arange(0, 8000, 5.0)
    yb = np.interp(xg, p[:, 0], p[:, 1], left=np.nan, right=np.nan)
    xf, yf, _ = S.waterline(slz, z, fn)
    xs_, ysk, _ = S.waterline(slzs, z, fns)
    print(key, "brep-vs-fine max|dy| (1000-7000): %.2f" % np.nanmax(np.abs((yb - yf)[(xg > 1000) & (xg < 7000)])))
    for sig in (15, 25, 40, 60):
        for thr in (0.02, 0.05, 0.1):
            print(f"   sigma {sig} thr {thr}: brep {count(xg, yb, sig, thr)}  fine {count(xf, yf, sig, thr)}  skrog {count(xs_, ysk, sig, thr)}")
