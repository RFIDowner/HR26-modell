import sys, json; sys.path.insert(0, '.')
import numpy as np
import common as c, uwlib as U, cands
cam_p = json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7]
cam = U.Cam(cam_p, 1500, 2000)
t = json.load(open(c.W + "/out/t9391.json"))
ro = np.array(t["red_outline"], float)
L = ro[(ro[:, 0] >= 755) & (ro[:, 0] <= 940)][:, [0, 1]]
R = ro[(ro[:, 0] >= 755) & (ro[:, 0] <= 915)][:, [0, 2]]
def outline(n_st=200, nsec=60):
    V, F = U.hull_mesh(n_st, nsec)
    lo, _ = U.row_extents(cam, V, F, L[:, 0])
    _, hi = U.row_extents(cam, V, F, R[:, 0])
    return lo, hi
def score(tag):
    lo, hi = outline()
    eL = -(lo - L[:, 1])        # outward positive (model wider)
    eR = hi - R[:, 1]
    h = U.hydro()
    print(f"{tag:28s} L mean {np.nanmean(eL):6.1f} rms {np.sqrt(np.nanmean(eL**2)):5.1f} | R mean {np.nanmean(eR):6.1f} rms {np.sqrt(np.nanmean(eR**2)):5.1f} | vol {h['vol']:.3f} bwl {h['bwl']:.0f} foot {c.C.bottom_z(U.transom_x(-400,0)):.0f}", flush=True)
    return dict(eL=eL, eR=eR, lo=lo, hi=hi, h=h)
if __name__ == "__main__":
    out = {}
    out["today"] = score("today")
    G = [(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.27, 0.0), (0.40, 3.0), (0.55, 8.0), (0.75, 12.0), (1.00, 13.0)]
    cands.apply(SECTION_DEADRISE=G); out["G"] = score("G")
    for mode in ("E", "B", "M"):
        cands.apply(CANOE_BOTTOM_HIDDEN=cands.hidden_aft(mode)); out["aft" + mode] = score("aft " + mode)
        cands.apply(CANOE_BOTTOM_HIDDEN=cands.hidden_aft(mode), SECTION_DEADRISE=G); out["aft" + mode + "+G"] = score("aft " + mode + " + G")
    print("rows L", L[::10, 0].tolist())
    for k in out:
        print(k, "eL", np.round(out[k]["eL"][::10], 0).tolist(), "eR", np.round(out[k]["eR"][::10], 0).tolist())
