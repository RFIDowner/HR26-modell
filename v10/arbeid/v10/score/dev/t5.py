import sys, time; sys.path.insert(0, "..")
import numpy as np, score as S
for tag in ["fine", "skrog"]:
    V = np.load(f"V_{tag}.npy"); F = np.load(f"F_{tag}.npy")
    fn, area, cen, asp, lmax = S.face_geom(V, F)
    slx = S.Slicer(V, F, 0, 10.0)
    xs = np.arange(30.0, 7900.0, 10.0)
    t = time.time()
    rows = S.station_sweep(slx, xs, fn)
    D = S.assemble_deck_line(rows)
    print(tag, "sweep %.1fs" % (time.time() - t), "n_fit", D["stb"]["n_fit"], D["port"]["n_fit"])
    dys = np.array([r["stb"][2]-r["stb"][0] if (r and r["stb"] and r["stb"][4]) else np.nan for r in rows])
    dzs = np.array([r["stb"][3]-r["stb"][1] if (r and r["stb"] and r["stb"][4]) else np.nan for r in rows])
    X = np.array([r["x"] for r in rows])
    win = (X > 3640) & (X < 4960)
    print("  raw offsets outside window: dy p1/50/99", np.nanpercentile(dys[~win],[1,50,99]).round(2), "dz", np.nanpercentile(dzs[~win],[1,50,99]).round(2), "valid", np.isfinite(dys).sum(), "/", len(dys))
    bad = np.nonzero(~np.isfinite(dys))[0]
    print("  invalid fits at x:", X[bad][:40])
    st = D["stb"]
    print("  smoothed offsets |dy| max %.2f |dz| max %.2f" % (np.abs(st["dy"]).max(), np.abs(st["dz"]).max()))
    for x0 in [300, 1050, 2100, 3000, 4200, 5100, 6000, 7050, 7650]:
        sec = slx.section(float(x0)); sec["n"] = fn[sec["f"]]
        i = np.argmin(abs(st["x"] - x0))
        sk = S.strake_at(sec, float(x0), st["zc"][i])
        print("   strake x", x0, {k: round(v,1) for k,v in sk.items()} if sk else None, "meas", S.strake_meas(x0))
