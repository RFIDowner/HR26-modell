exec(open("p5_bottom.py").read().split("V = {}")[0])
for nm, KN, wt in [("e", [300, 600, 900, 1250, 1700, 2200, 2800, 3500, 4200, 5000, 5800, 6500, 7100, 7500, 7800], 1.0),
                   ("e2", [300, 600, 900, 1250, 1700, 2200, 2800, 3500, 4200, 5000, 5800, 6500, 7100, 7500, 7800], 3.0),
                   ("e3", [300, 650, 950, 1250, 1650, 2100, 2800, 3500, 4200, 5000, 5800, 6500, 7100, 7500, 7800], 3.0)]:
    s = run(nm, KN, wt=wt)
    trall = (uw[:, 0] >= 1008.0) & (uw[:, 0] <= 2800.0)
    rta = s(uw[trall, 0]) + uw[trall, 1]; i = np.argmax(np.abs(rta))
    rs = s(stem_x) - stem_z; j = np.argmax(np.abs(rs))
    xx2 = np.arange(600, 2000, 1.0); kk = L.curvature(s, xx2) * 1000
    pk = [v for v in np.nonzero((kk[1:-1] > kk[:-2] + 1e-6) & (kk[1:-1] >= kk[2:]))[0] if kk[v + 1] > 0.05]
    print(f"     trace max {rta[i]:+.1f} at x={uw[trall,0][i]:.0f}; stem max {rs[j]:+.1f} at x={stem_x[j]:.0f}; peaks {[(int(xx2[p+1]), round(kk[p+1],2)) for p in pk]}")
