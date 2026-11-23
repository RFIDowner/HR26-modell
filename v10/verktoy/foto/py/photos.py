"""Photo silhouette metrics for the underwater body: IMG_9391 (astern, own camera) and IMG_9388 (ahead, 12.11 refit)."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
import common as c, uwlib as U
CAM91 = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
CAM88 = {"s2": U.Cam(json.load(open(c.W + "/out/cam9388_rail1.json"))["p"], 1500, 2000),
          "old2": U.Cam([-834.33, -5.7, 425.0, -3.37, 5.81, -0.08, 1496.69], 1500, 2000),
         "s1": U.Cam([-1242.41, -4.06, 23.85, -2.98, 2.63, 0.35, 1705.58], 1500, 2000)}
t91 = json.load(open(c.W + "/out/t9391.json")); ro = np.array(t91["red_outline"], float)
L91 = ro[(ro[:, 0] >= 755) & (ro[:, 0] <= 940)][:, [0, 1]]
R91 = ro[(ro[:, 0] >= 755) & (ro[:, 0] <= 915)][:, [0, 2]]
t88o = json.load(open(c.T9388_AUTO))
L88 = np.array(t88o["uw_left_auto"])[:, :2]; L88 = L88[(L88[:, 0] >= 880) & (L88[:, 0] <= 955)]
R88 = np.array(t88o["uw_right_auto"])[:, :2]; R88 = R88[(R88[:, 0] >= 860) & (R88[:, 0] <= 960)]
b88 = np.array(json.load(open(c.W + "/out/t9388.json"))["bottom_cols"])
B88 = b88[((b88[:, 0] >= 465) & (b88[:, 0] <= 625)) | ((b88[:, 0] >= 705) & (b88[:, 0] <= 865))]

def mesh():
    return U.hull_mesh(220, 60)

def e9391(V, F):
    lo, _ = U.row_extents(CAM91, V, F, L91[:, 0])
    _, hi = U.row_extents(CAM91, V, F, R91[:, 0])
    return -(lo - L91[:, 1]), hi - R91[:, 1]          # outward positive (model wider)

def e9388(V, F, key="s2"):
    cam = CAM88[key]
    lo, _ = U.row_extents(cam, V, F, L88[:, 0])
    _, hi = U.row_extents(cam, V, F, R88[:, 0])
    vlo, vhi = U.row_extents(cam, V, F, B88[:, 0], axis="col")     # per column: min/max row
    return -(lo - L88[:, 1]), hi - R88[:, 1], vhi - B88[:, 1]        # bottom: model lower = positive

def summary(tag, V=None, F=None, extra=""):
    if V is None:
        V, F = mesh()
    a, b = e9391(V, F); l8, r8, b8 = e9388(V, F)
    h = U.hydro()
    f = lambda e: f"{np.mean(e):+6.1f}/{np.sqrt(np.mean(e**2)):5.1f}"
    s = (f"{tag:26s} 9391 L {f(a)} R {f(b)} | 9388 L {f(l8)} R {f(r8)} bot {f(b8)} | vol {h['vol']:.3f} "
         f"BWL {h['bwl']:.0f} LWL {h['lwl']:.0f} LCB {h['lcb']:.0f} {extra}")
    print(s, flush=True)
    return dict(e91=(a, b), e88=(l8, r8, b8), h=h)
