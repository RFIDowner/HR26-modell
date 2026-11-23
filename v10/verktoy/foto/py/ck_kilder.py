"""Cockpit (trinn 7): maaler bronn, seter og brodekk i Enderleins 448-5 og
brosjyrens 1:50-tegninger, og lager sammenligningsbildet ck_kilder.png
(448-5 profil og plan, brosjyreplanen, modellens plan og senterlinjesnitt
med dagens bronn og forslaget i ck_spec.json). Uten CadQuery og uten bilder
med folk.

    python tools/memcap.py --gb 3 -- python v10/verktoy/foto/py/ck_kilder.py

x fra baugen, y halvbredde, z over DWL, fullskala mm.
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
from hr26 import curves as C  # noqa: E402
from hr26 import params as P  # noqa: E402

SRC = os.path.join(os.path.expanduser("~"), "Documents", "Seilbåt", "Hallberg-Rassy-kilder")
OUT = os.path.join(ROOT, "v10", "rapporter", "13nov_nye")
SPEC = json.load(open(os.path.join(OUT, "ck_spec.json"), encoding="utf-8"))
# cockpiten slik den ble bygget i commit d10de5d (448-5s raa tall), til sammenligning
D10 = {"seat": 898, "floor": 470, "x0": 6065, "x1": 7305, "hw": 330}

# ---------------------------------------------------------------- 448-5
E_S, E_U0, E_V0, E_VCL = 4.2591, 2240.1, 541.8, 1333.2      # enderlein_lines.json
E = np.asarray(Image.open(os.path.join(SRC, "HR26interior448-5.jpeg")).convert("L"), float)


def _runs(m):
    out, i = [], 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and m[j]:
                j += 1
            out.append((i, j - 1))
            i = j
        else:
            i += 1
    return out


def e_prof_col(x, thr=150):
    u = int(round(E_U0 - x / E_S))
    col = E[150:600, u - 1:u + 2].min(axis=1)
    return [round((E_V0 - (150 + 0.5 * (a + b))) * E_S) for a, b in _runs(col < thr)]


def e_prof_row(z, thr=150):
    v = int(round(E_V0 - z / E_S))
    row = E[v - 1:v + 2, 300:1000].min(axis=0)
    return [round((E_U0 - (300 + 0.5 * (a + b))) * E_S) for a, b in _runs(row < thr)]


def e_plan_col(x, hw=5, thr=150):
    u = int(round(E_U0 - x / E_S))
    col = E[1000:1700, u - hw:u + hw + 1].min(axis=1)
    return [round((E_VCL - (1000 + 0.5 * (a + b))) * E_S) for a, b in _runs(col < thr)]


def e_plan_row(y, hw=5, thr=150):
    v = int(round(E_VCL - y / E_S))
    row = E[v - hw:v + hw + 1, 350:900].min(axis=0)
    return [round((E_U0 - (350 + 0.5 * (a + b))) * E_S) for a, b in _runs(row < thr)]


# ------------------------------------------------- brosjyren (side 6, 1:50)
def _render_brochure(dpi=400):
    import pymupdf
    d = pymupdf.open(os.path.join(SRC, "HR26brochure.pdf"))
    pix = d[5].get_pixmap(dpi=dpi)
    return np.asarray(Image.open(io.BytesIO(pix.tobytes("png"))).convert("L"), float)


BR = _render_brochure()
BR_H = BR.shape[0]
# plan: kalibrert mot LOA (stevn 2887, akterspeil 445 px) og bredden (823 px = 2 679 mm)
BP_V0 = int(BR_H * 0.46)
BP_S, BP_U0, BP_VC = 7950.0 / 2442.0, 2887.0, 579.7 + BP_V0
# profil: tilpasset data/profile_top_silhouette.csv (median 1 mm); x kan ligge
# ca. 56 mm forut for planen (bronnens bakvegg 7 232 mot 7 288)
BF_V0 = int(BR_H * 0.72)
BF_S, BF_U0, BF_VD = 3.275, 2875.0, 624.4 + BF_V0


def b_plan_col(x):
    u = int(round(BP_U0 - x / BP_S))
    return [round((BP_VC - (a + b) / 2) * BP_S) for a, b in _runs(BR[:, u] < 128)
            if abs((BP_VC - (a + b) / 2) * BP_S) < 1500]


def b_plan_row(y):
    v = int(round(BP_VC - y / BP_S))
    return [round((BP_U0 - (300 + (a + b) / 2)) * BP_S) for a, b in _runs(BR[v, 300:1300] < 128)]


def b_prof_col(x):
    u = int(round(BF_U0 - x / BF_S))
    seg = BR[BF_V0 + 150:BF_V0 + 700, u] < 128
    return [round((BF_VD - (BF_V0 + 150 + (a + b) / 2)) * BF_S) for a, b in _runs(seg)]


def b_prof_row(z):
    v = int(round(BF_VD - z / BF_S))
    return [round((BF_U0 - (400 + (a + b) / 2)) * BF_S) for a, b in _runs(BR[v, 400:1400] < 128)]


def measure():
    m = {}
    m["e_prof_col"] = {x: e_prof_col(x) for x in (5850, 6200, 6600, 7000, 7500, 7700)}
    m["e_prof_row"] = {z: e_prof_row(z) for z in (520, 650, 800, 950)}
    m["e_plan_col"] = {x: e_plan_col(x) for x in (6300, 6700, 7100, 7300)}
    m["e_plan_row"] = {y: e_plan_row(y) for y in (0, 250, 500)}
    m["b_plan_col"] = {x: b_plan_col(x) for x in (6300, 6700, 7100, 7500)}
    m["b_plan_row"] = {y: b_plan_row(y) for y in (0, 200, 450)}
    m["b_prof_col"] = {x: b_prof_col(x) for x in (6300, 6900, 7200)}
    m["b_prof_row"] = {z: b_prof_row(z) for z in (500, 650, 900, 1150)}
    return m


# ------------------------------------------------------------- modellen
def _smin(a, b, k):
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k / 4.0


def well_hw(x):          # deckhouse.cockpit_half_width
    return max(200.0, _smin(P.COCKPIT_HALF_W, C.deck_half_breadth(x) - P.COCKPIT_INSET, P.WIDTH_BLEND))


def coam_hw(x):          # deckhouse.coaming_half_width
    return max(260.0, _smin(P.COAMING_HALF_W, C.deck_half_breadth(x) - 200.0, P.WIDTH_BLEND))


def well_outline():
    """Bronnens omriss (styrbord), som deckhouse._cockpit_stb uten hjornet."""
    x0, x1 = P.COCKPIT_X0, P.COCKPIT_AFT[0][0]
    pts = [(x, well_hw(x)) for x in np.linspace(x0, x1, 40)]
    pts += [(x, min(y, C.deck_half_breadth(x) - 200.0)) for x, y in P.COCKPIT_AFT]
    return np.array(pts)


def figure(m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

    sp = {k: v for k, v in SPEC["spec"].items()}
    fx0, fx1 = sp["footwell"]["x_fwd_top"]["value"], sp["footwell"]["x_aft_top"]["value"]
    hwf, hwa = sp["footwell"]["half_width_top"]["value"]
    zs, zf = sp["seats"]["top_z"]["value"], sp["footwell"]["sole_z"]["value"]
    zsill = sp["bridge_deck"]["companionway_sill_z"]["value"]

    fig = plt.figure(figsize=(18, 10.5), dpi=130)
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.05], hspace=0.28, wspace=0.12)
    X0, X1 = 5400, 8050

    # a) 448-5 profil
    ax = fig.add_subplot(gs[0, 0])
    u0, u1 = int(E_U0 - X1 / E_S), int(E_U0 - X0 / E_S)
    v0, v1 = int(E_V0 - 1450 / E_S), int(E_V0 - 250 / E_S)
    ax.imshow(E[v0:v1, u0:u1], cmap="gray", vmin=60, vmax=255,
              extent=[(E_U0 - u0) * E_S, (E_U0 - u1) * E_S, (E_V0 - v1) * E_S, (E_V0 - v0) * E_S])
    for z, lab in ((898, "sete 898"), (896, ""), (476, "durk 476")):
        if lab:
            ax.axhline(z, color="tab:red", lw=0.8, ls="--")
            ax.text(7950, z + 15, lab, color="tab:red", fontsize=8)
    for x, lab in ((6058, "fotbronn forut 6 058"), (7305, "bakvegg 7 305"), (5776, "ruffens akterflate 5 776")):
        ax.axvline(x, color="tab:blue", lw=0.8, ls="--")
        ax.text(x - 10, 1400, lab, color="tab:blue", fontsize=7, rotation=90, va="top")
    ax.text(5850, 930, "brodekk 896", color="tab:red", fontsize=8)
    ax.set_xlim(X1, X0)
    ax.set_title("Enderlein 448-5, profil 1:15 (z over tegningens DWL)", fontsize=10)
    ax.set_xlabel("x fra baugen (mm)")
    ax.set_ylabel("z (mm)")

    # b) 448-5 plan
    ax = fig.add_subplot(gs[0, 1])
    v0, v1 = int(E_VCL - 1350 / E_S), int(E_VCL + 1350 / E_S)
    ax.imshow(E[v0:v1, u0:u1], cmap="gray", vmin=60, vmax=255,
              extent=[(E_U0 - u0) * E_S, (E_U0 - u1) * E_S, (E_VCL - v1) * E_S, (E_VCL - v0) * E_S])
    ax.add_patch(Rectangle((6058, -330), 7305 - 6058, 660, fill=False, ec="tab:red", lw=1.0, ls="--"))
    ax.text(6650, -80, "fotbronn\n6 058-7 305\n±336 → ±317", color="tab:red", fontsize=8, ha="center")
    ax.add_patch(Rectangle((6141, 340), 6806 - 6141, 426, fill=False, ec="tab:green", lw=0.9, ls=":"))
    ax.text(6470, 520, "setekiste-lokk", color="tab:green", fontsize=7, ha="center")
    ax.add_patch(Rectangle((7307, -300), 7731 - 7307, 600, fill=False, ec="tab:green", lw=0.9, ls=":"))
    ax.text(7520, 330, "aktre benk", color="tab:green", fontsize=7, ha="center")
    ax.axvline(6048, color="tab:blue", lw=0.8, ls="--")
    ax.text(6030, -1300, "skott 6 048", color="tab:blue", fontsize=7, rotation=90, va="bottom")
    ax.set_xlim(X1, X0)
    ax.set_title("Enderlein 448-5, plan (stiplet = seter/lokk)", fontsize=10)
    ax.set_xlabel("x fra baugen (mm)")

    # c) brosjyren, plan 1:50
    ax = fig.add_subplot(gs[0, 2])
    u0, u1 = int(BP_U0 - X1 / BP_S), int(BP_U0 - X0 / BP_S)
    v0, v1 = int(BP_VC - 1350 / BP_S), int(BP_VC + 1350 / BP_S)
    ax.imshow(BR[v0:v1, u0:u1], cmap="gray", vmin=60, vmax=255,
              extent=[(BP_U0 - u0) * BP_S, (BP_U0 - u1) * BP_S, (BP_VC - v1) * BP_S, (BP_VC - v0) * BP_S])
    ax.add_patch(Rectangle((6067, -305), 7288 - 6067, 610, fill=False, ec="tab:red", lw=1.0, ls="--"))
    ax.text(6700, -560, "fotbronn 6 067-7 288\n±307 → ±280\n(traveller 6 067-6 137)", color="tab:red",
            fontsize=8, ha="center")
    ax.text(7480, 0, "aktre lokk\n7 288-7 672", color="tab:green", fontsize=7, ha="center", va="center")
    ax.text(6520, 520, "sidelokk 6 130-6 912\ny 302-723", color="tab:green", fontsize=7, ha="center")
    ax.text(5550, 940, "seterygg 782\nkarm innerkant 847", color="tab:purple", fontsize=7)
    ax.set_xlim(X1, X0)
    ax.set_title("Brosjyren, plan 1:50 (x kalibrert mot LOA, bredde 2 679)", fontsize=10)
    ax.set_xlabel("x fra baugen (mm)")

    # d) modellen, plan
    ax = fig.add_subplot(gs[1, 0:2])
    xs = np.linspace(5000, 7960, 300)
    hb = np.array([C.deck_half_breadth(x) for x in xs])
    ax.plot(xs, hb, "k", lw=1.0)
    ax.plot(xs, -hb, "k", lw=1.0, label="dekkskant")
    ch = np.array([coam_hw(x) for x in xs])
    mk = (xs > P.COCKPIT_X0 - P.COAMING_FWD) & (xs < P.COAMING_X1)
    ax.plot(xs[mk], ch[mk], color="0.5", lw=0.8)
    ax.plot(xs[mk], -ch[mk], color="0.5", lw=0.8, label="karmens ytterkant")
    wo = well_outline()
    poly = np.r_[wo, wo[::-1] * [1, -1]]
    ax.add_patch(Polygon(poly, closed=True, fc="#dde8f5", ec="tab:blue", lw=1.2,
                         label="bronnens omriss = setenes ytterkant (uendret)"))
    ax.add_patch(Rectangle((P.COCKPIT_X0, -wo[0, 1]), fx0 - P.COCKPIT_X0, 2 * wo[0, 1], fc="#f6d9b0",
                           ec="none", label=f"brodekk z {zs:.0f} (forslag)"))
    fw = np.array([(fx0, hwf), (fx1, hwa), (fx1, -hwa), (fx0, -hwf)])
    ax.add_patch(Polygon(fw, closed=True, fc="#f3b6b0", ec="tab:red", lw=1.4,
                         label=f"fotbronn {fx0:.0f}-{fx1:.0f}, ±{hwf:.0f}→±{hwa:.0f}, durk z {zf:.0f}"))
    lids = sp["seats"]["locker_lids_optional"]
    for key, col in (("side", "tab:green"), ("aft", "tab:green")):
        a = lids[key]
        ax.add_patch(Rectangle((a["x"][0], a["y"][0]), a["x"][1] - a["x"][0], a["y"][1] - a["y"][0],
                               fill=False, ec=col, ls=":", lw=1.0))
        if key == "side":
            ax.add_patch(Rectangle((a["x"][0], -a["y"][1]), a["x"][1] - a["x"][0], a["y"][1] - a["y"][0],
                                   fill=False, ec=col, ls=":", lw=1.0))
    R = D10   # det som ble bygget i commit d10de5d (samtidig med denne spesifikasjonen)
    ax.add_patch(Rectangle((R["x0"], -R["hw"]), R["x1"] - R["x0"], 2 * R["hw"], fill=False, ec="navy",
                           ls="--", lw=1.4, label=f"fotbronn i d10de5d {R['x0']}-{R['x1']} ±{R['hw']},"
                                                  f" sete {R['seat']}, durk {R['floor']}"))
    n = sp["bridge_deck"]["companionway_notch"]
    ax.add_patch(Rectangle((n["x"][0], -n["half_width"]), n["x"][1] - n["x"][0], 2 * n["half_width"],
                           fill=False, ec="tab:purple", lw=1.2, label="nedgang ned til brodekket (terskel)"))
    ax.axvline(P.COACH_X1, color="k", lw=0.8, ls="--")
    ax.text(P.COACH_X1 - 15, -1330, f"ruffens akterflate {P.COACH_X1:.0f} (lokket)", fontsize=8,
            rotation=90, va="bottom", ha="right")
    ax.text(6330, 560, "sete z %.0f" % zs, fontsize=9)
    ax.text(7330, 380, "aktre benk\nz %.0f" % zs, fontsize=8)
    ax.set_xlim(8000, 5250)
    ax.set_ylim(-1400, 1400)
    ax.set_aspect("equal")
    ax.legend(loc="lower left", fontsize=7.5, ncol=2, framealpha=0.9)
    ax.set_title("Modellen: commit d10de5d (stiplet blaa) og forslaget i ck_spec.json (farget) - plan, baugen til hoyre",
                 fontsize=10)
    ax.set_xlabel("x fra baugen (mm)")
    ax.set_ylabel("y (mm)")

    # e) modellen, senterlinjesnitt
    ax = fig.add_subplot(gs[1, 2])
    xs = np.linspace(5300, 7950, 200)
    ax.plot(xs, [C.deck_z(x, 0.0) for x in xs], "k", lw=1.0, label="dekket paa senterlinjen")
    ax.plot(xs, [C.sheer_z(x) for x in xs], color="0.5", lw=0.8, label="dekkskanten")
    ct = np.array(P.COAMING_TOP_Z)
    ax.plot(ct[:, 0], ct[:, 1], color="tab:blue", lw=0.8, ls="-.", label="karmtopp (tabell)")
    ax.plot([5300, P.COACH_X1, P.COACH_X1], [1375, 1375, 1110], "k", lw=1.2)
    ax.text(5320, 1390, "ruff (lokket)", fontsize=8)
    x_aft = P.COCKPIT_AFT[-1][0]
    ax.plot([P.COCKPIT_X0, P.COCKPIT_X0, x_aft, x_aft], [1190, 294, 294, 1000],
            color="0.6", lw=0.8, ls=":", label="foer trinn 7 (flat bronn, gulv 294)")
    R = D10
    ax.plot([P.COCKPIT_X0, P.COCKPIT_X0, R["x0"], R["x0"], R["x1"], R["x1"], x_aft, x_aft],
            [1190, R["seat"], R["seat"], R["floor"], R["floor"], R["seat"], R["seat"], 1000],
            color="navy", lw=1.0, ls="--", label=f"d10de5d (sete {R['seat']}, durk {R['floor']})")
    zsl = C.deck_z(P.COACH_X1, 0.0) + 60.0
    ax.plot([5480, P.COCKPIT_X0], [zsl, zsl], color="tab:purple", lw=1.2, ls=":",
            label=f"nedgangens terskel i d10de5d ({zsl:.0f})")
    prof = [(P.COCKPIT_X0, 1190), (P.COCKPIT_X0, zs), (fx0, zs), (fx0, zf), (fx1, zf), (fx1, zs),
            (x_aft, zs), (x_aft, 1000)]
    ax.plot(*zip(*prof), color="tab:red", lw=1.6, label="forslag: brodekk/sete, fotbronn")
    ax.plot([n["x"][0], P.COCKPIT_X0], [zsill, zsill], color="tab:purple", lw=2.0, label="nedgangens terskel (forslag)")
    # kildene, flyttet til modellens ramme
    ax.plot([5776, 6058], [866, 866], "o", color="tab:orange", ms=4, label="448-5 (z-30)")
    ax.plot([6058, 7305], [446, 446], "o", color="tab:orange", ms=4)
    ax.plot([5944, 7232], [418, 418], "s", color="tab:green", ms=4, label="brosjyreprofilen")
    ax.set_xlim(7980, 5300)
    ax.set_ylim(200, 1500)
    ax.legend(loc="lower right", fontsize=7)
    ax.set_title("Modellen, snitt paa senterlinjen (z over DWL)", fontsize=10)
    ax.set_xlabel("x fra baugen (mm)")
    fig.suptitle("HR 26 cockpit (trinn 7): kildene og forslaget i ck_spec.json - bilder med folk er ikke med",
                 fontsize=12)
    path = os.path.join(OUT, "ck_kilder.png")
    fig.savefig(path, dpi=110, bbox_inches="tight")
    print("lagret", path)


if __name__ == "__main__":
    mm = measure()
    for k, v in mm.items():
        print(k)
        for kk, vv in v.items():
            print("   ", kk, vv)
    figure(mm)
