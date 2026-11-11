import sys, json, csv, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cam9370 import hbf, sheer, strake
from slicer import section_points
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
fig = plt.figure(figsize=(16, 9.5), dpi=100)
ax = fig.add_axes([0.05, 0.56, 0.92, 0.39])
x = np.linspace(0, 7950, 400)
ax.plot(x, sheer(x), color="#b000b0", lw=1.8, label="today: deck edge DECK_EDGE_Z")
ax.fill_between(x[(x > 200) & (x < 7880)], strake(x[(x > 200) & (x < 7880)]) - 47.5, strake(x[(x > 200) & (x < 7880)]) + 47.5, color="#ff9900", alpha=0.35, label="today: rub rail band 95 mm")
ps = np.load(f"{D}/photo_strake_xz.npy")
ax.fill_between(ps[:, 0], ps[:, 2], ps[:, 1], color="#0090c0", alpha=0.8, label="photo IMG_9370: rub rail band (~42 mm)")
# model window
W0, W1 = 3700, 4900
xm = np.linspace(W0, W1, 50)
ax.plot(np.r_[xm, xm[::-1], xm[0]], np.r_[strake(xm) + 70, (sheer(xm) - 30)[::-1], strake(xm[0]) + 70], color="red", lw=2, label="today: window 3700-4900")
# photo window (frame) polygon in boat frame (from back-projection)
pw = np.array([[4012, 1033], [4040, 1130], [4236, 1161], [4807, 1144], [5430, 1115], [5600, 1050], [5621, 945], [5517, 856], [4798, 884], [4227, 907], [4060, 960], [4012, 1033]])
ax.plot(pw[:, 0], pw[:, 1], color="green", lw=2.5, label="photo: window frame ~4010-5620, 255 mm tall")
ax.annotate("deck edge must be above the\nphoto window top: >= ~1160\n(today 1099-1114)", xy=(4600, 1150), xytext=(5900, 1250), arrowprops=dict(arrowstyle="->"), fontsize=10)
ax.plot([3400, 3400], [1350, 1500], color="k", lw=3); ax.text(3410, 1460, "mast 3400 (drawing)", fontsize=9)
ax.plot([3600, 3600], [1350, 1500], color="green", lw=3, ls="--"); ax.text(3610, 1400, "photo ~3600 +-100", fontsize=9, color="green")
bt = [[1377, 126], [1845, 122], [2314, 114], [2786, 108], [3733, 94], [4209, 93], [5163, 94], [5641, 103], [6121, 116], [6602, 134]]
bt = np.array(bt)
ax.plot(bt[:, 0], bt[:, 1], "o-", color="#c8a000", label="photo: boot-top top edge (abs. z +-60, shape +-30)")
ax.axhline(0, color="#4060ff", lw=1, ls=":"); ax.text(50, 15, "DWL", color="#4060ff")
ax.set_xlim(-100, 8100); ax.set_ylim(-50, 1550); ax.set_xlabel("x from bow (mm, full scale)"); ax.set_ylabel("z above DWL (mm)")
ax.set_title("Side profile: photo-measured lines (IMG_9370, fitted camera) vs today's model", fontsize=12)
ax.legend(loc="lower left", fontsize=9, ncol=2); ax.grid(alpha=0.3)
# sections
ax2 = fig.add_axes([0.05, 0.06, 0.42, 0.42])
for xs_, col in ((3550, "red"), (4950, "#ff8080")):
    P = section_points(xs_); P = P[(P[:, 1] < 0)]
    ax2.plot(-P[:, 1], P[:, 2], ".", ms=1.2, color=col, label=f"today x={xs_}")
pts = json.load(open(f"{D}/bow_sil_3d.json"))
pp = np.array([[abs(r[5]), r[6]] for r in pts if r[3] < 500])
ax2.plot(pp[:, 0], pp[:, 1], "s", color="green", ms=7, label="photo IMG_9388 silhouette at x~3550")
pm = np.array([[abs(r[2]), r[3]] for r in pts if r[3] < 500])
ax2.plot(pm[:, 0], pm[:, 1], "x", color="red", ms=8, label="today silhouette points (same rows)")
ax2.set_xlim(600, 1400); ax2.set_ylim(-200, 1300); ax2.set_aspect("equal"); ax2.grid(alpha=0.3)
ax2.set_xlabel("half-breadth (mm)"); ax2.set_ylabel("z above DWL (mm)")
ax2.set_title("Head-on view: real topsides ~95-110 mm fuller at z 270-440\n(convex under the rail; today hollow)", fontsize=11)
ax2.legend(fontsize=8, loc="upper left")
# transom outline comparison (normalised)
ax3 = fig.add_axes([0.55, 0.06, 0.42, 0.42])
mt = np.load(f"{D}/model_transom_outline.npy")
sel = (mt[:, 0] <= 700) & (mt[:, 0] >= -150)
sil = np.nanmax(np.c_[mt[sel, 3], mt[sel, 4] * 1.045, np.nan_to_num(mt[sel, 5]) * 1.09], axis=1)
ax3.plot(sil / 870.0, mt[sel, 0], "o-", color="red", label="today: astern outline (max hb x7600-7800, persp.-weighted) / hb at rail")
ax3.plot(mt[sel, 1] / 690.0, mt[sel, 0], ":", color="red", lw=1, label="today: transom face half-width / face at rail")
R = np.array([(1290, 215), (1265, 250), (1255, 300), (1232, 400), (1215, 450), (1195, 500), (1175, 550), (1150, 600), (1120, 650), (1090, 700), (1065, 725)])
hw = (R[:, 0] - 640) / 650.0
zz = 804 - (R[:, 1] - 190) * (804 - 120) / (656 - 190)
ax3.plot(hw, zz, "s-", color="green", label="photo IMG_9391 outline from astern (approx. z mapping)")
ax3.axhline(804, color="#0090c0", ls="--"); ax3.text(0.02, 820, "rub rail", color="#0090c0")
ax3.set_xlim(0, 1.15); ax3.set_ylim(-100, 950); ax3.grid(alpha=0.3)
ax3.set_xlabel("half-width / half-width at rail level"); ax3.set_ylabel("z (mm, approx.)")
ax3.set_title("Transom outline from astern (scale-free; perspective +-10%)\nreal: smooth convex U, rounded corners; today: crease at face edge", fontsize=11)
ax3.legend(fontsize=8, loc="lower right")
fig.savefig(f"{D}/F_charts_profile_sections.png")
print("ok")
