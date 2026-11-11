import json, numpy as np, csv
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
REPO = r"C:/Users/stig/Documents/GitHub/HR26-modell"
m = json.load(open(f"{D}/m9370_lines.json"))
S = np.array(m["strake"])
rows = list(csv.DictReader(open(f"{REPO}/data/hull_stations.csv")))
xs = np.array([float(r["x_from_bow_mm"]) for r in rows]); zs = np.array([float(r["strake_z_mm"]) for r in rows])
hb = np.array([float(r["deck_half_breadth_mm"]) for r in rows])
DEZ = np.array([(0.0, 1204.0), (1000.0, 1204.0), (2000.0, 1200.0), (2500.0, 1175.0), (3000.0, 1150.0), (3750.0, 1122.0), (4200.0, 1115.0), (4500.0, 1105.0), (5000.0, 1095.0), (5500.0, 1085.0), (6000.0, 1080.0), (6500.0, 1075.0), (7000.0, 1056.0), (7200.0, 1040.0), (7400.0, 1020.0), (7600.0, 992.0), (7800.0, 962.0), (7950.0, 940.0)])
u0, u1 = 150.0, 985.0
for (ua, ub, tag) in ((150.0, 985.0, "LOA ends 150-985"),):
    sx = 7950.0 / (ub - ua)
    sel = (S[:, 0] > 200) & (S[:, 0] < 960)
    u = S[sel, 0]; v = S[sel, 3]
    x = (u - ua) * sx
    z = np.interp(x, xs, zs)
    # v = v0 - z/sz + k*x  -> linear LSQ in (v0, 1/sz, k)
    A = np.c_[np.ones_like(x), -z, x]
    p, *_ = np.linalg.lstsq(A, v, rcond=None)
    res = v - A @ p
    print(tag, "sx %.3f mm/px; v0 %.2f sz %.3f mm/px k %.5f px/mm (trim %.3f deg)  rms %.2f px max %.2f" % (sx, p[0], 1 / p[1], p[2], np.degrees(np.arctan(p[2] * (1 / p[1]))), res.std(), abs(res).max()))
    for uu in range(200, 961, 50):
        i = np.argmin(abs(u - uu)); print("   u %d x %.0f res %.2f px = %.0f mm" % (u[i], x[i], res[i], res[i] / p[1]))
    # fit without trim
    A2 = np.c_[np.ones_like(x), -z]
    p2, *_ = np.linalg.lstsq(A2, v, rcond=None); r2 = v - A2 @ p2
    print("  no-trim: sz %.3f rms %.2f max %.2f" % (1 / p2[1], r2.std(), abs(r2).max()))
