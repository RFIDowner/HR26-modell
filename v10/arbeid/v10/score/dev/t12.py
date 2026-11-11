import sys, time; sys.path.insert(0, "..")
import numpy as np, score as S
for tag in ["fine", "skrog"]:
    V = np.load(f"V_{tag}.npy"); F = np.load(f"F_{tag}.npy")
    fn, area, cen, asp, lmax = S.face_geom(V, F)
    slz = S.Slicer(V, F, 2, 10.0)
    holes = [h for h in S.find_holes(slz, np.arange(700.0, 1500.0, 5.0) + 0.37, lambda u, w: True) if h["n_levels"] >= 3]
    slx = S.Slicer(V, F, 0, 10.0)
    pins = S.find_holes(slx, np.arange(7650.0, 7850.0, 3.0) + 0.37, lambda u, w: abs(u) < 300 and w < 0)
    vh = [(h["u"], h["w"], 0.5 * max(h["ext_u"], h["ext_w"]), h["v_lo"], h["v_hi"]) for h in holes]
    hh = [(h["u"], h["w"], 0.5 * max(h["ext_u"], h["ext_w"]), h["v_lo"], h["v_hi"]) for h in pins]
    t = time.time()
    ext, wall, info = S.split_exterior(V, F, cen, vh, hh)
    print(tag, "split %.1fs" % (time.time() - t), info, "ext faces", ext.sum(), "wall faces", wall.sum())
    topo = S.edge_topology(F, len(V))
    skin = S.hull_skin_mask(cen, fn, ext)
    mq, ang = S.mesh_quality(topo, fn, asp, lmax, skin)
    print("  mesh", mq)
    deck = S.deck_mask(cen, fn, ext)
    t = time.time()
    wt, _ = S.wall_thickness(V, F, fn, area, cen, skin, deck, 30000)
    print("  thickness %.1fs" % (time.time() - t))
    for k, v in wt.items(): print("   ", k, v)
