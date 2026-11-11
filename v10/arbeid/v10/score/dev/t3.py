import sys, time; sys.path.insert(0, "..")
import numpy as np, score as S
for tag in ["fine", "skrog"]:
    V = np.load(f"V_{tag}.npy"); F = np.load(f"F_{tag}.npy")
    t = time.time()
    slx = S.Slicer(V, F, 0, 10.0)
    xs = np.arange(30.0, 7900.0, 10.0)
    rows = S.station_sweep(slx, xs)
    t1 = time.time()
    D = S.assemble_deck_line(rows)
    print(tag, "sweep %.1fs" % (t1 - t), "n_fit", D["stb"]["n_fit"], D["port"]["n_fit"])
    st = D["stb"]
    # raw virtual-corner offsets
    dys = np.array([r["stb"][2]-r["stb"][0] if (r and r["stb"] and r["stb"][4]) else np.nan for r in rows])
    dzs = np.array([r["stb"][3]-r["stb"][1] if (r and r["stb"] and r["stb"][4]) else np.nan for r in rows])
    print("  raw offsets dy p5/50/95", np.nanpercentile(dys,[5,50,95]).round(2), "dz", np.nanpercentile(dzs,[5,50,95]).round(2), "valid", np.isfinite(dys).sum(), "/", len(dys))
    for x0 in [100, 300, 600, 1000, 2000, 3000, 4000, 4300, 5000, 6000, 7000, 7300, 7600, 7800, 7850, 7880]:
        i = np.argmin(abs(st["x"] - x0))
        print("   x %5.0f  yc %7.1f zc %7.1f | y %7.1f z %7.1f | meas hb %7.1f zs %7.1f | port y %7.1f" % (st["x"][i], st["yc"][i], st["zc"][i], st["y"][i], st["z"][i], S.hb_meas(st["x"][i]), S.sheer_meas(st["x"][i]), D["port"]["y"][np.argmin(abs(D["port"]["x"]-x0))]))
    # strake
    for x0 in [300, 1050, 2100, 3000, 4200, 5100, 6000, 7050, 7650]:
        sec = slx.section(float(x0))
        i = np.argmin(abs(st["x"] - x0))
        sk = S.strake_at(sec, float(x0), st["zc"][i])
        print("   strake x", x0, {k: round(v,1) for k,v in sk.items()} if sk else None, "meas", S.strake_meas(x0))
