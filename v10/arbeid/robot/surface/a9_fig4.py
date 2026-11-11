import numpy as np, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface"
res = np.load(OUT + "/ripple.npy", allow_pickle=True).item()
rr = np.load(OUT + "/ripple_res.npy", allow_pickle=True).item()
xs = np.load(OUT + "/stations.npy")
st = np.load(OUT + "/strake.npz")
fig, axs = plt.subplots(3, 1, figsize=(15.5, 9.6), dpi=100, gridspec_kw=dict(height_ratios=[1.1, 1.1, 0.9]))
fig.patch.set_facecolor("#fcfcfb")
cols = {-150.0: "#86b6ef", 0.0: "#5598e7", 300.0: "#2a78d6", 600.0: "#104281"}
ax = axs[0]
for z, col in cols.items():
    R = res[z]; ax.plot(R["x"], rr[(z, 600.0)], color=col, lw=1.3, label=f"z = {z:+.0f} mm")
ax.set_title("(a) Exact loft surface: half-breadth at fixed height minus smooth trend (wavelengths > 600 mm removed)", loc="left", fontsize=11)
ax.set_ylabel("ripple, full-scale mm\n(model mm = /30)")
ax2 = axs[1]
for z, col in cols.items():
    R = res[z]; ax2.plot(R["x"], R["y"] - R["ya"], color=col, lw=1.3, label=f"z = {z:+.0f} mm")
ax2.set_title("(b) Loft minus analytic C.section(x): zero at stations; every dip > 1 mm sits within 3 mm of a WATERPLANE table breakpoint (black ticks)", loc="left", fontsize=11)
ax2.set_ylabel("deviation, full-scale mm")
for a in (ax, ax2):
    for x in xs:
        a.axvline(x, color="#eb6834", lw=0.6, alpha=0.5, zorder=0)
    a.axhline(0, color="#c3c2b7", lw=0.8)
    a.set_xlim(0, 8000); a.grid(axis="y", color="#e1e0d9", lw=0.6)
    a.set_facecolor("#fcfcfb")
    for s in ("top", "right"): a.spines[s].set_visible(False)
ax.plot([], [], color="#eb6834", lw=0.8, label="loft stations")
ax.legend(loc="upper center", ncol=5, fontsize=9, frameon=False)
ax2.set_ylim(-30, 30)
import sys
sys.path.insert(0, r"C:/Users/stig/Documents/GitHub/HR26-modell")
from hr26 import params as P
for t, _ in P.WATERPLANE:
    ax2.plot([P.LWL_FWD + t * P.LWL] * 2, [-30, -24], color="#0b0b0b", lw=1.6)
ax3 = axs[2]
sx = st["side_x"]; turn = st["turn"]
xk = sx[1:-1]; tk = turn[:len(xk)]
ax3.vlines(xk, 0, tk, color="#2a78d6", lw=2.0)
ax3.plot(xk, tk, "o", color="#2a78d6", ms=4)
ax3.annotate("+26 deg at x=7841 where the strake turns onto the transom (off scale); 1.1 deg per joint across the transom", xy=(7735, 15.5), xytext=(1500, 13.0), fontsize=9, color="#0b0b0b", arrowprops=dict(arrowstyle="->", color="#52514e"))
ax3.set_xlim(0, 8000); ax3.set_ylim(0, 17)
ax3.set_title("(c) Rubbing strake (ruled loft through 41 rectangles per side): plan-view kink at each panel joint", loc="left", fontsize=11)
ax3.set_ylabel("kink, deg"); ax3.set_xlabel("x from bow, full-scale mm")
ax3.grid(axis="y", color="#e1e0d9", lw=0.6); ax3.set_facecolor("#fcfcfb")
for s in ("top", "right"): ax3.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(OUT + "/fig4_ripple_strake.png", dpi=100, facecolor="#fcfcfb")
print("ok")
