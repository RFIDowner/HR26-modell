import sys, time, math
sys.path.insert(0, "..")
import numpy as np
import score as S
SP = "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/"
for path in [SP + "baseline_fine.stl", "C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl"]:
    t = time.time()
    T, kind = S.load_stl(path)
    t1 = time.time()
    Vm, F = S.weld(T)
    t2 = time.time()
    topo = S.edge_topology(F, len(Vm))
    t3 = time.time()
    nc, lab = S.components(F, len(Vm))
    t4 = time.time()
    print(path.split("/")[-1], kind, len(T), "verts", len(Vm), "load %.1f weld %.1f topo %.1f comp %.1f" % (t1-t, t2-t1, t3-t2, t4-t3))
    print("  edges", topo["n_edges"], "nonman", topo["n_nonmanifold"], "flipped", topo["n_flipped"], "comps", nc, np.bincount(lab)[:12])
    vol = S.signed_volume(Vm, F)
    print("  comp volumes (cm3 model):", [round(float(vol[lab==c].sum())/1000, 2) for c in range(min(nc, 40))])
    t = time.time()
    fr = S.detect_frame(Vm)
    print("  frame", {k: v for k, v in fr.items() if k != "R"}, "%.1fs" % (time.time()-t))
    V = S.to_build_frame(Vm, fr, 4.0)
    print("  bbox full", V.min(0).round(1), V.max(0).round(1))
    np.save("V_%s.npy" % ("fine" if "fine" in path else "skrog"), V)
    np.save("F_%s.npy" % ("fine" if "fine" in path else "skrog"), F)
    np.save("lab_%s.npy" % ("fine" if "fine" in path else "skrog"), lab)
