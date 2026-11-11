import sys; sys.path.insert(0, "..")
import numpy as np, score as S
V = np.load("V_fine.npy"); F = np.load("F_fine.npy")
slx = S.Slicer(V, F, 0, 10.0)
for x in [700.0, 3000.0, 4300.0, 5000.0, 6000.0, 7500.0]:
    sec = slx.section(x)
    y0, z0, y1, z1 = S._seg_yz(sec, 1)
    r = S.deck_edge_at(sec, x, 1)
    yc, zc = r[0], r[1]
    keep = np.maximum(y0, y1) > S.hb_meas(x) - 350
    zg = np.arange(max(S.strake_meas(x) + 55, zc - 140), zc - 25, 2.0)
    ys = S.envelope(z0[keep], y0[keep], z1[keep], y1[keep], zg, "max")
    fs = S.robust_line(zg[np.isfinite(ys)], ys[np.isfinite(ys)], cut=4.0, side="upper")
    yg = np.arange(yc - 170, yc - 25, 2.0)
    low = keep & (np.maximum(z0, z1) < zc + 60)
    zd = S.envelope(y0[low], z0[low], y1[low], z1[low], yg, "max")
    fd = S.robust_line(yg[np.isfinite(zd)], zd[np.isfinite(zd)], cut=6.0)
    print(f"x {x}: corner ({yc:.1f},{zc:.1f}) v=({r[2]:.1f},{r[3]:.1f}) ok={r[4]}  side fit {fs}  deck fit {fd}")
    print("   side env (z,y):", [(round(a),round(b,1)) for a,b in zip(zg[::6], ys[::6])])
    print("   deck env (y,z):", [(round(a),round(b,1)) for a,b in zip(yg[::6], zd[::6])])
