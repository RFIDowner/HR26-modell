"""Final numbers + figures for the cross-section lens. Reads our repo (import only), our STL contours
(ours_contours.json), Bambu contours (bambu_sections.json, produced by bambu_sections.py under python -I)."""
import sys, math, json
import numpy as np
sys.argv = ["x"]
HERE = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/sections"
exec(open(HERE + "/proposal.py").read().split('if __name__ == "__main__":')[0])
from scipy.interpolate import PchipInterpolator as PI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------- proposal B4 tables (fraction of LOA)
PHI = [(0, 24), (0.10, 19), (0.20, 13.5), (0.30, 11), (0.45, 9.5), (0.60, 9.0), (0.75, 9.0), (0.90, 10.0), (1.0, 10.5)]
NN = [(0, 2.4), (0.15, 3.1), (0.35, 3.4), (0.6, 3.5), (0.8, 3.3), (1.0, 3.1)]
BETA = [(0, 45), (0.127, 15), (0.2, 4), (0.27, 0), (1.0, 0)]
pf = PI(*zip(*PHI)); nf = PI(*zip(*NN)); bf = PI(*zip(*BETA))


def newsec(x, m=600):
    t = x / P.LOA
    return curve(x, float(nf(t)), m, phi=float(pf(t)), beta=float(bf(t)))


ORANGE, BLUE, AQUA = "#eb6834", "#2a78d6", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.titlesize": 10, "axes.titleweight": "bold", "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb"})

# ---------------- Bambu topside metrics (beam-corrected) vs ours over a common height band
B = json.load(open(HERE + "/bambu_sections.json"))
S = B["stretch"]
O = json.load(open(HERE + "/ours_contours.json"))


def chord_metrics(Y, Z, z_lo, z_hi):
    """Y(Z) on [z_lo, z_hi]: signed max deviation from chord (+ convex/outward), flare near bottom & top (deg)."""
    zz = np.linspace(z_lo, z_hi, 60)
    yy = np.interp(zz, Z, Y)
    y0, y1 = yy[0], yy[-1]
    cy, cz = y1 - y0, z_hi - z_lo; L = math.hypot(cy, cz); nrm = np.array([cz, -cy]) / L
    dev = (yy - y0) * nrm[0] + (zz - z_lo) * nrm[1]
    k = 8
    fl_lo = math.degrees(math.atan2(yy[k] - yy[0], zz[k] - zz[0]))
    fl_hi = math.degrees(math.atan2(yy[-1] - yy[-1 - k], zz[-1] - zz[-1 - k]))
    return round(float(dev[np.argmax(np.abs(dev))]), 1), round(fl_lo, 1), round(fl_hi, 1)


cmp_rows = []
for f in ["0.15", "0.2", "0.25", "0.3", "0.4", "0.5", "0.6", "0.7", "0.75", "0.8", "0.85", "0.9"]:
    x = B[f]["x"]
    env = np.array(B[f]["env"]); bot = np.array(B[f]["bottom"])
    zk, zs = C.strake_z(x), C.sheer_z(x)
    # Bambu: max-y height in [zs-300, zs+150] = its deck edge / strake
    sel = (env[:, 1] > zs - 300) & (env[:, 1] < zs + 150)
    j = np.argmax(env[sel, 0]); z_top_b = env[sel][j, 1]
    z_bot_b = bot[bot[:, 0] < 60, 1].min() if (bot[:, 0] < 60).any() else env[:, 1].min()
    z_lo = max(z_bot_b + 200.0, 300.0)
    z_hi = min(z_top_b, zk - 75.0)
    if z_hi - z_lo < 200:
        continue
    e = env[(env[:, 1] >= z_lo - 20) & (env[:, 1] <= z_hi + 20)]
    bm = chord_metrics(e[:, 0] * S, e[:, 1], z_lo, z_hi)
    bm_raw = chord_metrics(e[:, 0], e[:, 1], z_lo, z_hi)
    cur = np.array(C.section(x, 3000)); i = np.argsort(cur[:, 1])
    om = chord_metrics(cur[i, 0], cur[i, 1], z_lo, z_hi)
    nw = newsec(x); i2 = np.argsort(nw[:, 1])
    nm = chord_metrics(nw[i2, 0], nw[i2, 1], z_lo, z_hi)
    cmp_rows.append(dict(f=float(f), x=round(x), z_lo=round(z_lo), z_hi=round(z_hi), bambu=bm, bambu_rawwidth=bm_raw, ours=om, proposal=nm))
