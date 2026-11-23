"""Trace the exterior lines of the inboard profile (Enderlein 448-5) in
image pixels. Each line has a hand-read guide (from zoomed crops, +-3 px);
the tracer snaps the guide to the drawn line (sub-pixel centre of the ink).

Writes work/profile_px.json: {name: [[x, y, minval], ...]}
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from img import gray, WORK
from tracer import snap, column_scan, row_scan

a = gray()
out = {}


def lin(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    return lambda x: y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def piece(pts):
    p = np.asarray(pts, float)
    return lambda t: float(np.interp(t, p[:, 0], p[:, 1]))


# ---------------------------------------------------------------- hull outline
# The hull shell is drawn as a double line (outer + inner face, 3-4 px apart;
# 10 px under the keel). Each segment takes the OUTER line: lowest under the
# bottom, aft-most on the keel TE, forward-most on the LE and the stem.
segs = {}
# aft canoe body, transom foot to the keel fillet (column scans, lowest run)
AFTB = [(414, 628.3), (450, 629.4), (500, 630.7), (550, 630.9), (600, 634.0), (650, 635.0),
        (700, 634.8), (750, 636.4), (800, 637.3), (840, 638.2), (860, 638.9), (872, 641.5)]
r = column_scan(a, 414, 872, piece(AFTB), search=2.6, thr=205, pick="bottom")
segs["aft_bottom"] = r[:, :3]
# fillet: canoe body -> keel trailing edge (snap, outer = toward -y.. use guide order fwd->down)
FIL = [(872, 641.5), (882, 645.0), (892.4, 650.5), (901.4, 660.0), (907.5, 670.0), (909.2, 680.0)]
r = snap(a, FIL, step=1.0, search=2.5, thr=215, pick="outer", side=+1, max_jump=2.0)
segs["te_fillet"] = r[:, :3]
# trailing edge, near vertical (row scans, aft-most = left run)
TE = [(680, 909.2), (700, 908.8), (720, 908.3), (740, 907.6), (760, 906.9), (780, 906.0),
      (800, 904.2), (820, 902.0), (835, 899.0), (846, 897.5)]
r = row_scan(a, 681, 846, piece(TE), search=2.6, thr=222, pick="left")
segs["te"] = r[:, :3]
# keel bottom (outer = lower line, ~853.7)
r = column_scan(a, 899, 1238, lambda x: 853.7, search=2.6, thr=210, pick="bottom")
segs["keel_bottom"] = r[:, :3]
# leading edge from the bottom corner up to the keel/hull junction
LE = [(1225, 853.7), (1240, 852.5), (1257, 848.0), (1270, 842.5), (1283, 835.5), (1294, 830.0),
      (1311.4, 815.0), (1324.6, 800.0), (1342.9, 780.0), (1370, 750.0), (1393, 725.0),
      (1415.6, 700.0), (1428.5, 680.0), (1440, 666.0), (1452, 655.0), (1462, 646.5)]
r = snap(a, LE, step=1.0, search=3.0, thr=215, pick="outer", side=+1, max_jump=2.0)
segs["keel_le"] = r[:, :3]
# forward canoe body and forefoot (column scans, lowest run)
FWB = [(1462, 645.5), (1480, 640.2), (1500, 631.0), (1550, 623.5), (1600, 617.8), (1650, 614.5),
       (1700, 612.0), (1750, 606.5), (1800, 600.0), (1850, 591.0), (1900, 577.5), (1940, 564.5)]
r = column_scan(a, 1462, 1940, piece(FWB), search=2.6, thr=205, pick="bottom")
segs["fwd_bottom"] = r[:, :3]
# stem: forefoot -> stem head (snap, forward-most run)
STEM = [(1940, 564.5), (1960, 556.0), (1977.5, 550.0), (1994, 539.0), (2009, 526.0),
        (2025, 512.0), (2040, 500.0), (2052.4, 490.0), (2065, 478.0), (2075.6, 466.0),
        (2087, 454.0), (2098, 442.0), (2109, 430.0), (2119, 418.0), (2130.5, 406.0),
        (2141, 394.0), (2151, 382.0), (2161.5, 370.0), (2171, 358.0), (2182, 346.0),
        (2192.5, 334.0), (2201.5, 322.0), (2213.5, 308.0), (2224, 296.0), (2234, 284.0)]
r = snap(a, STEM, step=1.0, search=3.0, thr=200, pick="outer", side=+1, max_jump=2.0)
segs["stem"] = r[:, :3]
for k, v in segs.items():
    out["hull_" + k] = v.tolist()

# ---------------------------------------------------------------- transom
# Row profiles show three near-vertical lines: L_a (aft, dark), L_b (dark)
# and L_c (faint, 3.5 px forward of L_b). L_b + L_c are the transom shell
# (outer/inner face, like the hull's double line elsewhere); L_a, 9 px aft at
# the top and merging near y=520, is the rudder's leading edge. L_b reaches
# its aft-most point x=373.5 at y~315-330 (= plan transom, 7950) and rounds
# forward into the aft deck at (377, 300).
TB = [(305, 376.6), (315, 373.8), (322, 373.4), (330, 373.6), (345, 375.8), (360, 377.7),
      (380, 380.3), (400, 382.7), (420, 385.4), (440, 388.1), (460, 390.7), (480, 393.2),
      (500, 395.7), (520, 397.4), (540, 400.4), (560, 403.2), (580, 407.0), (600, 409.5),
      (615, 411.4), (622, 412.4)]
r = row_scan(a, 306, 622, piece(TB), search=2.2, thr=175, pick="nearest")
out["transom"] = r[:, :3].tolist()
TA = [(305, 361.0), (315, 362.0), (330, 364.4), (360, 368.5), (380, 371.3), (400, 374.0),
      (420, 376.7), (440, 379.3), (460, 381.7), (480, 384.4), (500, 387.0)]
r = row_scan(a, 305, 500, piece(TA), search=2.2, thr=175, pick="nearest")
out["rudder_le_upper"] = r[:, :3].tolist()

# ---------------------------------------------------------------- deck / roof
# foredeck on the centreline: upper of the two deck lines
g = lin((1750, 249.5), (2150, 257.7))
res = []
for x in range(1722, 2233):
    yg = g(x)
    col = a[int(yg) - 4:int(yg) + 4, x]
    ys = np.arange(int(yg) - 4, int(yg) + 4)
    m = col < 185
    if not m.any():
        continue
    # first (topmost) dark run
    i = np.argmax(m)
    j = i
    while j + 1 < len(m) and m[j + 1]:
        j += 1
    w = np.clip(185 - col[i:j + 1], 0, None) + 1e-6
    res.append((x, float(np.sum(ys[i:j + 1] * w) / w.sum()), float(col[i:j + 1].min())))
out["foredeck_cl"] = res

# coachroof front slope
r = snap(a, [(1719, 249.5), (1712, 243.0), (1706, 236.0), (1701, 231.0)], step=1.0,
         search=3.0, thr=185, pick="nearest")
out["coachroof_front"] = r[:, :3].tolist()

# roof top on the centreline (under the hatches): front to the sea hood
ROOF = [(1699, 229.5), (1670, 229.0), (1660, 228.5), (1650, 227.0), (1620, 224.5), (1600, 223.0),
        (1570, 221.0), (1545, 219.0), (1530, 217.0), (1510, 214.0), (1480, 212.0), (1450, 211.0),
        (1420, 210.0), (1380, 209.0), (1340, 208.5), (1300, 208.0), (1250, 207.5), (1200, 207.0),
        (1162, 206.5)]
g = piece(sorted(ROOF))
r = column_scan(a, 1162, 1699, g, search=2.5, thr=200, pick="nearest")
out["roof_cl"] = r[:, :3].tolist()

# sea hood / roof aft of the step at 1155 (lower pair), and sliding hatch (upper pair)
r = column_scan(a, 1067, 1150, lin((1067, 197.5), (1150, 199.5)), search=2.5, thr=190, pick="top")
out["seahood_top"] = r[:, :3].tolist()
r = column_scan(a, 903, 1152, lin((903, 184.5), (1152, 189.0)), search=2.5, thr=190, pick="top")
out["hatch_top"] = r[:, :3].tolist()
r = column_scan(a, 1537, 1653, lin((1537, 211.0), (1653, 213.5)), search=2.5, thr=190, pick="top")
out["forehatch_top"] = r[:, :3].tolist()

# aft face of the coachroof / companionway, from the hatch top down to the seat level
r = row_scan(a, 180, 328, lambda y: 900.0 + (y - 180.0) * (878.0 - 900.0) / (328.0 - 180.0),
             search=3, thr=180, pick="left")
out["coachroof_aft_face"] = r[:, :3].tolist()

# cockpit coaming top (single line from the coachroof aft face to the transom)
COAM = [(884, 240.0), (850, 244.0), (800, 249.5), (750, 254.5), (700, 259.0), (650, 263.0),
        (615, 265.0), (600, 266.5), (550, 270.0), (500, 274.5), (450, 279.0), (420, 282.0),
        (398, 284.5)]
g = piece(sorted(COAM))
r = column_scan(a, 398, 884, g, search=3, thr=190, pick="nearest")
out["coaming_top"] = r[:, :3].tolist()

# ---------------------------------------------------------------- hull side
# sheer / deck edge (faint line between deck and strake, bow to ~x=1360)
SHEER = [(2235, 265.0), (2200, 265.0), (2120, 266.5), (2040, 268.5), (1960, 270.4),
         (1880, 272.0), (1800, 274.0), (1720, 275.0), (1640, 276.0), (1520, 277.0),
         (1400, 278.0), (1350, 278.3)]
g = piece(sorted(SHEER))
r = column_scan(a, 1350, 2235, g, search=2.5, thr=232, pick="nearest")
out["sheer_line"] = r[:, :3].tolist()

# rubbing strake (faint line, bow to the head bulkhead)
STRK = [(2236, 270.0), (2200, 275.0), (2120, 283.0), (2040, 291.0), (1960, 299.0),
        (1880, 305.6), (1800, 312.0), (1760, 315.0), (1720, 318.0), (1680, 321.0),
        (1640, 323.6), (1600, 325.0), (1560, 327.6), (1520, 329.8), (1480, 330.5)]
g = piece(sorted(STRK))
r = column_scan(a, 1480, 2236, g, search=2.5, thr=232, pick="nearest")
out["strake_line"] = r[:, :3].tolist()
# dashed line aft at about y=345 (strake behind the cockpit?)
r = column_scan(a, 400, 880, lambda x: 345.0, search=3, thr=215, pick="nearest")
out["aft_dashed_345"] = r[:, :3].tolist()

# window: top edge, bottom edge, forward slanted end
r = column_scan(a, 1085, 1360, lin((1085, 290.0), (1360, 289.0)), search=3, thr=180, pick="nearest")
out["window_top"] = r[:, :3].tolist()
r = column_scan(a, 1088, 1376, lin((1090, 332.4), (1372, 323.0)), search=3, thr=180, pick="nearest")
out["window_bottom"] = r[:, :3].tolist()
r = snap(a, [(1361, 289.5), (1368, 298.0), (1374, 306.0), (1378, 313.0), (1377, 318.0)],
         step=1.0, search=3.0, thr=180, pick="nearest")
out["window_fwd_end"] = r[:, :3].tolist()

# ---------------------------------------------------------------- mast
for nm, xg in (("mast_aft_line", 1412.5), ("mast_fwd_line", 1447.0)):
    r = row_scan(a, 40, 198, lambda y, xg=xg: xg, search=3, thr=185, pick="nearest")
    out[nm] = r[:, :3].tolist()

# ---------------------------------------------------------------- DWL dashes
res = []
for x in list(range(205, 372)) + list(range(2015, 2115)):
    col = a[532:551, x]
    if col.min() < 205:
        ys = np.arange(532, 551)
        w = np.clip(215 - col, 0, None)
        res.append((x, float(np.sum(ys * w) / w.sum()), float(col.min())))
out["dwl_dashes"] = res

json.dump(out, open(os.path.join(WORK, "profile_px.json"), "w"))
for k, v in out.items():
    v = np.asarray(v)
    print(f"{k:20s} n={len(v):4d}  x {v[:, 0].min():7.1f}-{v[:, 0].max():7.1f}  "
          f"y {v[:, 1].min():6.1f}-{v[:, 1].max():6.1f}")
