exec(open("p5_bottom.py").read().split("V = {}")[0])
def transom_bottom(f):
    # der kanobunnen moeter akterspeilets plan paa senterlinjen: x = TRANSOM_WL_X + RAKE*z
    xs = np.arange(7600.0, 7950.0, 0.5)
    g = np.array([f(v) for v in xs]) - (xs - P.TRANSOM_WL_X) / P.TRANSOM_RAKE
    i = np.nonzero(np.diff(np.sign(g)))[0][0]
    return xs[i], f(xs[i])
print("orig transom bottom", transom_bottom(C0.bottom_z))
V = {}
for nm, KN in {
    "a": [200, 400, 600, 800, 950, 1100, 1300, 1550, 1850, 2200, 2600, 3000, 3500, 4100, 4700, 5300, 5900, 6500, 7000, 7400, 7700],
    "e": [300, 600, 900, 1250, 1700, 2200, 2800, 3500, 4200, 5000, 5800, 6500, 7100, 7500, 7800],
    "f": [300, 600, 900, 1250, 1700, 2200, 2800, 3500, 4200, 5000, 5800, 6500, 7100, 7500],
    "g": [250, 500, 750, 1000, 1300, 1700, 2200, 2800, 3500, 4200, 5000, 5800, 6500, 7100, 7500],
    "h": [350, 700, 1000, 1350, 1800, 2300, 2800, 3500, 4200, 5000, 5800, 6500, 7100, 7500],
}.items():
    s = run(nm, KN)
    V[nm] = s
    xt, zt = transom_bottom(lambda v: float(s(v)[0]))
    xx2 = np.arange(600, 2000, 1.0); kk = L.curvature(s, xx2) * 1000
    # antall lokale maksima i kurvaturen i forfoten
    pk = np.nonzero((kk[1:-1] > kk[:-2]) & (kk[1:-1] >= kk[2:]))[0]
    print(f"      transom bottom x={xt:.0f} z={zt:.0f}; forfot-kurvatur topper ved {xx2[pk+1].round().tolist()} verdier {kk[pk+1].round(2).tolist()}; kappe {s(3200)[0]:.0f}/{C0.bottom_z(3200):.0f} at 3200, {s(3600)[0]:.0f}/{C0.bottom_z(3600):.0f} at 3600")
np.save(os.path.join(HERE, "p5_cases.npy"), {k: (v.t, v.c) for k, v in V.items()}, allow_pickle=True)