print("Topside band comparison: (max chord deviation mm [+ convex], flare at band bottom deg, flare at band top deg)")
for r in cmp_rows:
    print(f"  f={r['f']:.2f} x={r['x']:5d} band z {r['z_lo']:4d}..{r['z_hi']:4d} | Bambu {r['bambu']} (raw width {r['bambu_rawwidth']}) | ours {r['ours']} | proposal {r['proposal']}")

# ---------------- proposal numbers at the 15 stations
FR = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
prow = []
for f in FR:
    x = f * P.LOA
    m = metrics(newsec(x), x)
    K_, D_, Cc, a, c, ub, us = frame(x, float(pf(f)), float(bf(f)))
    prow.append(dict(f=f, x=round(x), zb=round(C.bottom_z(x)), zs=round(C.sheer_z(x)), bd=round(C.deck_half_breadth(x)),
                     phi=round(float(pf(f)), 1), beta=round(float(bf(f)), 1), n=round(float(nf(f)), 2),
                     a=round(a), c=round(c), Cy=round(Cc[0]), Cz=round(Cc[1]), **m, bw_table=round(bw_current(x))))
print("\nProposal per station:")
for k in ["f", "x", "zb", "zs", "bd", "phi", "beta", "n", "a", "c", "Cy", "Cz", "y_WL", "bw_table", "flare_at_WL", "flare_deck", "topside_dev", "R_45", "z_45", "R_min", "z_Rmin", "y_strake", "strake_face_minus_deck", "inflections"]:
    print(f"{k:>22s}: " + " | ".join(str(r.get(k)) for r in prow))
xv = np.linspace(P.LWL_FWD, max(P.LWL_AFT, P.TRANSOM_WL_X), 200)
an = np.array([area_below_dwl(newsec(x, 300)) for x in xv]); ac = np.array([area_current(x) for x in xv])
bn = np.array([y_at(newsec(x, 300), 0.0) if C.bottom_z(x) < -1 else 0 for x in xv]); bc = np.array([bw_current(x) for x in xv])
Vn, Vc = np.trapezoid(an, xv) / 1e9, np.trapezoid(ac, xv) / 1e9
print(f"\ncanoe body below DWL: current {Vc:.3f} m3 -> proposal {Vn:.3f} m3 ({(Vn / Vc - 1) * 100:+.1f} %);  "
      f"max WL beam {2 * bc.max():.0f} -> {2 * bn.max():.0f} mm ({(bn.max() / bc.max() - 1) * 100:+.1f} %), at x {xv[np.argmax(bc)]:.0f} -> {xv[np.argmax(bn)]:.0f};  "
      f"WL area {2 * np.trapezoid(bc, xv) / 1e6:.2f} -> {2 * np.trapezoid(bn, xv) / 1e6:.2f} m2")

# ================= FIGURE 1: body plan of the current generator + curvature along height
fig = plt.figure(figsize=(14, 7.6), dpi=110)
ax = fig.add_axes([0.065, 0.09, 0.55, 0.83]); axk = fig.add_axes([0.69, 0.09, 0.29, 0.83])
xs20 = np.linspace(0.03, 0.97, 20) * P.LOA
for x in xs20:
    s = np.array(C.section(x, 26))           # the 26 points the CAD spline is built from
    dense = np.array(C.section(x, 3000))
    side = 1 if x <= P.LOA / 2 else -1
    ax.plot(side * dense[:, 0], dense[:, 1], color=ORANGE, lw=1.4, solid_capstyle="round")
    ax.plot(side * s[:, 0], s[:, 1], ".", color=INK2, ms=2.2)
    # mark tightest turn: the DWL junction
    if C.bottom_z(x) < -1:
        ax.plot(side * min(C.wl_half_breadth(x), C.deck_half_breadth(x)), 0, "o", ms=4, mfc="none", mec=INK)
