"""Spantriss foer (A1, to kurver limt i DWL) og etter (A2, en konveks kurve
med avrundet dekkskant), pluss krumning oppover spantet og tall per stasjon."""
import importlib.util, json, math, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

A2 = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/a2"
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"


def load(root, tag):
    sys.path.insert(0, root)
    for k in [k for k in sys.modules if k.startswith("hr26")]:
        del sys.modules[k]
    import hr26.curves as C
    import hr26.params as P
    sys.path.pop(0)
    return C, P


Cb, Pb = load(A2 + "/pkg_a1", "a1")
mods_b = {k: v for k, v in sys.modules.items() if k.startswith("hr26")}
Cn, Pn = load(WT, "a2")


def curv(p):
    d1 = np.gradient(p, axis=0)
    d2 = np.gradient(d1, axis=0)
    return (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.maximum((d1 ** 2).sum(1) ** 1.5, 1e-30)


def full_new(x):
    """Ny: tett side + avrundet hjoerne + dekk (styrbord halvdel)."""
    sp = Cn.section_parts(x, 200, 40, 41)
    deck = sp["deck"][: len(sp["deck"]) // 2 + 1]
    return np.vstack([sp["side"], sp["corner"][1:], deck[1:]])


ORANGE, AQUA, INK, INK2, GRID = "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#d9d8d4"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb"})
fig = plt.figure(figsize=(14.5, 8.0), dpi=105)
ax = fig.add_axes([0.05, 0.08, 0.56, 0.84])
axk = fig.add_axes([0.67, 0.08, 0.31, 0.84])
FR = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98]
rows = []
for f in FR:
    x = f * Pn.LOA
    side = 1 if f <= 0.5 else -1
    old = np.array(Cb.section(x, 3000))
    new = full_new(x)
    oarc = np.array(Cb.deck_arc(x, 40))[:21]
    ax.plot(side * old[:, 0], old[:, 1], color=ORANGE, lw=1.1)
    ax.plot(side * oarc[:, 0], oarc[:, 1], color=ORANGE, lw=1.1)
    ax.plot(side * new[:, 0], new[:, 1], color=AQUA, lw=1.7)
    # tall
    sec = np.array(Cn.section(x, 2000))
    k = curv(sec)
    inner = k[5:-5]
    infl = int((np.diff(np.sign(inner[np.abs(inner) > 1e-7])) != 0).sum())
    ang = np.degrees(np.arctan2(np.gradient(sec[:, 0]), np.gradient(sec[:, 1])))
    zk = Cn.strake_z(x)
    yk = float(np.interp(zk, sec[:, 1], sec[:, 0]))
    hb = Cn.deck_half_breadth(x)
    j0 = int(np.argmin(np.abs(sec[:, 1])))
    ko = curv(old)
    rows.append(dict(x=round(x), wl_old=round(Cb.wl_half_breadth(x)), wl_new=round(Cn.wl_half_breadth(x)),
                     flare_wl=round(float(ang[j0]), 1) if sec[0, 1] < 0 else None,
                     flare_deck=round(float(ang[-3]), 1), inflections=infl,
                     Rmin_new=round(1.0 / max(inner.max(), 1e-9)),
                     Rmin_old=round(1.0 / max(ko[5:-5].max(), 1e-9)),
                     strake_face35=round(yk + 35 - hb), strake_face55=round(yk + 55 - hb)))
ax.axhline(0, color=INK2, lw=0.8)
ax.axvline(0, color=GRID, lw=0.8)
ax.set_aspect("equal")
ax.set_xlim(-1500, 1500)
ax.set_ylim(-560, 1560)
ax.grid(color=GRID, lw=0.6)
ax.plot([], [], color=ORANGE, lw=1.1, label="foer (A1): superellipse under DWL + hul side, skarp dekkskant")
ax.plot([], [], color=AQUA, lw=1.7, label="etter (A2): en konveks kurve, avrundet dekkskant R25, rund stevn")
ax.legend(frameon=False, fontsize=9, loc="upper center")
ax.text(700, 1290, "forut: 2-50 % LOA", ha="center", color=INK2)
ax.text(-700, 1290, "akter: 60-98 % LOA", ha="center", color=INK2)
ax.set_title("Spantriss, fullskala mm (y halvbredde, z over DWL)", loc="left")
for f, ls in ((0.25, "-"), (0.5, "--"), (0.85, ":")):
    x = f * Pn.LOA
    for p, col, lab in ((np.array(Cb.section(x, 6000)), ORANGE, "foer"), (np.array(Cn.section(x, 6000)), AQUA, "etter")):
        k = curv(p)
        sel = (p[:, 1] > p[0, 1] + 25) & (p[:, 1] < p[-1, 1] - 10)
        axk.plot(np.clip(k[sel] * 1000, -12, 25), p[sel, 1], color=col, lw=1.5, ls=ls, label=f"{lab}, x={x:.0f}")
axk.axhline(0, color=INK2, lw=0.8)
axk.axvline(0, color=GRID, lw=0.8)
axk.set_xlabel("krumning 1000/R (1/m), + = konveks, - = hul (klippet ved 25)")
axk.set_ylabel("z over DWL (mm)")
axk.set_title("Krumning oppover spantet", loc="left")
axk.grid(color=GRID, lw=0.6)
axk.legend(fontsize=8, frameon=False, loc="upper right")
fig.savefig(A2 + "/a2_bodyplan_before_after.png")
print(json.dumps(rows, indent=0))
xs = np.linspace(Pn.LWL_FWD, max(Pn.LWL_AFT, Pn.TRANSOM_WL_X), 400)
bo = np.array([Cb.wl_half_breadth(x) for x in xs])
bn = np.array([Cn.wl_half_breadth(x) for x in xs])
print(f"max WL beam {2 * bo.max():.0f} -> {2 * bn.max():.0f} ({(bn.max() / bo.max() - 1) * 100:+.1f} %), at x {xs[bo.argmax()]:.0f} -> {xs[bn.argmax()]:.0f}")
print(f"WL area {2 * np.trapezoid(bo, xs) / 1e6:.2f} -> {2 * np.trapezoid(bn, xs) / 1e6:.2f} m2")
print(f"canoe body {Cb.displaced_volume_m3():.3f} -> {Cn.displaced_volume_m3():.3f} m3")
