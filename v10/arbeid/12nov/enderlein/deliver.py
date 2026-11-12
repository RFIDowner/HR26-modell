"""Deliverables: enderlein_lines.json, overlay_profile.png, overlay_plan.png and
the comparison tables (work/tables.md) used in enderlein_vs_model.md."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import calib as K
import lines as L
from img import SRC, OUT, WORK

C, P = L.model()
pm = L.profile_mm()
pl = L.plan_mm()


def at(name, v, axis=0):
    p = pm[name]
    o = 1 - axis
    s = p[np.argsort(p[:, axis])]
    if v < s[0, axis] - 1 or v > s[-1, axis] + 1:
        return np.nan
    return float(np.interp(v, s[:, axis], s[:, o]))


# ------------------------------------------------------------------ JSON
desc = {
    "hull_stem": "stem, outer face, centreline", "hull_fwd_bottom": "forefoot + canoe body to keel LE junction",
    "hull_keel_le": "keel leading edge incl. lower corner", "hull_keel_bottom": "keel bottom (outer line)",
    "hull_te": "keel trailing edge (faint)", "hull_te_fillet": "fillet TE -> canoe body",
    "hull_aft_bottom": "canoe body aft of keel to transom foot", "transom": "transom aft face, centreline",
    "rudder_le_upper": "rudder leading edge above hull (aft of transom)", "foredeck_cl": "foredeck top, centreline",
    "coachroof_front": "coachroof front slope, centreline", "roof_cl": "coachroof top, centreline (under hatches)",
    "forehatch_top": "fore hatch top", "seahood_top": "sea hood / roof step aft", "hatch_top": "sliding hatch top",
    "coachroof_aft_face": "coachroof aft face / companionway", "coaming_top": "cockpit coaming top (single line)",
    "sheer_line": "faint line between deck and strake: deck edge (medium confidence)",
    "strake_line": "rubbing strake (faint line)", "aft_dashed_345": "dashed line aft, z~830 (probably strake, low confidence)",
    "window_top": "hull window top", "window_bottom": "hull window bottom", "window_fwd_end": "hull window forward (slanted) end",
    "mast_aft_line": "mast aft face", "mast_fwd_line": "mast forward face", "dwl_dashes": "DWL dashes (z~0 check)",
}
J = {"_units": "mm full scale; x from the bow (plan bow tip), z above the drawing's DWL (dashed line), "
               "y half-breadth (plan; + = upper side of the sheet)",
     "_source": "Enderlein drawing 448-5 (HR 26, 1:15, 1977), scan HR26interior448-5.jpeg",
     "_calibration": {"S_mm_per_px": round(K.S, 4), "X_BOW_px": K.X_BOW, "X_TRANSOM_px": K.X_TRANSOM,
                      "Y_CL_plan_px": K.Y_CL, "Y_DWL_px": [K.Y_DWL_AFT, K.Y_DWL_FWD],
                      "isotropic": True},
     "profile": {}, "plan": {}}
for k, v in pm.items():
    J["profile"][k] = {"view": "profile", "what": desc.get(k, k),
                       "xz": np.round(v[:: max(1, len(v) // 400)], 1).tolist()}
for side in ("top", "bottom"):
    v = pl[side]
    J["plan"]["deck_outline_" + side] = {"view": "plan", "what": "deck outline (thick line, centre of ink), "
                                         + ("upper" if side == "top" else "lower") + " side of sheet",
                                         "x_halfbreadth": np.round(v[::4, :2], 1).tolist()}
for k in ("bow_rows", "transom_rows"):
    J["plan"]["outline_" + k] = {"view": "plan", "what": "outline traced by rows (ends)",
                                 "x_y_signed": np.round(pl[k][::2], 1).tolist()}
pd = json.load(open(os.path.join(WORK, "plan_extra_px.json"))) if os.path.exists(os.path.join(WORK, "plan_extra_px.json")) else {}
json.dump(J, open(os.path.join(OUT, "enderlein_lines.json"), "w"), indent=0)

# ------------------------------------------------------------------ model keel
root_z = C.bottom_z(0.5 * (P.KEEL_LE_ROOT + P.KEEL_TE_ROOT)) + 260.0


def keel_le_te(z):
    t = (z - root_z) / (P.KEEL_TIP_Z - root_z)
    t = min(max(t, 0.0), 1.0)
    le = P.KEEL_LE_ROOT + (P.KEEL_LE_TIP - P.KEEL_LE_ROOT) * t ** 0.85
    te = P.KEEL_TE_ROOT + (P.KEEL_TE_TIP - P.KEEL_TE_ROOT) * t ** 1.30
    return le, te


# ------------------------------------------------------------------ tables
T = []


def table(title, head, rows):
    T.append(f"\n**{title}**\n\n| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n")
    for r in rows:
        T.append("| " + " | ".join("–" if (isinstance(c, float) and np.isnan(c)) else
                                    (f"{c:.0f}" if isinstance(c, float) else str(c)) for c in r) + " |\n")


xs = np.linspace(0, 1600, 3201)
zz = np.array([C.bottom_z(v) for v in xs])
rows = []
for z in [1000, 900, 800, 600, 400, 200, 100, 0]:
    e = at("hull_stem", z, 1)
    m = float(np.interp(-z, -zz, xs))
    rows.append((f"{z}", e, m, e - m))
table("Stem, x at height z (E = Enderlein, M = model)", ["z", "x E", "x M", "E−M"], rows)

rows = []
for x in [600, 800, 1000, 1200, 1400, 1650, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200]:
    e = at("hull_fwd_bottom", x)
    if np.isnan(e):
        e = at("hull_stem", x)
    m = C.bottom_z(x)
    rows.append((f"{x}", e, m, e - m))
table("Forefoot and canoe body forward of the keel, z at x", ["x", "z E", "z M", "E−M"], rows)

rows = []
for z in [-500, -600, -700, -800, -900, -1000, -1100, -1200, -1300]:
    e = at("hull_keel_le", z, 1)
    le, te = keel_le_te(z)
    et = at("hull_te", z, 1)
    rows.append((f"{z}", e, le, e - le, et, te, et - te))
table("Keel leading and trailing edge, x at depth z", ["z", "LE E", "LE M", "E−M", "TE E", "TE M", "E−M"], rows)

rows = []
for x in [6000, 6200, 6400, 6600, 6800, 7000, 7200, 7400, 7600, 7700, 7760]:
    e = at("hull_aft_bottom", x)
    rows.append((f"{x}", e, C.bottom_z(x), e - C.bottom_z(x)))
table("Canoe body aft of the keel, z at x", ["x", "z E", "z M", "E−M"], rows)

rows = []
for z in [-340, -300, -200, -100, 0, 200, 400, 600, 800, 900, 950]:
    e = at("transom", z, 1)
    rows.append((f"{z}", e, C.transom_x(z), e - C.transom_x(z)))
table("Transom on the centreline, x at z", ["z", "x E", "x M", "E−M"], rows)

rows = []
for x in [50, 200, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3250, 3500, 3750]:
    s = at("strake_line", x)
    sh = at("sheer_line", x)
    dc = at("foredeck_cl", x)
    rows.append((f"{x}", sh, C.sheer_z(x), sh - C.sheer_z(x), dc, C.deck_z(x, 0.0), dc - C.deck_z(x, 0.0),
                 s, C.strake_z(x), s - C.strake_z(x)))
table("Hull side and foredeck, z at x", ["x", "deck edge E", "sheer M", "E−M", "deck CL E", "deck CL M", "E−M",
                                         "strake E", "strake M", "E−M"], rows)

ct = np.array(P.COACH_TOP)
rows = []
for x in [2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400]:
    e = at("roof_cl", x)
    m = float(np.interp(x, ct[:, 0], ct[:, 1]))
    rows.append((f"{x}", e, m, e - m))
table("Coachroof top on the centreline, z at x (M = COACH_TOP polyline)", ["x", "z E", "z M", "E−M"], rows)

ca = np.array(P.COAMING_TOP_Z)
rows = []
for x in [5800, 6000, 6200, 6400, 6600, 6800, 7000, 7400, 7800]:
    e = at("coaming_top", x)
    m = float(np.interp(x, ca[:, 0], ca[:, 1])) if x <= ca[-1, 0] else np.nan
    rows.append((f"{x}", e, m, e - m, C.sheer_z(x)))
table("Cockpit coaming top, z at x", ["x", "z E", "z M (COAMING_TOP_Z)", "E−M", "M sheer"], rows)

# plan
top, bot = pl["top"], pl["bottom"]
rows = []
br = np.loadtxt(os.path.join(L.SNAP, "data", "deck_halfbreadth.csv"), delimiter=",", skiprows=1)
for x in [100, 300, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 4800, 5000, 5500, 6000, 6500, 7000,
          7300, 7500, 7700, 7800, 7850, 7880]:
    a1 = float(np.interp(x, top[:, 0], top[:, 1]))
    a2 = float(np.interp(x, bot[:, 0], bot[:, 1]))
    e = 0.5 * (a1 + a2)
    m = C.deck_half_breadth(x)
    b = float(np.interp(x, br[:, 0], br[:, 1])) if x <= br[-1, 0] else np.nan
    rows.append((f"{x}", a1, a2, a2 - a1, e, m, e - m, b, e - b))
table("Deck outline half-breadth at x (E top/bottom side of the sheet = port/starboard)",
      ["x", "E top", "E bottom", "bottom−top", "E mean", "M", "E−M", "brochure trace", "E−brochure"], rows)
xm = top[np.argmax(top[:, 1])]
xb = bot[np.argmax(bot[:, 1])]
T.append(f"\nMax half-breadth E: top {xm[1]:.0f} at x={xm[0]:.0f}, bottom {xb[1]:.0f} at x={xb[0]:.0f}; "
         f"beam (centre of ink) {top[:, 1].max() + bot[:, 1].max():.0f} mm. Model max {2 * max(C.deck_half_breadth(v) for v in range(4000, 5600, 20)):.0f}.\n")
open(os.path.join(WORK, "tables.md"), "w", encoding="utf-8").write("".join(T))

# ------------------------------------------------------------------ overlays
RED, BLUE = (220, 20, 20), (0, 70, 230)


def draw_poly(d, pts, col, w=2):
    pts = [tuple(p) for p in pts if np.all(np.isfinite(p))]
    if len(pts) > 1:
        d.line(pts, fill=col, width=w)


im = Image.open(SRC).convert("RGB")
# profile
box = (180, 20, 2330, 900)
cr = im.crop(box)
d = ImageDraw.Draw(cr)
off = np.array([box[0], box[1]], float)


def p2i(x, z):
    px, py = K.prof_px(np.asarray(x, float), np.asarray(z, float))
    return np.c_[px, py] - off


X = np.linspace(0, 7950, 800)
draw_poly(d, p2i(X, [C.bottom_z(v) for v in X]), RED)
X2 = X[X < 7930]
draw_poly(d, p2i(X2, [C.sheer_z(v) for v in X2]), RED)
draw_poly(d, p2i(X2, [C.strake_z(v) for v in X2]), RED)
draw_poly(d, p2i(X[X < 2200], [C.deck_z(v, 0) for v in X[X < 2200]]), RED)
Z = np.linspace(C.bottom_z(7770), C.sheer_z(7940), 50)
draw_poly(d, p2i([C.transom_x(v) for v in Z], Z), RED)
zk = np.linspace(-1400, -380, 60)
le = [keel_le_te(v)[0] for v in zk]
te = [keel_le_te(v)[1] for v in zk]
okl = [z <= C.bottom_z(x) for x, z in zip(le, zk)]
okt = [z <= C.bottom_z(x) for x, z in zip(te, zk)]
draw_poly(d, p2i(np.array(le)[okl], zk[okl]), RED)
draw_poly(d, p2i(np.array(te)[okt], zk[okt]), RED)
draw_poly(d, p2i([P.KEEL_LE_TIP, P.KEEL_TE_TIP], [-1400, -1400]), RED)
draw_poly(d, p2i(ct[:, 0], ct[:, 1]), RED)
draw_poly(d, p2i([P.STEP_X0, P.STEP_X1], [C.deck_z(P.STEP_X0, 0), ct[0, 1]]), RED)
draw_poly(d, p2i(ca[:, 0], ca[:, 1]), RED)
for xw in (P.WIN_X0, P.WIN_X1):
    draw_poly(d, p2i([xw, xw], [C.strake_z(xw) + P.WIN_ABOVE_STRAKE, C.sheer_z(xw) - P.WIN_BELOW_DECK]), RED)
draw_poly(d, p2i([P.MAST_STEP_X] * 2, [1380, 1900]), RED)
for k, v in pm.items():
    if k == "dwl_dashes":
        continue
    al = 1 if k in ("hull_te", "hull_keel_le", "hull_stem", "transom", "rudder_le_upper", "coachroof_front",
                    "coachroof_aft_face", "window_fwd_end", "mast_aft_line", "mast_fwd_line") else 0
    s = v[np.argsort(v[:, al])]
    draw_poly(d, p2i(s[:, 0], s[:, 1]), BLUE)
draw_poly(d, p2i([-100, 8100], [0, 0]), (0, 150, 0), 1)
W = 2000
cr = cr.resize((W, int(cr.size[1] * W / cr.size[0])), Image.LANCZOS)
dd = ImageDraw.Draw(cr)
dd.text((10, 10), "Enderlein 448-5 profile: blue = traced (Enderlein), red = current model (V10 snapshot), green = DWL",
        fill=(0, 0, 0))
cr.save(os.path.join(OUT, "overlay_profile.png"))

# plan
im = Image.open(SRC).convert("RGB")
box = (300, 960, 2300, 1700)
cr = im.crop(box)
d = ImageDraw.Draw(cr)
off = np.array([box[0], box[1]], float)


def q2i(x, y):
    px, py = K.plan_px(np.asarray(x, float), np.asarray(y, float))
    return np.c_[px, py] - off


X = np.linspace(0, P.STERN_OUTLINE[-1][0], 700)
hb = np.array([C.deck_half_breadth(v) for v in X])
draw_poly(d, q2i(X, hb), RED)
draw_poly(d, q2i(X, -hb), RED)
yy = np.linspace(-hb[-1], hb[-1], 40)
draw_poly(d, q2i([C.transom_x(C.sheer_z(7940), abs(v)) for v in yy], yy), RED)
for side, sg in (("top", 1), ("bottom", -1)):
    v = pl[side]
    draw_poly(d, q2i(v[:, 0], sg * v[:, 1]), BLUE)
t = pl["transom_rows"]
draw_poly(d, q2i(t[:, 0], t[:, 1]), BLUE)
b = pl["bow_rows"]
draw_poly(d, q2i(b[:, 0], b[:, 1]), BLUE)
cr = cr.resize((W, int(cr.size[1] * W / cr.size[0])), Image.LANCZOS)
dd = ImageDraw.Draw(cr)
dd.text((10, 10), "Enderlein 448-5 plan: blue = traced deck outline, red = current model deck edge + transom",
        fill=(0, 0, 0))
cr.save(os.path.join(OUT, "overlay_plan.png"))
print("ok")
