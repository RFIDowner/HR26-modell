import sys, math
import numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b")
from p1_corner import side_y, psi_side, psi_tr, corner_K, C, P
from geo import full_tris, outer_lines
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

R_C, ALPHA, M_OUT = 220.0, math.radians(7.0), 25.0

def arc_end(z, yt, dlt):
    xt = C.transom_x(z, yt); pt = psi_tr(yt); pe = pt + dlt
    return (xt + R_C * (math.sin(pe) - math.sin(pt)), yt + R_C * (math.cos(pt) - math.cos(pe))), pe

def solve(z):
    K = corner_K(z)
    if K is None: return None
    th = psi_side(K[0] - 1, z) - psi_tr(K[1])
    a = min(ALPHA, 0.5 * th)
    def g(yt):
        dlt = th - a
        for _ in range(3):
            E, pe = arc_end(z, yt, dlt)
            dlt = psi_side(E[0], z) - a - psi_tr(yt)
        E, pe = arc_end(z, yt, dlt)
        return side_y(E[0], z) - E[1], dlt
    lo, hi = 0.0, K[1]
    if g(lo)[0] <= 0: return dict(K=K, th=th, yt=None)
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if g(m)[0] > 0: lo = m
        else: hi = m
    yt = 0.5 * (lo + hi); dlt = g(yt)[1]
    E, pe = arc_end(z, yt, dlt)
    return dict(K=K, th=th, yt=yt, dlt=dlt, E=E, pe=pe, a=a)

if __name__ == "__main__":
    T = full_tris(sys.argv[1]) if len(sys.argv) > 1 else None
    zs = (-150, 0, 200, 400, 600, 804, 880, 930)
    fig, axs = plt.subplots(2, 4, figsize=(16, 8.5))
    for ax, z in zip(axs.ravel(), zs):
        if T is not None:
            for Pl in outer_lines(T, 2, z):
                if (Pl[:, 0] > 7450).sum() > 1: ax.plot(Pl[:, 0], Pl[:, 1], "k-", lw=0.7)
        s = solve(z)
        if s and s["yt"] is not None:
            yt, dlt = s["yt"], s["dlt"]
            ys = np.linspace(0, yt, 30); ax.plot([C.transom_x(z, y) for y in ys], ys, "b-", lw=1.2)
            pts = [arc_end(z, yt, d)[0] for d in np.linspace(0, dlt, 20)]
            pts = np.array(pts); ax.plot(pts[:, 0], pts[:, 1], "r-", lw=1.5)
            E, pe = s["E"], s["pe"]; ax.plot([E[0], E[0] + 80 * math.cos(pe)], [E[1], E[1] + 80 * math.sin(pe)], "g-")
            depth = math.hypot(s["K"][0] - pts[10, 0], s["K"][1] - pts[10, 1])
            ax.set_title(f"z={z} th={math.degrees(s['th']):.0f} yt={yt:.0f} K=({s['K'][0]:.0f},{s['K'][1]:.0f}) a={math.degrees(s['a']):.1f}", fontsize=8)
            print(f"z={z}: theta={math.degrees(s['th']):.1f} K={s['K'][0]:.0f},{s['K'][1]:.0f} yt={yt:.1f} tangent len on transom={s['K'][1]-yt:.0f} E=({E[0]:.0f},{E[1]:.0f}) |KE|={math.hypot(E[0]-s['K'][0],E[1]-s['K'][1]):.0f} dlt={math.degrees(dlt):.1f}")
        ax.set_xlim(7600, 7980); ax.set_ylim(350, 850); ax.set_aspect("equal"); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b/p2_arcs.png", dpi=80)
