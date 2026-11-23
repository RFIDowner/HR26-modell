import sys, time; sys.path.insert(0, "..")
import numpy as np, score as S
for tag in ["fine", "skrog"]:
    V = np.load(f"V_{tag}.npy"); F = np.load(f"F_{tag}.npy")
    t = time.time()
    sz = S.Slicer(V, F, 2, 10.0)
    t1 = time.time()
    levels = np.arange(700.0, 1500.0, 5.0) + 0.37
    holes = S.find_holes(sz, levels, lambda u, w: True)
    t2 = time.time()
    print(tag, "slicer %.2fs holes %.2fs" % (t1-t, t2-t1), len(holes))
    for h in sorted(holes, key=lambda h: (h["u"], h["w"])):
        print("   x %7.1f y %7.1f  d_eq %6.1f ext %6.1f x %6.1f  z %6.1f..%6.1f n %d" % (h["u"], h["w"], h["d_eq"], h["ext_u"], h["ext_w"], h["v_lo"], h["v_hi"], h["n_levels"]))
    sx = S.Slicer(V, F, 0, 10.0)
    levels = np.arange(7650.0, 7850.0, 3.0) + 0.37
    ph = S.find_holes(sx, levels, lambda u, w: abs(u) < 300 and w < 100)
    print("  pins:", [(round(h["u"],1), round(h["w"],1), round(h["d_eq"],1), round(h["v_lo"],1), round(h["v_hi"],1)) for h in ph])
    # orientation sanity: largest loop area sign at a mid section
    sec = sx.section(4000.37)
    L = S.section_loops(sec)
    i = np.argmax(np.abs(L["area"]))
    print("  x=4000 loops", L["n"], "largest area", L["area"][i], "closed", L["closed"][i], "areas", np.round(np.sort(L["area"])[:5]))