ax.axhline(0, color=INK2, lw=0.8); ax.axvline(0, color=GRID, lw=0.8)
ax.text(-1450, 25, "DWL", color=INK2, fontsize=9)
ax.text(760, 1440, "forward half (x < 3975)", ha="center", color=INK2); ax.text(-1450, 1440, "aft half", ha="left", color=INK2)
ax.annotate("hollow topsides: up to 54 mm (1.8 mm at 1:30)\ninside the WL-to-deck chord", xy=(745, 520), xytext=(250, 820),
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), fontsize=9, color=INK)
ax.annotate("every section is vertical exactly at the DWL:\ntightest bilge turn sits 8-34 mm below it,\nthen the side flips to hollow (inflection)", xy=(-1124, 0), xytext=(-1500, 1180),
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), fontsize=9, color=INK)
ax.set_aspect("equal"); ax.set_xlim(-1550, 1550); ax.set_ylim(-560, 1520)
ax.set_title("Current generator (curves.section, n=26): body plan, 20 stations 3-97 % LOA, full-scale mm", loc="left", color=INK)
ax.grid(color=GRID, lw=0.6); ax.set_xlabel("half-breadth y (mm)"); ax.set_ylabel("z above DWL (mm)")
for f, ls in ((0.25, "-"), (0.5, "--"), (0.85, ":")):
    x = f * P.LOA
    for Pp, col, lab in ((np.array(C.section(x, 6000)), ORANGE, "current"), (newsec(x, 3000), AQUA, "proposal")):
        d1 = np.gradient(Pp, axis=0); d2 = np.gradient(d1, axis=0)
        k = (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.maximum((d1 ** 2).sum(1) ** 1.5, 1e-30)
        sel = (Pp[:, 1] > C.bottom_z(x) + 30) & (Pp[:, 1] < C.sheer_z(x) - 10)
        axk.plot(np.clip(k[sel] * 1000, -12, 25), Pp[sel, 1], color=col, lw=1.5, ls=ls, label=f"{lab}, x={x:.0f}")
axk.axhline(0, color=INK2, lw=0.8); axk.axvline(0, color=GRID, lw=0.8)
axk.set_xlabel("curvature  1000/R  (1/m; + = convex bilge, - = hollow)"); axk.set_ylabel("z above DWL (mm)")
axk.set_title("Curvature up the section (clipped at 25)", loc="left", color=INK); axk.grid(color=GRID, lw=0.6)
axk.legend(fontsize=8, frameon=False, loc="upper right")
axk.text(4, 120, "current: spike at the DWL,\nsign flip = crease line", fontsize=8.5, color=INK)
fig.savefig(HERE + "/fig1_bodyplan_current.png"); plt.close(fig)

# ================= FIGURE 2: ours (STL) vs Bambu (beam-corrected) topsides, 8 stations, + proposal
sts = ["0.15", "0.25", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9"]
fig, axs = plt.subplots(2, 4, figsize=(14.5, 8.2), dpi=110)
for axx, f in zip(axs.ravel(), sts):
    x = B[f]["x"]; zk, zs, bd = C.strake_z(x), C.sheer_z(x), C.deck_half_breadth(x)
    env = np.array(B[f]["env"]); bot = np.array(B[f]["bottom"])
    # walk up the side; stop at the first inward jump > 60 mm (deck / rail above Bambu's sheer)
    keep = np.zeros(len(env), bool); run = -1e9
    for i_ in np.argsort(env[:, 1]):
        if env[i_, 0] < run - 60 and env[i_, 1] > zs - 400: break
        keep[i_] = True; run = max(run, env[i_, 0])
    axx.plot(env[keep, 0] * S, env[keep, 1], color=BLUE, lw=1.8, label="Bambu, y x 1.223")
    pts = np.array(O[f]["pts"]); msk = np.array(O[f]["m"])
    sel = (pts[:, 1] > -150)
    axx.plot(pts[sel, 0], pts[sel, 1], color=ORANGE, lw=1.8, label="our STL (01_skrog)")
    nw = newsec(x); s2 = nw[:, 1] > -150
    axx.plot(nw[s2, 0], nw[s2, 1], color=AQUA, lw=1.4, ls="--", label="proposal")
    if C.bottom_z(x) < -1:
        bw = bw_current(x)
        axx.plot([bw, bd], [0, zs], color=INK2, lw=0.8, ls=":")
    axx.axhline(0, color=INK2, lw=0.7)
    axx.set_title(f"x = {x:.0f} mm ({float(f) * 100:.0f} % LOA)", loc="left", color=INK)
    axx.set_ylim(-150, zs + 80)
    lo = min(np.interp(-150, pts[np.argsort(pts[:, 1]), 1], pts[np.argsort(pts[:, 1]), 0]), env[keep, 0].min() * S)
    axx.set_xlim(max(lo - 60, 0), bd + 120)
    axx.set_aspect("equal"); axx.grid(color=GRID, lw=0.6)
    axx.tick_params(labelsize=8)
axs[0, 0].legend(fontsize=8, frameon=False, loc="upper left")
fig.suptitle("Topsides, full-scale mm (z above our DWL; dotted = chord WL to deck edge). Bambu has no hull below ~z 200-350.",
             x=0.01, ha="left", fontsize=11, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(HERE + "/fig2_ours_vs_bambu_topsides.png"); plt.close(fig)

# ================= FIGURE 3: proposal overlaid on current, body plan 12 stations
fig, ax = plt.subplots(figsize=(13, 7.4), dpi=110)
xs12 = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
for f in xs12:
    x = f * P.LOA; side = 1 if f <= 0.5 else -1
    cur = np.array(C.section(x, 3000)); nw = newsec(x)
    ax.plot(side * cur[:, 0], cur[:, 1], color=ORANGE, lw=1.3)
    ax.plot(side * nw[:, 0], nw[:, 1], color=AQUA, lw=1.8)
    ax.plot(side * C.deck_half_breadth(x), C.sheer_z(x), "o", ms=3.5, color=INK)
    yk = y_at(nw, C.strake_z(x))
    ax.plot([side * yk, side * (yk + P.STRAKE_PROUD)], [C.strake_z(x)] * 2, color=INK2, lw=2.2, solid_capstyle="butt")
ax.axhline(0, color=INK2, lw=0.8); ax.axvline(0, color=GRID, lw=0.8)
ax.text(-1500, 25, "DWL", color=INK2, fontsize=9)
ax.plot([], [], color=ORANGE, lw=1.3, label="current section (superellipse + t^1.45)")
ax.plot([], [], color=AQUA, lw=1.8, label="proposal: corner-rounding superellipse, G2, convex")
ax.plot([], [], "o", ms=3.5, color=INK, label="measured deck edge (kept exactly)")
ax.plot([], [], color=INK2, lw=2.2, label="strake (55 mm proud) on the proposal")
ax.legend(frameon=False, fontsize=9, loc="upper center", ncol=2)
ax.text(760, 1290, "forward: 5, 10, 15, 20, 30, 40, 50 % LOA", ha="center", color=INK2, fontsize=9)
ax.text(-760, 1290, "aft: 60, 70, 80, 90, 95 % LOA", ha="center", color=INK2, fontsize=9)
ax.set_aspect("equal"); ax.set_xlim(-1550, 1550); ax.set_ylim(-560, 1640); ax.grid(color=GRID, lw=0.6)
ax.set_title(f"Proposed section family over the current one (keel point, deck edge, strake height unchanged). "
             f"Canoe body {Vc:.2f} -> {Vn:.2f} m3 ({(Vn / Vc - 1) * 100:+.0f} %)", loc="left", color=INK)
ax.set_xlabel("half-breadth y (mm)"); ax.set_ylabel("z above DWL (mm)")
fig.tight_layout(); fig.savefig(HERE + "/fig3_proposal_vs_current.png"); plt.close(fig)
json.dump(dict(cmp=cmp_rows, proposal=prow, Vc=Vc, Vn=Vn), open(HERE + "/final.json", "w"), indent=1)
print("figures written")
