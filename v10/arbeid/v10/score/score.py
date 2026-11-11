#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HR 26 V10 scorecard  (score.py)
===============================

Scores ONE hull STL of the 1:30 Hallberg-Rassy 26 model and writes a JSON with
all numbers plus ONE summary PNG (1600 px wide).  Runs in about 1-3 minutes.

USAGE
    python score.py HULL.stl [options]

    HULL.stl  either the plate-placed export/stl/01_skrog.stl (turned about Z on
              the bed, keel at z=0; the angle is fitted, normally 45 deg) or a
              boat-frame STL from build_hull_only.py (x from the bow, y across,
              z up, keel at z=0).  Detected automatically.

    --frame auto|plate|boat  force the input frame (default auto)
    --out DIR                output folder (default: <this folder>/out)
    --name TAG               stem of the output files (default: STL file stem)
    --ref REF.json           earlier score JSON to diff against (default:
                             <this folder>/out/baseline_fine_score.json if it
                             exists and is not the file being written)
    --anchor auto|mast|bow   x registration in the build frame: centre of the
                             mast hole = 3400 (auto; falls back to bow) or the
                             bow tip = --xbow
    --xbow MM                build-frame x of the bow tip for --anchor bow (4.0)
    --rays N                 wall-thickness rays (default 30000)
    --photos DIR             folder with IMG_9388/9391/9370/9389.jpeg
                             (default C:/Users/stig/Documents/Seilbåt)
    --no-render              numbers only, no PNG
    --jobs N                 render threads (default 6)

    Example (both of today's hulls, the "before" numbers):
        python score.py ../baseline_fine.stl --name baseline_fine
        python score.py C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl --name skrog_today

OUTPUTS
    DIR/TAG_score.json   every number; lengths are FULL-SCALE mm unless the key
                         ends in _model (model mm, 1:30).  "summary" holds the
                         headline numbers with PASS/FAIL for the V10 requirements.
    DIR/TAG_score.png    summary sheet: score table, 6 Bambu-style flat-shaded
                         views, 4 photo-matched views (photo | model, model
                         silhouette drawn in cyan on the photo), and plots of the
                         line deviations, waterline curvature and wall thickness.

FRAME AND CONVENTIONS
    Build frame, full scale: x from the bow aft, y to starboard, z up from the
    DWL; keel bottom at z = -1400 (model z = 0, DWL at model z = 46.67).
    The STL itself has no absolute x reference, so x is registered on the mast
    hole (centre = MAST_STEP_X = 3400, the interface that must not move); if no
    mast hole is found the bow tip is put at --xbow (today's hull: x = 4).
    Draft cannot be measured from a keel-at-zero STL; it is checked through the
    rudder-pin holes, which are positioned in the build frame (z = -90/-200).

WHAT IS MEASURED (keys in the JSON)
  mesh       triangles, file size, welded vertices; dihedral angles between
             adjacent triangles on the hull topsides/bottom (strake band, keel
             root, window recess, ends excluded): share > 5 and > 10 deg and
             percentiles; sliver share (longest edge / its altitude > 20).
  lines      deck outline (virtual intersection of side and deck, so a rounded
             deck edge is judged on the same line as a sharp one) vs
             data/deck_halfbreadth.csv (x < 7300) + STERN_OUTLINE: plan distance
             max/rms; sheer vs DECK_EDGE_Z at the table points; strake centre
             height vs hull_stations.csv strake_z_mm; LOA (stem head to transom
             top on the centreline), beam (deck line and overall), draft check;
             underwater centreline profile vs data/uw_station.csv by segment
             (propeller and rudder ranges of the trace are skipped).
  fairness   waterlines z = +150/+400/+700/+900 above the DWL and the deck edge
             (plan and profile), all sampled on the STL as printed:
               sign_changes   curvature reversals, |k| > 0.02 1/m (profile
                              0.005), Gaussian sigma 60 mm = the SHAPE scale
               ripple_rms     rms of k(sigma 25 mm) - k(sigma 60 mm), 1/m: the
                              facet/short-ripple content (lower = smoother)
               max_jump_50mm  largest change of k (sigma 25) over 50 mm, 1/m
               wiggle_lt1m    deviation from a 1 m low-pass, x 1500-6800, mm
             Strake band and window recess are cut out of the waterlines (the
             +900 waterline is mostly strake, so it covers only x<1950/x>6000).
             10 sections (x 1400-7250): curvature reversals keel->strake
             (sigma 15 mm, |k| > 0.1 1/m) and the DWL crease index = mean side
             angle from vertical in z -60..-5 minus that in z +5..+60 (deg).
  interfaces deck holes (stanchions, pulpit, pushpit) and the mast hole from
             horizontal slices, rudder-pin holes from vertical slices: count,
             positions, diameters, closed depth, vs design and vs today's hull
             (TODAY_HOLES, measured on baseline_fine.stl).
  shell      closed/manifold (exact topology after a 1e-5 mm weld; the
             tools/meshcheck.py 1e-4 weld count is reported too), shells,
             volumes, cavities that open to the outside through deck holes, and
             the wall thickness by ray casting along the inward normal from
             sampled points on the hull sides and deck (grazing exits at sharp
             edges are ignored; the thinnest spots are listed with the nearest
             deck hole).

Curvature numbers depend on the smoothing scale and on the tessellation (even
baseline_fine.stl has topside triangles 100-250 mm long); they are meant for
round-to-round comparison, not as absolute truth.  Photos are perspective
views; the photo-matched cameras were solved once (dev/fit_*.py) from traced
hull outlines and a few landmarks, with residuals of roughly 10-30 photo px,
so treat the overlays as a visual check, not a measurement.  Rudder, rig,
stands and water are in the photos but not in the hull STL.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import os
import re
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

VERSION = "1.0 (2026-11-10)"
HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# Frozen copies of the measured lines and design constants (10.11.2026).
# Measurements must not follow later edits of params.py, so they live here.
# ============================================================================
SCALE = 30.0
DRAFT = 1400.0
LOA = 7950.0
BEAM = 2680.0
DIM_TOL = 0.005                 # +-0.5 % on LOA, beam, draft (CLAUDE.md)
LINE_TOL = 12.5                 # one 0.25 mm line of the 1:50 drawings
TRANSOM_WL_X = 7806.0
TRANSOM_RAKE = 0.146
TRANSOM_CAMBER_R = 3050.0
STRAKE_H = 95.0
DECK_CAMBER = 30.0
MAST_STEP_X = 3400.0
MAST_HOLE_XY = (135.0, 105.0)   # oval hole, for-aft x across
MAST_SOCKET = 330.0
STANCHION_X = [1450.0, 2500.0, 3550.0, 4600.0, 5650.0, 6700.0]
PULPIT_X = [520.0, 900.0]
PUSHPIT_X = [7250.0, 7680.0]
DECK_HOLE_D = 36.0              # STANCHION_D + CLEAR
DECK_HOLE_DEPTH = 210.0
RUDDER_PIN_Z = (-90.0, -200.0)
RUDDER_PIN_HOLE_D = 42.0
WIN_X = (3700.0, 4900.0)

DECK_EDGE_Z = [
    (0.0, 1204.0), (1000.0, 1204.0), (2000.0, 1200.0), (2500.0, 1175.0),
    (3000.0, 1150.0), (3750.0, 1122.0), (4200.0, 1115.0), (4500.0, 1105.0),
    (5000.0, 1095.0), (5500.0, 1085.0), (6000.0, 1080.0), (6500.0, 1075.0),
    (7000.0, 1056.0), (7200.0, 1040.0), (7400.0, 1020.0), (7600.0, 992.0),
    (7800.0, 962.0), (7950.0, 940.0),
]
STERN_OUTLINE = [
    (7300.0, 995.0), (7400.0, 968.0), (7500.0, 944.0), (7600.0, 916.0),
    (7700.0, 890.0), (7750.0, 866.0), (7800.0, 835.0), (7820.0, 812.0),
    (7840.0, 773.0), (7860.0, 730.0), (7880.0, 650.0), (7891.0, 605.0),
]
# data/deck_halfbreadth.csv (raw trace of the 1:50 deck plan)
DECK_HB = [
    (0.0, 84.9), (100.6, 154.8), (201.3, 189.4), (301.9, 234.5), (402.5, 272.7), (503.2, 309.7),
    (603.8, 346.1), (704.4, 382.3), (805.1, 417.7), (905.7, 453.3), (1006.3, 488.3), (1107.0, 523.2),
    (1207.6, 557.6), (1308.2, 592.0), (1408.9, 625.9), (1509.5, 659.9), (1610.1, 693.5), (1710.8, 726.8),
    (1811.4, 759.9), (1912.0, 792.2), (2012.7, 823.9), (2113.3, 855.3), (2213.9, 885.8), (2314.6, 915.7),
    (2415.2, 945.1), (2515.8, 970.2), (2616.5, 980.1), (2717.1, 1007.2), (2817.7, 1033.1), (2918.4, 1058.2),
    (3019.0, 1085.7), (3119.6, 1126.8), (3220.3, 1148.7), (3320.9, 1169.5), (3421.5, 1188.8), (3522.2, 1207.3),
    (3622.8, 1223.9), (3723.4, 1239.6), (3824.1, 1255.1), (3924.7, 1269.7), (4025.3, 1283.0), (4125.9, 1296.1),
    (4226.6, 1308.2), (4327.2, 1318.3), (4427.8, 1327.2), (4528.5, 1334.7), (4629.1, 1340.6), (4729.7, 1344.8),
    (4830.4, 1347.7), (4931.0, 1348.7), (5031.6, 1348.2), (5132.3, 1345.5), (5232.9, 1340.6), (5333.5, 1333.8),
    (5434.2, 1325.0), (5534.8, 1314.1), (5635.4, 1302.7), (5736.1, 1290.4), (5836.7, 1277.4), (5937.3, 1263.6),
    (6038.0, 1249.6), (6138.6, 1234.2), (6239.2, 1218.4), (6339.9, 1201.7), (6440.5, 1185.0), (6541.1, 1166.7),
    (6641.8, 1147.4), (6742.4, 1127.5), (6843.0, 1106.6), (6943.7, 1084.3), (7044.3, 1061.5), (7144.9, 1038.0),
    (7245.6, 1013.5), (7346.2, 988.3), (7446.8, 962.8), (7547.5, 934.9), (7648.1, 886.1), (7748.7, 714.7),
    (7849.4, 745.1), (7950.0, 106.1),
]
# data/hull_stations.csv: x, deck half-breadth, strake_z_mm, canoe_bottom_z_mm
HULL_STATIONS = [
    (0, 84.9, 1125.0, -0.0), (150, 171.8, 1114.3, -0.0), (300, 233.6, 1101.3, -0.0), (450, 290.1, 1089.5, -0.0),
    (600, 344.8, 1077.7, -0.0), (750, 398.3, 1066.3, -5.7), (900, 451.3, 1055.6, -27.1),
    (1050, 503.4, 1045.0, -60.4), (1200, 555.0, 1034.5, -101.8), (1350, 606.1, 1024.0, -150.0),
    (1500, 656.7, 1013.4, -195.3), (1650, 706.7, 1002.9, -228.1), (1800, 756.1, 992.4, -252.0),
    (1950, 804.2, 981.8, -271.8), (2100, 851.2, 971.3, -288.3), (2250, 896.5, 960.8, -305.4),
    (2400, 940.7, 950.3, -323.8), (2550, 973.6, 939.7, -343.5), (2700, 1002.6, 929.2, -366.1),
    (2850, 1041.2, 918.7, -395.6), (3000, 1080.5, 908.1, -435.9), (3150, 1133.4, 897.6, -470.7),
    (3300, 1165.2, 887.1, -500.3), (3450, 1194.0, 877.3, -522.1), (3600, 1220.2, 868.5, -532.5),
    (3750, 1243.7, 860.7, -527.9), (3900, 1266.1, 853.8, -523.3), (4050, 1286.2, 848.2, -518.7),
    (4200, 1305.0, 843.3, -514.1), (4350, 1320.3, 839.1, -509.5), (4500, 1332.6, 835.6, -504.8),
    (4650, 1341.5, 831.8, -500.2), (4800, 1346.9, 828.0, -495.6), (4950, 1348.6, 824.4, -491.0),
    (5100, 1346.4, 820.9, -486.4), (5250, 1339.5, 817.5, -481.8), (5400, 1328.0, 815.1, -477.2),
    (5550, 1312.4, 813.3, -472.6), (5700, 1294.8, 811.7, -464.4), (5850, 1275.6, 810.4, -497.9),
    (6000, 1254.9, 809.4, -520.1), (6150, 1232.4, 808.7, -531.2), (6300, 1208.3, 808.0, -525.9),
    (6450, 1183.2, 807.1, -525.2), (6600, 1155.4, 806.1, -483.7), (6750, 1125.9, 805.3, -454.4),
    (6900, 1094.0, 804.6, -438.5), (7050, 1060.2, 804.1, -439.8), (7200, 1024.6, 804.0, -432.6),
    (7350, 987.4, 804.0, -410.0), (7500, 948.1, 804.0, -372.0), (7650, 882.9, 804.0, -317.2),
    (7800, 730.2, 804.0, -247.1), (7950, 106.1, 804.0, -170.0),
]
# data/uw_station.csv (lower silhouette of the 1:50 profile), 20 mm bin means,
# x <= 7450 (aft of that the trace is the rudder).  x:depth below DWL.
UW_TABLE = """
1013:7.3 1030:16.4 1049:27.8 1069:38.0 1090:50.3 1111:64.0 1131:73.5 1150:82.6 1170:93.9 1190:102.3
1209:112.7 1229:121.4 1250:127.0 1271:135.2 1291:145.5 1310:151.2 1330:156.8 1350:166.0 1369:173.9
1389:179.2 1410:183.8 1431:190.4 1451:195.5 1470:200.6 1490:204.7 1510:208.5 1529:215.5 1549:217.1
1570:223.7 1591:226.9 1611:231.0 1630:234.0 1650:240.8 1670:243.2 1689:243.2 1709:246.7 1730:252.9
1751:253.1 1771:253.1 1790:253.2 1810:257.3 1830:259.6 1849:259.6 1869:261.0 1890:268.3 1911:269.5
1931:269.5 1950:271.8 1970:278.6 1989:279.3 2009:279.3 2029:280.9 2050:285.5 2071:285.9 2091:285.9
2110:289.4 2130:295.5 2149:295.8 2169:295.8 2189:299.3 2210:305.4 2231:305.6 2251:306.6 2270:311.3
2290:312.2 2309:312.2 2329:313.6 2349:320.7 2370:322.1 2391:322.3 2411:328.4 2430:331.9 2450:331.9
2469:332.1 2489:336.2 2509:338.5 2530:338.5 2551:340.8 2571:347.7 2590:348.4 2610:348.6 2629:354.7
2649:358.2 2669:358.2 2690:360.2 2711:364.6 2731:364.8 2750:364.8 2770:365.5 2789:372.3 2809:374.9
2829:381.0 2850:384.5 2871:387.8 2891:391.8 2910:398.6 2930:402.3 2949:409.4 2969:412.4 2990:417.2
3011:423.7 3031:430.8 3051:437.8 3070:443.0 3090:450.0 3109:457.0 3129:465.5 3150:471.8 3171:482.6
3191:490.4 3211:497.7 3230:507.7 3250:517.6 3269:527.3 3289:537.5 3310:548.0 3331:562.4 3351:573.0
3371:585.0 3390:598.4 3410:611.3 3429:624.2 3449:637.6 3470:652.2 3491:670.0 3511:682.9 3531:700.7
3550:716.6 3570:733.6 3589:752.6 3609:772.4 3630:796.9 3651:820.0 3671:842.2 3691:863.1 3710:882.9
3730:902.4 3749:922.2 3769:942.0 3790:963.3 3811:984.7 3831:1004.5 3850:1024.0 3870:1042.5
3890:1055.8 3909:1074.7 3929:1094.4 3950:1110.8 3971:1128.4 3991:1146.7 4010:1159.9 4030:1178.6
4050:1195.8 4069:1209.5 4089:1225.1 4110:1235.2 4131:1250.5 4151:1260.1 4170:1270.7 4190:1283.4
4210:1293.9 4229:1304.9 4249:1311.5 4270:1319.3 4291:1327.5 4311:1333.3 4330:1338.8 4350:1346.3
4370:1353.8 4389:1357.3 4409:1358.2 4430:1363.1 4451:1364.6 4471:1371.4 4490:1373.7 4510:1373.7
4530:1374.4 4549:1381.2 4569:1383.6 4590:1383.6 4611:1383.6 4631:1385.1 4650:1389.7 4670:1390.1
4690:1390.1 4709:1390.1 4729:1390.1 4750:1390.1 4771:1390.1 4791:1390.9 4810:1397.7 4830:1400.0
4850:1400.0 4869:1400.0 4889:1400.0 4910:1400.0 4931:1400.0 4951:1400.0 4970:1400.0 4990:1400.0
5010:1400.0 5029:1400.0 5049:1400.0 5070:1400.0 5091:1400.0 5111:1400.7 5130:1407.5 5150:1409.9
5170:1409.9 5189:1409.9 5209:1409.9 5230:1409.9 5251:1409.9 5271:1409.9 5290:1409.9 5310:1409.9
5329:1409.9 5349:1409.9 5369:1409.9 5390:1409.9 5411:1409.9 5431:1409.9 5450:1409.9 5470:1409.9
5489:1409.9 5509:1409.9 5529:1409.9 5550:1409.7 5571:1403.5 5591:1400.0 5610:1400.0 5630:1400.0
5649:1400.0 5669:1400.0 5689:1277.5 5710:639.2 5731:517.5 5751:507.0 5770:496.1 5790:487.8
5809:477.0 5829:469.3 5849:464.3 5870:460.4 5891:453.8 5911:451.2 5930:444.4 5950:443.7 5969:443.7
5989:442.3 6009:443.2 6030:464.7 6051:503.3 6071:578.6 6090:651.4 6110:675.4 6129:680.5 6149:686.6
6170:690.1 6191:690.1 6211:690.1 6231:690.1 6250:690.1 6270:690.1 6289:686.6 6309:680.5 6330:679.9
6351:676.2 6371:697.1 6391:750.1 6410:700.2 6430:648.0 6449:538.7 6469:437.1 6490:437.1 6511:437.1
6531:437.1 6551:437.1 6570:437.1 6590:437.1 6609:437.1 6629:437.1 6650:437.1 6671:437.1 6691:437.1
6711:437.1 6730:437.1 6750:437.1 6769:437.1 6789:437.1 6810:437.1 6831:437.1 6851:437.1 6871:437.1
6890:437.1 6910:437.1 6929:437.1 6949:437.6 6970:442.3 6991:443.7 7011:443.7 7031:441.3 7050:438.2
7070:442.7 7089:443.7 7109:443.7 7130:443.7 7151:443.7 7171:443.7 7190:443.7 7210:443.7 7230:443.7
7249:443.7 7269:443.7 7290:443.7 7311:443.7 7331:443.7 7350:443.7 7370:443.7 7390:443.7 7409:443.7
7429:443.7 7450:453.6
"""
# Segments of the trace used for the comparison.  6030-6450 is the propeller
# and > 7450 the rudder (neither is part of the hull STL).  The aft run
# 6470-7440 is a dead-flat line in the trace and probably not the hull bottom:
# reported, but marked as uncertain.
UW_SEGMENTS = [("canoe_fwd", 1010, 3100), ("keel_le", 3110, 4800), ("keel_bottom", 4830, 5670),
               ("canoe_aft_of_keel", 5730, 6010), ("aft_trace_uncertain", 6470, 7440)]

_HS = np.array(HULL_STATIONS, float)
_DHB = np.array(DECK_HB, float)
_DEZ = np.array(DECK_EDGE_Z, float)
_SO = np.array(STERN_OUTLINE, float)
_UW = np.array([[float(a) for a in t.split(":")] for t in UW_TABLE.split()], float)


def hb_meas(x):
    """Measured deck half-breadth: trace for x < 7300, STERN_OUTLINE aft of it."""
    x = np.asarray(x, float)
    a = np.interp(x, _DHB[:, 0], _DHB[:, 1])
    b = np.interp(x, _SO[:, 0], _SO[:, 1])
    return np.where(x < 7300.0, a, b)


def sheer_meas(x):
    return np.interp(x, _DEZ[:, 0], _DEZ[:, 1])


def strake_meas(x):
    return np.interp(x, _HS[:, 0], _HS[:, 2])


def bottom_meas(x):
    return np.interp(x, _HS[:, 0], _HS[:, 3])


def transom_x(z, y=0.0):
    R = TRANSOM_CAMBER_R
    y = np.minimum(np.abs(y), R)
    sag = R - np.sqrt(R * R - y * y)
    return TRANSOM_WL_X + TRANSOM_RAKE * np.asarray(z, float) - sag * math.sqrt(1 + TRANSOM_RAKE ** 2)


def log(*a):
    print(*a, flush=True)


# ============================================================================
# STL loading, welding, topology
# ============================================================================
def load_stl(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) >= 84:
        n = struct.unpack("<I", data[80:84])[0]
        if n > 0 and 84 + 50 * n == len(data):
            dt = np.dtype([("n", "<f4", (3,)), ("v", "<f4", (3, 3)), ("a", "<u2")])
            rec = np.frombuffer(data, dtype=dt, count=n, offset=84)
            return rec["v"].astype(np.float64), "binary"
    txt = data.decode("latin-1")
    vals = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", txt)
    if not vals:
        raise ValueError(f"{path}: neither binary nor ASCII STL")
    T = np.array(vals, dtype=np.float64).reshape(-1, 3, 3)
    return T, "ascii"


def weld(T, tol=1e-5):
    """Quantized weld (tools/meshcheck.py logic). Returns verts (nv,3), F (nf,3)."""
    V = T.reshape(-1, 3)
    q = np.round(V / tol).astype(np.int64)
    o = np.lexsort((q[:, 2], q[:, 1], q[:, 0]))
    qs = q[o]
    new = np.empty(len(qs), bool)
    new[0] = True
    new[1:] = np.any(qs[1:] != qs[:-1], axis=1)
    ids = np.cumsum(new) - 1
    inv = np.empty(len(q), np.int64)
    inv[o] = ids
    return V[o[new]].copy(), inv.reshape(-1, 3)


def edge_topology(F, nv):
    """Undirected edges with their face pair, manifold and orientation checks."""
    nf = len(F)
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    a = np.minimum(e[:, 0], e[:, 1])
    b = np.maximum(e[:, 0], e[:, 1])
    key = a * np.int64(nv) + b
    o = np.argsort(key, kind="stable")
    ks = key[o]
    start = np.r_[0, np.nonzero(ks[1:] != ks[:-1])[0] + 1]
    cnt = np.diff(np.r_[start, len(ks)])
    man = cnt == 2
    h1 = o[start[man]]
    h2 = o[start[man] + 1]
    same_dir = e[h1, 0] == e[h2, 0]          # both faces walk the edge the same way
    return dict(n_edges=int(len(start)), n_nonmanifold=int((cnt != 2).sum()),
                n_boundary=int((cnt == 1).sum()), n_over=int((cnt > 2).sum()),
                n_flipped=int(same_dir.sum()),
                f1=h1 % nf, f2=h2 % nf, ev=np.c_[a[h1], b[h1]])


def components(F, nv):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    a = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
    b = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
    g = coo_matrix((np.ones(len(a), np.int8), (a, b)), shape=(nv, nv))
    n, lab = connected_components(g, directed=False)
    return n, lab[F[:, 0]]


def signed_volume(V, F):
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    return np.einsum("ij,ij->i", A, np.cross(B, C)) / 6.0


def face_geom(V, F):
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(B - A, C - A)
    a2 = np.linalg.norm(n, axis=1)
    fn = n / np.maximum(a2, 1e-30)[:, None]
    l = np.stack([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1),
                  np.linalg.norm(A - C, axis=1)], 1)
    lmax = l.max(1)
    aspect = lmax ** 2 / np.maximum(a2, 1e-30)      # longest edge / its altitude
    return fn, 0.5 * a2, (A + B + C) / 3.0, aspect, lmax


# ============================================================================
# Frame detection: plate (turned about Z) or boat frame -> full-scale build frame
# ============================================================================
def _sym_metric(xy, ang_deg, nb=80):
    a = math.radians(ang_deg)
    c, s = math.cos(a), math.sin(a)
    xr = xy[:, 0] * c + xy[:, 1] * s
    yr = -xy[:, 0] * s + xy[:, 1] * c
    lo, hi = xr.min(), xr.max()
    L = hi - lo
    b = np.clip(((xr - lo) / L * nb).astype(int), 0, nb - 1)
    ymax = np.full(nb, -np.inf)
    ymin = np.full(nb, np.inf)
    np.maximum.at(ymax, b, yr)
    np.minimum.at(ymin, b, yr)
    k = slice(int(0.05 * nb), int(0.95 * nb))
    mid = 0.5 * (ymax[k] + ymin[k])
    ok = np.isfinite(mid)
    return float(np.std(mid[ok]))


def detect_frame(Vm, mode="auto"):
    """Vm welded vertices in model mm.  Returns dict with rotation (deg, the STL
    was turned by +rot about Z), flip (bool) and the frame name."""
    xy = Vm[:, :2]
    c = xy.mean(0)
    cov = np.cov((xy - c).T)
    w, U = np.linalg.eigh(cov)
    ax = U[:, 1]
    th = math.degrees(math.atan2(ax[1], ax[0]))
    th = (th + 90.0) % 180.0 - 90.0
    if mode == "boat" or (mode == "auto" and abs(th) < 5.0):
        frame, rot = "boat", 0.0
    else:
        frame = "plate"
        # refine by port/starboard symmetry of the plan silhouette
        sub = xy[:: max(1, len(xy) // 150000)]
        grid = np.arange(th - 2.0, th + 2.0001, 0.1)
        vals = [_sym_metric(sub, g) for g in grid]
        g0 = grid[int(np.argmin(vals))]
        grid = np.arange(g0 - 0.12, g0 + 0.12001, 0.005)
        vals = [_sym_metric(sub, g) for g in grid]
        rot = float(grid[int(np.argmin(vals))])
        if abs(rot - round(rot)) < 0.03:      # build_hull uses whole degrees
            rot = float(round(rot))
    a = math.radians(-rot)
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])
    P = Vm @ R.T
    # bow at min x: the keel (lowest points) lies 60-75 % aft of the bow
    z0 = P[:, 2].min()
    low = P[:, 2] < z0 + 0.4
    L = P[:, 0].max() - P[:, 0].min()
    fk = (P[low, 0].mean() - P[:, 0].min()) / L
    # second opinion: the bow end is narrow
    xs = P[:, 0]
    nar = lambda m: np.ptp(P[m, 1]) if m.any() else 0.0
    w_lo = nar(xs < xs.min() + 0.03 * L)
    w_hi = nar(xs > xs.max() - 0.03 * L)
    flip = fk < 0.5
    agree = (w_lo < w_hi) != flip
    return dict(frame=frame, rot_deg=rot, pca_deg=th, flip=bool(flip), keel_frac=float(fk),
                bow_check_agrees=bool(agree), R=R)


def to_build_frame(Vm, fr, xbow):
    P = Vm @ fr["R"].T
    if fr["flip"]:
        P[:, 0] *= -1
        P[:, 1] *= -1
    P[:, 0] -= P[:, 0].min()
    P[:, 1] -= 0.5 * (P[:, 1].min() + P[:, 1].max())
    P[:, 2] -= P[:, 2].min()
    out = P * SCALE
    out[:, 0] += xbow
    out[:, 2] -= DRAFT
    return out


# ============================================================================
# Slicing
# ============================================================================
class Slicer:
    """Fast plane sections of a welded mesh along one axis.

    section(v) returns, for every face crossing the plane coord[axis] = v, the
    two crossing points D -> U oriented so that outer boundaries run counter-
    clockwise in the (u, w) plane, u, w = the next two axes cyclically (holes
    run clockwise).  Node keys identify the crossed mesh edges, so the
    segments can be chained exactly."""

    def __init__(self, V, F, axis, step):
        self.V, self.F, self.axis, self.step = V, F, axis, step
        self.nv = np.int64(len(V))
        c = V[F][:, :, axis]
        self.lo = c.min(1)
        self.hi = c.max(1)
        self.org = float(self.lo.min()) - step
        b0 = np.floor((self.lo - self.org) / step).astype(np.int64)
        b1 = np.floor((self.hi - self.org) / step).astype(np.int64)
        n = b1 - b0 + 1
        fid = np.repeat(np.arange(len(F)), n)
        off = np.arange(len(fid)) - np.repeat(np.cumsum(n) - n, n)
        bins = b0[fid] + off
        o = np.argsort(bins, kind="stable")
        self.fid = fid[o]
        self.nb = int(bins.max()) + 2
        self.start = np.searchsorted(bins[o], np.arange(self.nb + 1))

    def faces_at(self, v):
        b = int(math.floor((v - self.org) / self.step))
        if b < 0 or b >= self.nb:
            return np.zeros(0, np.int64)
        f = self.fid[self.start[b]:self.start[b + 1]]
        return f[(self.lo[f] <= v) & (self.hi[f] >= v)]

    def section(self, v, faces=None):
        ax = self.axis
        f = self.faces_at(v) if faces is None else faces
        if len(f) == 0:
            return None
        Fi = self.F[f]
        P = self.V[Fi]                       # (k,3,3)
        c = P[:, :, ax] - v
        above = c > 0
        k = above.sum(1)
        keep = (k == 1) | (k == 2)
        if not keep.any():
            return None
        f, Fi, P, c, above = f[keep], Fi[keep], P[keep], c[keep], above[keep]
        n = len(f)
        U = np.zeros((n, 3))
        D = np.zeros((n, 3))
        kU = np.zeros(n, np.int64)
        kD = np.zeros(n, np.int64)
        for i, j in ((0, 1), (1, 2), (2, 0)):
            up = (~above[:, i]) & above[:, j]
            dn = above[:, i] & (~above[:, j])
            m = up | dn
            if not m.any():
                continue
            ci, cj = c[m, i], c[m, j]
            t = ci / (ci - cj)
            pt = P[m, i] + t[:, None] * (P[m, j] - P[m, i])
            a, b = Fi[m, i], Fi[m, j]
            key = np.minimum(a, b) * self.nv + np.maximum(a, b)
            mu, md = up[m], dn[m]
            iu = np.nonzero(m)[0][mu]
            idn = np.nonzero(m)[0][md]
            U[iu] = pt[mu]
            kU[iu] = key[mu]
            D[idn] = pt[md]
            kD[idn] = key[md]
        u_ax, w_ax = (ax + 1) % 3, (ax + 2) % 3
        return dict(f=f, P0=D, P1=U, k0=kD, k1=kU, u=u_ax, w=w_ax)


def section_loops(sec):
    """Group the oriented segments of one section into loops.
    Returns per loop: signed area (+ outer, - hole), centroid (u, w), bbox,
    closed flag, n segments, and the label of each segment."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    k0, k1 = sec["k0"], sec["k1"]
    keys, inv = np.unique(np.r_[k0, k1], return_inverse=True)
    n = len(k0)
    a, b = inv[:n], inv[n:]
    g = coo_matrix((np.ones(n, np.int8), (a, b)), shape=(len(keys), len(keys)))
    nc, lab = connected_components(g, directed=False)
    deg = np.bincount(a, minlength=len(keys)) + np.bincount(b, minlength=len(keys))
    seg_lab = lab[a]
    bad = np.bincount(lab, weights=(deg != 2).astype(float), minlength=nc) > 0
    u, w = sec["u"], sec["w"]
    p0 = sec["P0"][:, [u, w]]
    p1 = sec["P1"][:, [u, w]]
    o = p0.mean(0)
    q0, q1 = p0 - o, p1 - o
    cr = q0[:, 0] * q1[:, 1] - q0[:, 1] * q1[:, 0]
    area = 0.5 * np.bincount(seg_lab, weights=cr, minlength=nc)
    cx = np.bincount(seg_lab, weights=(q0[:, 0] + q1[:, 0]) * cr, minlength=nc)
    cy = np.bincount(seg_lab, weights=(q0[:, 1] + q1[:, 1]) * cr, minlength=nc)
    with np.errstate(divide="ignore", invalid="ignore"):
        cen = np.c_[cx, cy] / (6.0 * area[:, None]) + o
    nseg = np.bincount(seg_lab, minlength=nc)
    umin = np.full(nc, np.inf); umax = np.full(nc, -np.inf)
    wmin = np.full(nc, np.inf); wmax = np.full(nc, -np.inf)
    np.minimum.at(umin, seg_lab, np.minimum(p0[:, 0], p1[:, 0]))
    np.maximum.at(umax, seg_lab, np.maximum(p0[:, 0], p1[:, 0]))
    np.minimum.at(wmin, seg_lab, np.minimum(p0[:, 1], p1[:, 1]))
    np.maximum.at(wmax, seg_lab, np.maximum(p0[:, 1], p1[:, 1]))
    return dict(n=nc, area=area, cen=cen, closed=~bad, nseg=nseg, seg_lab=seg_lab,
                bbox=np.c_[umin, umax, wmin, wmax])


def chain_loop(sec, seg_idx):
    """Order the segments of one closed loop; returns the polyline (m,2) in (u,w)."""
    k0, k1 = sec["k0"][seg_idx], sec["k1"][seg_idx]
    nxt = {int(k): i for i, k in enumerate(k0)}
    p0 = sec["P0"][seg_idx][:, [sec["u"], sec["w"]]]
    out, i, seen = [], 0, 0
    while seen <= len(seg_idx):
        out.append(p0[i])
        j = nxt.get(int(k1[i]))
        seen += 1
        if j is None or j == 0:
            break
        i = j
    return np.array(out)


def envelope(u0, w0, u1, w1, grid, mode="max"):
    """Max (or min) of w over all segments at each grid value of u (exact on the
    polyline); segment end points are also dropped into the nearest grid cell."""
    n = len(grid)
    out = np.full(n, -np.inf if mode == "max" else np.inf)
    if len(u0) == 0:
        return out
    g0, du = grid[0], grid[1] - grid[0]
    a = np.minimum(u0, u1)
    b = np.maximum(u0, u1)
    i0 = np.maximum(np.ceil((a - g0) / du), 0).astype(np.int64)
    i1 = np.minimum(np.floor((b - g0) / du), n - 1).astype(np.int64)
    cnt = np.maximum(i1 - i0 + 1, 0)
    red = np.maximum.at if mode == "max" else np.minimum.at
    tot = int(cnt.sum())
    if tot:
        s = np.repeat(np.arange(len(u0)), cnt)
        gi = i0[s] + (np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt))
        den = u1[s] - u0[s]
        t = np.where(np.abs(den) > 1e-12, (grid[gi] - u0[s]) / np.where(np.abs(den) > 1e-12, den, 1.0), 0.0)
        red(out, gi, w0[s] + t * (w1[s] - w0[s]))
    for uu, ww in ((u0, w0), (u1, w1)):
        gi = np.round((uu - g0) / du).astype(np.int64)
        m = (gi >= 0) & (gi < n)
        red(out, gi[m], ww[m])
    return out


# ============================================================================
# Small numeric helpers
# ============================================================================
def gsmooth(y, sigma_samples):
    from scipy.ndimage import gaussian_filter1d
    return gaussian_filter1d(np.asarray(y, float), sigma_samples, mode="nearest")


def fill_nan(y):
    y = np.asarray(y, float).copy()
    ok = np.isfinite(y)
    if ok.sum() < 2:
        return y
    i = np.arange(len(y))
    y[~ok] = np.interp(i[~ok], i[ok], y[ok])
    return y


def curvature_graph(x, y, sigma_mm):
    """Curvature (1/m) of the graph y(x) sampled on a uniform x grid (mm)."""
    dx = x[1] - x[0]
    ys = gsmooth(y, sigma_mm / dx)
    d1 = np.gradient(ys, dx)
    d2 = np.gradient(d1, dx)
    return d2 / (1 + d1 ** 2) ** 1.5 * 1000.0, ys


def sign_changes(k, thr):
    m = np.abs(k) > thr
    s = np.sign(k[m])
    return int((s[1:] != s[:-1]).sum()), m


def fairness_stats(x, k, thr, lag_mm=50.0):
    nsc, _ = sign_changes(k, thr)
    dx = x[1] - x[0]
    lag = max(1, int(round(lag_mm / dx)))
    jump = np.abs(k[lag:] - k[:-lag]) if len(k) > lag else np.zeros(1)
    j = int(np.argmax(jump))
    return dict(sign_changes=nsc, max_abs_k=float(np.max(np.abs(k))),
                max_jump_50mm=float(jump[j]), max_jump_x=float(x[j] + 0.5 * lag * dx),
                rms_k=float(np.sqrt(np.mean(k ** 2))))


def robust_line(t, v, it=3, cut=6.0, side=None):
    """Fit v = a + b t; drop outliers (|res| > cut, or res < -cut when side='upper')."""
    m = np.isfinite(t) & np.isfinite(v)
    for _ in range(it):
        if m.sum() < 4:
            return None
        A = np.c_[np.ones(m.sum()), t[m]]
        coef, *_ = np.linalg.lstsq(A, v[m], rcond=None)
        r = v - (coef[0] + coef[1] * t)
        if side == "upper":
            m2 = m & (r > -cut)
        else:
            m2 = m & (np.abs(r) < cut)
        if m2.sum() == m.sum():
            break
        m = m2
    if m.sum() < 4:
        return None
    return float(coef[0]), float(coef[1]), int(m.sum())


def pct(a, q):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return float(np.percentile(a, q)) if len(a) else float("nan")


def r1(v, nd=1):
    if v is None:
        return None
    if isinstance(v, (float, np.floating)):
        if not np.isfinite(v):
            return None
        return round(float(v), nd)
    return v


# ============================================================================
# Holes (deck, mast, rudder pins)
# ============================================================================
def find_holes(slicer, levels, region, max_d=220.0, link=30.0):
    """Small closed clockwise loops (holes) in a stack of sections, clustered
    across levels.  region(u, w) -> bool keeps the area of interest."""
    rec = []
    for v in levels:
        sec = slicer.section(v)
        if sec is None:
            continue
        L = section_loops(sec)
        A = L["area"]
        dmax = np.maximum(L["bbox"][:, 1] - L["bbox"][:, 0], L["bbox"][:, 3] - L["bbox"][:, 2])
        m = L["closed"] & (A < 0) & (dmax < max_d) & (L["nseg"] >= 3)
        for i in np.nonzero(m)[0]:
            cu, cw = L["cen"][i]
            if not region(cu, cw):
                continue
            bb = L["bbox"][i]
            rec.append((v, cu, cw, 2 * math.sqrt(-A[i] / math.pi), bb[1] - bb[0], bb[3] - bb[2]))
    if not rec:
        return []
    R = np.array(rec)
    from scipy.spatial import cKDTree
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    pairs = cKDTree(R[:, 1:3]).query_pairs(link, output_type="ndarray")
    g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(R), len(R))) if len(pairs) else \
        coo_matrix((len(R), len(R)))
    nc, lab = connected_components(g, directed=False)
    holes = []
    step = levels[1] - levels[0] if len(levels) > 1 else 1.0
    for c in range(nc):
        r = R[lab == c]
        holes.append(dict(u=float(np.median(r[:, 1])), w=float(np.median(r[:, 2])),
                          d_eq=float(np.median(r[:, 3])), ext_u=float(np.median(r[:, 4])),
                          ext_w=float(np.median(r[:, 5])), v_lo=float(r[:, 0].min() - 0.5 * step),
                          v_hi=float(r[:, 0].max() + 0.5 * step), n_levels=int(len(r))))
    return holes


def design_deck_holes():
    out = []
    for x in STANCHION_X:
        for s in (1, -1):
            out.append(("stanchion", x, s))
    for x in PULPIT_X:
        for s in (1, -1):
            out.append(("pulpit", x, s))
    for x in PUSHPIT_X:
        for s in (1, -1):
            out.append(("pushpit", x, s))
    return out


# ============================================================================
# Stations: deck edge (virtual corner), lower profile, strake
# ============================================================================
def _seg_yz(sec, side):
    return (sec["P0"][:, 1] * side, sec["P0"][:, 2], sec["P1"][:, 1] * side, sec["P1"][:, 2])


def _seg_n(sec, side):
    """Face normal (y, z) of every segment, y mirrored for the port side."""
    n = sec.get("n")
    if n is None:
        return np.ones(len(sec["P0"])), np.ones(len(sec["P0"]))
    return n[:, 1] * side, n[:, 2]


def deck_edge_at(sec, x, side=1):
    """Deck edge of one x-section on one side.

    c = support point (max of y + z/2 in a window above the strake): the sharp
    corner, or a point on the rounding of a rounded edge.  v = virtual corner =
    intersection of a line fitted to the side just below c and a line fitted
    to the deck just inboard of c.  Returns (y_c, z_c, y_v, z_v, ok_v)."""
    y0, z0, y1, z1 = _seg_yz(sec, side)
    ny, nz = _seg_n(sec, side)
    hb, zs, zk = float(hb_meas(x)), float(sheer_meas(x)), float(strake_meas(x))
    P = np.r_[np.c_[y0, z0], np.c_[y1, z1]]
    m = (P[:, 0] > max(hb - 350.0, 0.0)) & (P[:, 1] > zk + 60.0) & (P[:, 1] < zs + 150.0)
    if m.sum() < 3:
        return None
    Q = P[m]
    i = int(np.argmax(Q[:, 0] + 0.5 * Q[:, 1]))
    yc, zc = float(Q[i, 0]), float(Q[i, 1])
    out = [yc, zc, np.nan, np.nan, False]
    keep = (np.maximum(y0, y1) > hb - 350.0)
    # side line y = a + b z, outward-facing faces only
    zlo = max(zk + 55.0, zc - 140.0)
    zg = np.arange(zlo, zc - 35.0, 2.0)
    out_f = keep & (ny > 0.3)
    if len(zg) >= 8:
        ys = envelope(z0[out_f], y0[out_f], z1[out_f], y1[out_f], zg, "max")
        fs = robust_line(zg[np.isfinite(ys)], ys[np.isfinite(ys)], cut=4.0, side="upper")
    else:
        fs = None
    # deck line z = c + d y, up-facing faces only (drops cleat walls and the
    # cavity ceiling under fittings)
    yg = np.arange(yc - 180.0, yc - 45.0, 2.0)
    low = keep & (nz > 0.3) & (np.maximum(z0, z1) < zc + 40.0)
    zd = envelope(y0[low], z0[low], y1[low], z1[low], yg, "max")
    fd = robust_line(yg[np.isfinite(zd)], zd[np.isfinite(zd)], cut=6.0)
    if fs is not None and fd is not None:
        a, b, _ = fs
        c, d, _ = fd
        den = 1.0 - b * d
        if abs(den) > 1e-6:
            yv = (a + b * c) / den
            zv = c + d * yv
            ang = math.degrees(abs(math.atan2(1.0, b) - math.atan(d)))
            if abs(yv - yc) < 40.0 and abs(zv - zc) < 50.0 and ang > 25.0:
                out[2], out[3], out[4] = float(yv), float(zv), True
    return out


def strake_at(sec, x, zc, side=1):
    """Strake bump on the side envelope y(z): centre (half-max), height, proud."""
    y0, z0, y1, z1 = _seg_yz(sec, side)
    ny, nz = _seg_n(sec, side)
    zk = float(strake_meas(x))
    hb = float(hb_meas(x))
    keep = (np.maximum(y0, y1) > max(hb - 500.0, 0.0)) & (ny > -0.2)
    lo = max(zk - 300.0, 60.0)
    hi = min(zk + 160.0, zc - 15.0)
    zg = np.arange(lo, hi, 3.0)
    if len(zg) < 20:
        return None
    ys = envelope(z0[keep], y0[keep], z1[keep], y1[keep], zg, "max")
    ok = np.isfinite(ys)
    base_m = ok & (zg < zk - 75.0) & (zg > zk - 260.0)
    if base_m.sum() < 10:
        return None
    co = np.polyfit(zg[base_m], ys[base_m], 2)
    r = ys - np.polyval(co, zg)
    fit_rms = float(np.sqrt(np.mean(r[base_m] ** 2)))
    win = ok & (np.abs(zg - zk) < 130.0)
    if not win.any():
        return None
    idx = np.nonzero(win)[0]
    i = idx[int(np.argmax(r[idx]))]
    if r[i] < 5.0:
        return None
    # side-view band of the strake: where it stands > 10 % of its projection
    # (> 3 mm) proud of the side; its middle is what the profile drawing shows
    lim = max(3.0, 0.1 * r[i])
    j0 = i
    while j0 > 0 and ok[j0 - 1] and r[j0 - 1] > lim:
        j0 -= 1
    j1 = i
    while j1 < len(zg) - 1 and ok[j1 + 1] and r[j1 + 1] > lim:
        j1 += 1
    za, zb = zg[j0] - 1.5, zg[j1] + 1.5
    # outer-face centre (half maximum), for reference
    h0 = i
    while h0 > 0 and ok[h0 - 1] and r[h0 - 1] > 0.5 * r[i]:
        h0 -= 1
    h1 = i
    while h1 < len(zg) - 1 and ok[h1 + 1] and r[h1 + 1] > 0.5 * r[i]:
        h1 += 1
    return dict(z_center=float(0.5 * (za + zb)), height=float(zb - za), proud=float(r[i]),
                z_bottom=float(za), z_top=float(zb), z_face=float(0.5 * (zg[h0] + zg[h1])),
                fit_rms=fit_rms, reliable=bool(fit_rms < 2.5 and (zb - za) < 2.0 * STRAKE_H))


def station_sweep(slx, xs, fn=None):
    """One x-section per station: deck edge both sides, lowest point, widest."""
    rows = []
    for x in xs:
        sec = slx.section(x)
        if sec is None:
            rows.append(None)
            continue
        pts = np.r_[sec["P0"], sec["P1"]]
        cl = np.abs(pts[:, 1]) < 800.0
        zlow = float(pts[cl, 2].min()) if cl.any() else np.nan
        if fn is not None:
            sec["n"] = fn[sec["f"]]
        d_s = deck_edge_at(sec, x, 1)
        d_p = deck_edge_at(sec, x, -1)
        rows.append(dict(x=float(x), zlow=zlow, ymax=float(np.abs(pts[:, 1]).max()), stb=d_s, port=d_p, sec=sec))
    return rows


def assemble_deck_line(rows):
    """Deck line along x from the station sweep: support point + smoothed
    virtual-corner offset (offsets from stations with a clean fit, outside the
    window recess, interpolated elsewhere)."""
    xs = np.array([r["x"] for r in rows if r is not None and r["stb"] is not None])
    out = {}
    for side in ("stb", "port"):
        X, YC, ZC, DY, DZ = [], [], [], [], []
        for r in rows:
            if r is None or r[side] is None:
                continue
            yc, zc, yv, zv, ok = r[side]
            X.append(r["x"]); YC.append(yc); ZC.append(zc)
            good = ok and not (WIN_X[0] - 60 < r["x"] < WIN_X[1] + 60)
            DY.append(yv - yc if good else np.nan)
            DZ.append(zv - zc if good else np.nan)
        X, YC, ZC, DY, DZ = map(np.array, (X, YC, ZC, DY, DZ))
        nfit = int(np.isfinite(DY).sum())
        dx = np.median(np.diff(X)) if len(X) > 1 else 10.0
        if nfit >= 5:
            DYs = gsmooth(fill_nan(DY), 100.0 / dx)
            DZs = gsmooth(fill_nan(DZ), 100.0 / dx)
        else:
            DYs = np.zeros_like(YC)
            DZs = np.zeros_like(ZC)
        out[side] = dict(x=X, yc=YC, zc=ZC, y=YC + DYs, z=ZC + DZs, dy=DYs, dz=DZs, n_fit=nfit)
    return out


def transom_top(sly, ys, zmin_of_x):
    """Plan outline aft: for planes y = const the aftmost point above the strake."""
    out = []
    for y in ys:
        sec = sly.section(y)
        if sec is None:
            continue
        P = np.r_[sec["P0"], sec["P1"]]
        m = (P[:, 0] > 7000.0) & (P[:, 2] > zmin_of_x(P[:, 0]))
        if m.any():
            j = int(np.argmax(np.where(m, P[:, 0], -np.inf)))
            out.append((float(P[j, 0]), float(y), float(P[j, 2])))
    return np.array(out)


def poly_dist(px, py, qx, qy):
    """Distance of points (px,py) to the polyline (qx,qy) and the closest index."""
    ax, ay = qx[:-1], qy[:-1]
    bx, by = qx[1:], qy[1:]
    dx, dy = bx - ax, by - ay
    L2 = np.maximum(dx * dx + dy * dy, 1e-12)
    t = np.clip(((px[:, None] - ax) * dx + (py[:, None] - ay) * dy) / L2, 0, 1)
    cx = ax + t * dx
    cy = ay + t * dy
    d = np.hypot(px[:, None] - cx, py[:, None] - cy)
    j = np.argmin(d, axis=1)
    r = np.arange(len(px))
    return d[r, j], cx[r, j], cy[r, j]


def err_stats(e, x=None):
    e = np.asarray(e, float)
    ok = np.isfinite(e)
    if not ok.any():
        return dict(n=0)
    ea = np.abs(e[ok])
    j = int(np.argmax(ea))
    out = dict(n=int(ok.sum()), max_abs=r1(ea[j]), rms=r1(math.sqrt(float(np.mean(e[ok] ** 2)))),
               mean=r1(float(np.mean(e[ok]))), within_tol=int((ea <= LINE_TOL).sum()))
    if x is not None:
        out["x_at_max"] = r1(float(np.asarray(x, float)[ok][j]), 0)
    return out


# ============================================================================
# Fairness
# ============================================================================
WL_LEVELS = (150.0, 400.0, 700.0, 900.0)
WL_RANGE = (600.0, 7400.0)
SECTION_X = (1400.0, 2050.0, 2700.0, 3350.0, 4000.0, 4650.0, 5300.0, 5950.0, 6600.0, 7250.0)


def _runs(mask):
    """Contiguous True runs -> list of (i0, i1) inclusive."""
    m = np.r_[False, mask, False].astype(int)
    d = np.diff(m)
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0] - 1))


def waterline(slz, z, fn, dx=5.0):
    sec = slz.section(z)
    xg = np.arange(0.0, 8000.0, dx)
    if sec is None:
        return xg, np.full(len(xg), np.nan), np.full(len(xg), np.nan)
    n = fn[sec["f"]]
    out = {}
    for side in (1, -1):
        m = n[:, 1] * side > -0.2
        y = envelope(sec["P0"][m, 0], sec["P0"][m, 1] * side, sec["P1"][m, 0], sec["P1"][m, 1] * side, xg, "max")
        y[~np.isfinite(y)] = np.nan
        y[y <= 0] = np.nan
        out[side] = y
    return xg, out[1], out[-1]


SHAPE_SIGMA, FINE_SIGMA = 60.0, 25.0


def _two_scale(x, y, thr_shape, thr_fine):
    """Curvature statistics of y(x) at the shape scale and the facet scale."""
    dx = x[1] - x[0]
    out = {}
    for tag, sig, thr in (("shape", SHAPE_SIGMA, thr_shape), ("fine", FINE_SIGMA, thr_fine)):
        k, _ = curvature_graph(x, y, sig)
        c = int(round(2 * sig / dx))
        if len(k) <= 2 * c + 10:
            return None
        k2, x2 = k[c:-c], x[c:-c]
        st = fairness_stats(x2, k2, thr)
        out[tag] = (st, x2, k2, k)
    c = int(round(2 * SHAPE_SIGMA / dx))
    rip = out["fine"][3][c:-c] - out["shape"][3][c:-c]
    out["ripple_rms"] = float(np.sqrt(np.mean(rip ** 2)))
    out["ripple_n"] = len(rip)
    return out


def waterline_fairness(slz, fn):
    res = {}
    traces = {}
    for z in WL_LEVELS:
        xg, ys, yp = waterline(slz, z, fn)
        valid = np.isfinite(ys) & (xg >= WL_RANGE[0]) & (xg <= WL_RANGE[1])
        zk = strake_meas(xg)
        valid &= ~((z > zk - 47.5 - 45.0) & (z < zk + 47.5 + 30.0))         # strake band
        valid &= ~((xg > WIN_X[0] - 50) & (xg < WIN_X[1] + 50) & (z > zk + 40.0))   # window recess
        sc_s = sc_f = 0
        jumps, wig, ks, xs2, rips = [], [], [], [], []
        cover = 0.0
        for i0, i1 in _runs(valid):
            if i1 - i0 < 80:          # < 400 mm piece: too short to judge
                continue
            x = xg[i0:i1 + 1]
            y = ys[i0:i1 + 1]
            two = _two_scale(x, y, 0.02, 0.05)
            if two is None:
                continue
            sc_s += two["shape"][0]["sign_changes"]
            sc_f += two["fine"][0]["sign_changes"]
            rips.append((two["ripple_rms"], two["ripple_n"]))
            jumps.append((two["fine"][0]["max_jump_50mm"], two["fine"][0]["max_jump_x"]))
            low = gsmooth(y, 187.0 / 5.0)
            hp = y - low
            c = int(round(2 * SHAPE_SIGMA / 5.0))
            inmid = (x >= 1500) & (x <= 6800)
            inmid[:c] = False
            inmid[-c:] = False
            if inmid.any():
                wig.append((float(np.max(np.abs(hp[inmid]))), float(np.sqrt(np.mean(hp[inmid] ** 2)))))
            ks.append(two["shape"][2])
            xs2.append(two["shape"][1])
            cover += x[-1] - x[0]
        asym = np.nanmax(np.abs(ys - yp)[valid]) if valid.any() else np.nan
        j = max(jumps) if jumps else (np.nan, np.nan)
        res[f"z{int(z)}"] = dict(
            sign_changes=sc_s, sign_changes_fine=sc_f,
            ripple_rms=r1(float(np.sqrt(sum(r * r * n for r, n in rips) / max(sum(n for _, n in rips), 1))), 4) if rips else None,
            max_jump_50mm=r1(j[0], 3), max_jump_x=r1(j[1], 0),
            wiggle_lt1m_max=r1(max(w[0] for w in wig), 2) if wig else None,
            wiggle_lt1m_rms=r1(float(np.sqrt(np.mean([w[1] ** 2 for w in wig]))), 2) if wig else None,
            covered_mm=r1(cover, 0), port_stb_max_diff=r1(asym, 1))
        traces[z] = (np.concatenate(xs2) if xs2 else np.zeros(0), np.concatenate(ks) if ks else np.zeros(0), xg, ys)
    return res, traces


def deckline_fairness(D):
    st = D["stb"]
    m = (st["x"] >= 300) & (st["x"] <= 7600)
    x = st["x"][m]
    out = {}
    tr = {}
    for key, v, ts, tf in (("plan", st["y"][m], 0.02, 0.05), ("profile", st["z"][m], 0.005, 0.01)):
        xg = np.arange(x[0], x[-1], 10.0)
        yg = np.interp(xg, x, v)
        two = _two_scale(xg, yg, ts, tf)
        low = gsmooth(yg, 187.0 / 10.0)
        hp = yg - low
        mid = (xg >= 1500) & (xg <= 6800)
        sh, fi = two["shape"][0], two["fine"][0]
        out[key] = dict(sign_changes=sh["sign_changes"], sign_changes_fine=fi["sign_changes"],
                        ripple_rms=r1(two["ripple_rms"], 4),
                        thresholds_per_m=[ts, tf], max_jump_50mm=r1(fi["max_jump_50mm"], 3),
                        max_jump_x=r1(fi["max_jump_x"], 0), max_abs_k=r1(fi["max_abs_k"], 3),
                        wiggle_lt1m_max=r1(float(np.max(np.abs(hp[mid]))), 2),
                        wiggle_lt1m_rms=r1(float(np.sqrt(np.mean(hp[mid] ** 2))), 2))
        tr[key] = (two["shape"][1], two["shape"][2])
    return out, tr


def outer_loop(sec):
    L = section_loops(sec)
    if L["n"] == 0:
        return None
    i = int(np.argmax(np.where(L["closed"], L["area"], -np.inf)))
    if L["area"][i] <= 0:
        return None
    idx = np.nonzero(L["seg_lab"] == i)[0]
    return chain_loop(sec, idx)


def section_fairness(slx):
    rows = []
    curves = {}
    for x in SECTION_X:
        sec = slx.section(x)
        if sec is None:
            continue
        loop = outer_loop(sec)
        if loop is None or len(loop) < 10:
            continue
        y, z = loop[:, 0], loop[:, 1]
        zk = float(strake_meas(x))
        z0 = max(float(bottom_meas(x)) + 40.0, -450.0)
        z1 = zk - 100.0
        m = (y > 15.0) & (z >= z0) & (z <= z1)
        runs = _runs(m)
        if not runs:
            continue
        i0, i1 = max(runs, key=lambda r: r[1] - r[0])
        P = loop[i0:i1 + 1]
        if P[-1, 1] < P[0, 1]:
            P = P[::-1]
        d = np.hypot(*np.diff(P, axis=0).T)
        s = np.r_[0, np.cumsum(d)]
        keep = np.r_[True, d > 1e-9]
        P, s = P[keep], s[keep]
        if s[-1] < 200:
            continue
        sg = np.arange(0, s[-1], 2.0)
        yy = np.interp(sg, s, P[:, 0])
        zz = np.interp(sg, s, P[:, 1])
        # curvature (1/m), smoothing 15 mm along the curve
        ys_, zs_ = gsmooth(yy, 7.5), gsmooth(zz, 7.5)
        th = np.unwrap(np.arctan2(np.gradient(zs_), np.gradient(ys_)))
        k = np.gradient(th, 2.0) * 1000.0
        c = 8
        k2, z2 = k[c:-c], zz[c:-c]
        nsc, _ = sign_changes(k2, 0.1)
        # side angle from vertical (deg), light smoothing 5 mm
        y5, z5 = gsmooth(yy, 2.5), gsmooth(zz, 2.5)
        ang = np.degrees(np.arctan2(np.gradient(y5), np.gradient(z5)))
        below = (z5 > -60) & (z5 < -5)
        above = (z5 > 5) & (z5 < 60)
        crease = float(np.mean(ang[below]) - np.mean(ang[above])) if below.any() and above.any() else np.nan
        # how much of the turn sits in the DWL band compared with its neighbours
        band = (z5 > -60) & (z5 < 60)
        nb = ((z5 > -240) & (z5 < -60)) | ((z5 > 60) & (z5 < 240))
        conc = float(np.mean(np.abs(k[band])) / max(np.mean(np.abs(k[nb])), 1e-6)) if band.any() and nb.any() else np.nan
        rows.append(dict(x=x, sign_changes=nsc, dwl_crease_deg=r1(crease, 1), dwl_turn_concentration=r1(conc, 2),
                         angle_below_deg=r1(float(np.mean(ang[below])), 1) if below.any() else None,
                         angle_above_deg=r1(float(np.mean(ang[above])), 1) if above.any() else None,
                         max_abs_k=r1(float(np.max(np.abs(k2))), 2), z_from=r1(float(z2[0]), 0), z_to=r1(float(z2[-1]), 0)))
        curves[x] = (z2, k2, yy, zz)
    return rows, curves


# ============================================================================
# Exterior skin vs cavities
# ============================================================================
def split_exterior(V, F, cen, vholes, hholes):
    """Label the exterior skin.  Deck holes may break into the hollow, which
    joins a cavity to the outside; removing the hole walls first separates them
    again.  vholes: vertical holes (x, y, r, z_lo, z_hi); hholes: horizontal
    x-axis holes (y, z, r, x_lo, x_hi).  Returns ext mask (faces), hole-wall
    mask and the number of cavities that were open to the outside."""
    wall = np.zeros(len(F), bool)
    for (hx, hy, r, zl, zh) in vholes:
        d = np.hypot(cen[:, 0] - hx, cen[:, 1] - hy)
        wall |= (d < r + 3.0) & (cen[:, 2] > zl - 400.0) & (cen[:, 2] < zh + 30.0)
    for (hy, hz, r, xl, xh) in hholes:
        d = np.hypot(cen[:, 1] - hy, cen[:, 2] - hz)
        wall |= (d < r + 3.0) & (cen[:, 0] > xl - 100.0) & (cen[:, 0] < xh + 30.0)
    keep = np.nonzero(~wall)[0]
    nv = int(F.max()) + 1
    nc0, lab0 = components(F, nv)
    nc, lab = components(F[keep], nv)
    # exterior = component holding the outermost face (max |y|, then max z)
    j = int(np.argmax(np.abs(cen[keep, 1]) + 1e-3 * cen[keep, 2]))
    ext = np.zeros(len(F), bool)
    ext[keep[lab == lab[j]]] = True
    vol = signed_volume(V, F)
    cav0 = int((np.bincount(lab0, weights=vol, minlength=nc0) < 0).sum())
    sub = np.bincount(lab, weights=vol[keep], minlength=nc)
    cav1 = int(((sub < -1e3) & (np.arange(nc) != lab[j])).sum())
    return ext, wall, dict(shells_raw=int(nc0), cavities_closed_raw=cav0,
                           cavities_after_removing_hole_walls=cav1,
                           cavities_open_through_holes=int(max(cav1 - cav0, 0)))


# ============================================================================
# Mesh quality on the hull skin
# ============================================================================
def hull_skin_mask(cen, fn, ext):
    x, y, z = cen[:, 0], cen[:, 1], cen[:, 2]
    zk = strake_meas(x)
    m = ext.copy()
    m &= np.abs(y) > 25.0                                   # centreline seam / stem edge
    m &= ~((x < 750.0) & (np.abs(y) < 120.0) & (z > 600.0))  # anchor-roller block
    m &= (x > 150.0) & (x < transom_x(z, y) - 100.0)
    m &= z < sheer_meas(x) - 60.0
    m &= ~((np.abs(y) < 300.0) & (z < bottom_meas(x) + 120.0) & (x > 3300.0) & (x < 5950.0))
    m &= ~((z > zk - 107.5) & (z < zk + 77.5))
    m &= ~((x > WIN_X[0] - 50) & (x < WIN_X[1] + 50) & (z > zk + 40.0))
    m &= (fn[:, 1] * np.sign(y) > 0.05) | (fn[:, 2] < -0.5)
    return m


def deck_mask(cen, fn, ext):
    x, y, z = cen[:, 0], cen[:, 1], cen[:, 2]
    zs = sheer_meas(x)
    return ext & (fn[:, 2] > 0.9) & (z > zs - 20.0) & (z < zs + DECK_CAMBER + 15.0) & (x > 700) & (x < 7400) \
        & (np.abs(y) < hb_meas(x) - 90.0)


def mesh_quality(topo, fn, aspect, lmax, skin):
    f1, f2 = topo["f1"], topo["f2"]
    both = skin[f1] & skin[f2]
    cosang = np.clip(np.einsum("ij,ij->i", fn[f1[both]], fn[f2[both]]), -1, 1)
    ang = np.degrees(np.arccos(cosang))
    return dict(skin_triangles=int(skin.sum()), skin_edges=int(both.sum()),
                dihedral_gt5_pct=r1(100.0 * float(np.mean(ang > 5.0)), 2),
                dihedral_gt10_pct=r1(100.0 * float(np.mean(ang > 10.0)), 2),
                dihedral_gt2_pct=r1(100.0 * float(np.mean(ang > 2.0)), 2),
                dihedral_p50_deg=r1(pct(ang, 50), 2), dihedral_p90_deg=r1(pct(ang, 90), 2),
                dihedral_p99_deg=r1(pct(ang, 99), 2),
                sliver_gt20_pct_skin=r1(100.0 * float(np.mean(aspect[skin] > 20.0)), 2),
                sliver_gt20_pct_all=r1(100.0 * float(np.mean(aspect > 20.0)), 2),
                edge_p50_model=r1(pct(lmax[skin], 50) / SCALE, 3), edge_p95_model=r1(pct(lmax[skin], 95) / SCALE, 3),
                edge_max_model=r1(float(lmax[skin].max()) / SCALE if skin.any() else np.nan, 2)), ang


# ============================================================================
# Wall thickness by ray casting
# ============================================================================
def ray_cast(V, F, O, Dd, L, h, chunk=3000, bounds=None):
    """Nearest hit of each ray O + t Dd, t in (1e-3, L] (uniform grid).
    Returns (t, face) with t = inf / face = -1 where nothing is hit."""
    lo = np.minimum(O.min(0), (O + L * Dd).min(0)) - h
    hi = np.maximum(O.max(0), (O + L * Dd).max(0)) + h
    if bounds is None:
        T = V[F]
        bounds = (T.min(1), T.max(1))
    tmin = bounds[0] - 0.5 * h
    tmax = bounds[1] + 0.5 * h
    sel = np.nonzero(np.all(tmax >= lo, 1) & np.all(tmin <= hi, 1))[0]
    dims = np.ceil((hi - lo) / h).astype(np.int64) + 1
    c0 = np.clip(np.floor((tmin[sel] - lo) / h).astype(np.int64), 0, dims - 1)
    c1 = np.clip(np.floor((tmax[sel] - lo) / h).astype(np.int64), 0, dims - 1)
    ext = c1 - c0 + 1
    cnt = ext.prod(1)
    fidx = np.repeat(np.arange(len(sel)), cnt)
    loc = np.arange(len(fidx)) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    e = ext[fidx]
    iz = loc % e[:, 2]
    iy = (loc // e[:, 2]) % e[:, 1]
    ix = loc // (e[:, 2] * e[:, 1])
    key = ((c0[fidx, 0] + ix) * dims[1] + (c0[fidx, 1] + iy)) * dims[2] + (c0[fidx, 2] + iz)
    o = np.argsort(key, kind="stable")
    key, cell_f = key[o], sel[fidx[o]]
    ukey, ustart = np.unique(key, return_index=True)
    uend = np.r_[ustart[1:], len(key)]
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    E1, E2 = B - A, C - A
    best = np.full(len(O), np.inf)
    bestf = np.full(len(O), -1, np.int64)
    ts = np.arange(0.0, L + 1e-9, 0.5 * h)
    for r0 in range(0, len(O), chunk):
        oo, dd = O[r0:r0 + chunk], Dd[r0:r0 + chunk]
        nr = len(oo)
        pts = oo[:, None, :] + ts[None, :, None] * dd[:, None, :]
        ci = np.clip(np.floor((pts - lo) / h).astype(np.int64), 0, dims - 1)
        k = (ci[..., 0] * dims[1] + ci[..., 1]) * dims[2] + ci[..., 2]
        rid = np.repeat(np.arange(nr), len(ts))
        k = k.ravel()
        pair = np.unique(rid * (dims.prod() + 1) + k)
        rid, k = pair // (dims.prod() + 1), pair % (dims.prod() + 1)
        pos = np.searchsorted(ukey, k)
        pos = np.clip(pos, 0, len(ukey) - 1)
        hit = ukey[pos] == k
        rid, pos = rid[hit], pos[hit]
        n_in = uend[pos] - ustart[pos]
        rr = np.repeat(rid, n_in)
        off = np.arange(int(n_in.sum())) - np.repeat(np.cumsum(n_in) - n_in, n_in)
        ff = cell_f[np.repeat(ustart[pos], n_in) + off]
        pr = np.unique(rr.astype(np.int64) * len(F) + ff)
        rr, ff = pr // len(F), pr % len(F)
        # Moeller-Trumbore
        d = dd[rr]
        p = np.cross(d, E2[ff])
        det = np.einsum("ij,ij->i", E1[ff], p)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = oo[rr] - A[ff]
        u = np.einsum("ij,ij->i", tv, p) * inv
        q = np.cross(tv, E1[ff])
        v = np.einsum("ij,ij->i", d, q) * inv
        t = np.einsum("ij,ij->i", E2[ff], q) * inv
        good = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-3) & (t <= L)
        rg, tg, fg = rr[good], t[good], ff[good]
        o = np.lexsort((tg, rg))
        rg, tg, fg = rg[o], tg[o], fg[o]
        first = np.r_[True, rg[1:] != rg[:-1]]
        best[r0 + rg[first]] = tg[first]
        bestf[r0 + rg[first]] = fg[first]
    return best, bestf


def wall_thickness(V, F, fn, area, cen, skin, deck, n_rays, L=300.0, h=30.0, seed=1):
    rng = np.random.default_rng(seed)
    out = {}
    pts_all = []
    T = V[F]
    fb = (T.min(1), T.max(1))
    del T
    for name, m in (("hull_side", skin & (np.abs(cen[:, 1]) > 80.0)), ("deck", deck)):
        idx = np.nonzero(m)[0]
        if len(idx) == 0:
            out[name] = dict(n=0)
            continue
        w = area[idx] / area[idx].sum()
        n = max(200, int(n_rays * (0.75 if name == "hull_side" else 0.25)))
        fsel = idx[rng.choice(len(idx), size=3 * n, p=w)]
        a, b = rng.random(3 * n), rng.random(3 * n)
        flip = a + b > 1
        a[flip], b[flip] = 1 - a[flip], 1 - b[flip]
        P = V[F[fsel, 0]] + a[:, None] * (V[F[fsel, 1]] - V[F[fsel, 0]]) + b[:, None] * (V[F[fsel, 2]] - V[F[fsel, 0]])
        # the region test again on the sample point itself (long faces reach out of it)
        if name == "hull_side":
            pm = hull_skin_mask(P, fn[fsel], np.ones(len(P), bool)) & (np.abs(P[:, 1]) > 80.0)
        else:
            pm = deck_mask(P, fn[fsel], np.ones(len(P), bool))
        sel = np.nonzero(pm)[0][:n]
        fsel, P = fsel[sel], P[sel]
        n = len(sel)
        d = -fn[fsel]
        O = P + 0.05 * d
        # rays in x-slabs: small grids, bounded memory on big meshes
        t = np.full(n, np.inf)
        fh = np.full(n, -1, np.int64)
        for part in np.array_split(np.argsort(O[:, 0]), max(1, n // 2500)):
            if len(part):
                t[part], fh[part] = ray_cast(V, F, O[part], d[part], L, h, bounds=fb)
        t = t + 0.05
        # a proper exit leaves through a face that roughly faces the ray; a
        # grazing first hit means the sample sat on a sharp edge -> ignored
        graze = np.zeros(n, bool)
        hit = fh >= 0
        graze[hit] = np.einsum("ij,ij->i", fn[fh[hit]], d[hit]) < 0.3
        tm = np.where(graze, np.nan, t / SCALE)
        fin = np.isfinite(tm)
        order = np.argsort(np.where(fin, tm, np.inf))[:8]
        out[name] = dict(n=int(n), solid_or_gt_L_pct=r1(100.0 * float(np.mean(~fin & ~graze)), 1),
                         edge_samples_pct=r1(100.0 * float(np.mean(graze)), 1),
                         min_model=r1(float(np.min(tm[fin])), 3) if fin.any() else None,
                         p01_model=r1(pct(tm[fin], 0.1), 3), p1_model=r1(pct(tm[fin], 1), 3),
                         p5_model=r1(pct(tm[fin], 5), 3), p50_model=r1(pct(tm[fin], 50), 3),
                         thinnest=[dict(x=r1(P[i, 0], 0), y=r1(P[i, 1], 0), z=r1(P[i, 2], 0), t_model=r1(tm[i], 3))
                                   for i in order if np.isfinite(tm[i])])
        pts_all.append((name, P, tm))
    return out, pts_all


# Today's hull: measured by this script on baseline_fine.stl (10.11.2026).
# V10 must keep these (CLAUDE.md: rorhull, masthull og rekkehull blir der de er).
TODAY_HOLES = {
    # name: (x, y, d_eq, z_top, z_bottom_closed), full-scale mm, from baseline_fine.stl
    "deck": {
        "stanchion_1450_stb": (1450.0, 568.6, 36.0, 1202.9, 997.9),
        "stanchion_1450_port": (1450.0, -568.6, 36.0, 1202.9, 997.9),
        "stanchion_2500_stb": (2500.0, 887.1, 36.0, 1177.9, 967.9),
        "stanchion_2500_port": (2500.0, -887.1, 36.0, 1177.9, 967.9),
        "stanchion_3550_stb": (3550.0, 1135.4, 36.0, 1132.9, 972.9),
        "stanchion_3550_port": (3550.0, -1135.4, 36.0, 1132.9, 972.9),
        "stanchion_4600_stb": (4600.0, 1261.6, 36.0, 1107.9, 992.9),
        "stanchion_4600_port": (4600.0, -1261.6, 36.0, 1107.9, 992.9),
        "stanchion_5650_stb": (5650.0, 1226.4, 36.0, 1087.9, 877.9),
        "stanchion_5650_port": (5650.0, -1226.4, 36.0, 1087.9, 877.9),
        "stanchion_6700_stb": (6700.0, 1061.5, 36.0, 1067.9, 1017.9),
        "stanchion_6700_port": (6700.0, -1061.5, 36.0, 1067.9, 1017.9),
        "pulpit_520_stb": (520.0, 241.2, 36.0, 1207.9, 1037.9),
        "pulpit_520_port": (520.0, -241.2, 36.0, 1207.9, 1037.9),
        "pulpit_900_stb": (900.0, 379.8, 36.0, 1207.9, 1002.9),
        "pulpit_900_port": (900.0, -379.8, 36.0, 1207.9, 1002.9),
        "pushpit_7250_stb": (7250.0, 931.8, 36.0, 1032.9, 982.9),
        "pushpit_7250_port": (7250.0, -931.8, 36.0, 1032.9, 982.9),
        "pushpit_7680_stb": (7680.0, 825.2, 36.0, 977.9, 772.9),
        "pushpit_7680_port": (7680.0, -825.2, 36.0, 977.9, 772.9),
    },
    # (x, y, size_x, size_y, z_top, z_bottom)
    "mast": (3400.0, -0.0, 135.0, 105.0, 1377.9, 1047.9),
    # z_design: (y, z, d_eq, x_bottom, x_mouth)
    "pins": {
        "-90": (-0.0, -90.0, 42.0, 7730.9, 7790.9),
        "-200": (-0.0, -200.0, 42.0, 7715.9, 7772.9),
    },
}


# ============================================================================
# Interfaces
# ============================================================================
def classify_holes(vholes, pins):
    """Match detected holes to the design list.  Coordinates already in the
    final build frame."""
    today = TODAY_HOLES or {}
    tdeck = today.get("deck", {})
    round_h = [h for h in vholes if 20.0 < h["d_eq"] < 70.0 and h["n_levels"] >= 3
               and 0.75 < h["ext_u"] / max(h["ext_w"], 1e-6) < 1.33 and abs(h["w"]) > 100.0]
    used = set()
    rows = []
    for kind, xd, side in design_deck_holes():
        name = f"{kind}_{int(xd)}_{'stb' if side > 0 else 'port'}"
        ref = tdeck.get(name)
        best, bd = None, 1e9
        for i, h in enumerate(round_h):
            if i in used or np.sign(h["w"]) != side:
                continue
            d = abs(h["u"] - xd) + (abs(h["w"] - ref[1]) if ref else 0.0)
            if d < bd:
                best, bd = i, d
        if best is None or abs(round_h[best]["u"] - xd) > 150.0:
            rows.append(dict(name=name, found=False))
            continue
        used.add(best)
        h = round_h[best]
        r = dict(name=name, found=True, x=r1(h["u"]), y=r1(h["w"]), d=r1(h["d_eq"]),
                 z_top=r1(h["v_hi"]), z_bottom_closed=r1(h["v_lo"]), closed_depth=r1(h["v_hi"] - h["v_lo"]),
                 dx_design=r1(h["u"] - xd))
        if ref:
            r.update(dx_today=r1(h["u"] - ref[0]), dy_today=r1(h["w"] - ref[1]), dd_today=r1(h["d_eq"] - ref[2]),
                     dz_top_today=r1(h["v_hi"] - ref[3]))
        rows.append(r)
    extras = [dict(x=r1(h["u"]), y=r1(h["w"]), d=r1(h["d_eq"])) for i, h in enumerate(round_h) if i not in used]
    others = [dict(x=r1(h["u"]), y=r1(h["w"]), d_eq=r1(h["d_eq"]), ext=[r1(h["ext_u"]), r1(h["ext_w"])],
                   z=[r1(h["v_lo"]), r1(h["v_hi"])]) for h in vholes
              if h["n_levels"] >= 3 and h not in round_h and not (abs(h["w"]) < 60 and h["d_eq"] > 60)]
    found = [r for r in rows if r["found"]]
    out = dict(expected=len(rows), found=len(found), missing=[r["name"] for r in rows if not r["found"]],
               extra_round_holes=extras, other_small_pockets=others, holes=rows)
    if found:
        out["max_abs_dx_design"] = r1(max(abs(r["dx_design"]) for r in found))
        if any("dx_today" in r for r in found):
            out["max_pos_change_vs_today"] = r1(max(math.hypot(r.get("dx_today", 0), r.get("dy_today", 0)) for r in found))
            out["max_d_change_vs_today"] = r1(max(abs(r.get("dd_today", 0)) for r in found), 2)
        out["min_closed_depth"] = r1(min(r["closed_depth"] for r in found))
        out["holes_shorter_than_design"] = [r["name"] for r in found if r["closed_depth"] < DECK_HOLE_DEPTH - 20.0]
    # mast
    mc = [h for h in vholes if abs(h["w"]) < 60.0 and h["d_eq"] > 60.0 and h["n_levels"] >= 3]
    if mc:
        h = min(mc, key=lambda h: abs(h["u"] - MAST_STEP_X))
        m = dict(found=True, x=r1(h["u"]), y=r1(h["w"]), size_x=r1(h["ext_u"]), size_y=r1(h["ext_w"]),
                 z_top=r1(h["v_hi"]), z_bottom=r1(h["v_lo"]), depth=r1(h["v_hi"] - h["v_lo"]),
                 dsize_design=[r1(h["ext_u"] - MAST_HOLE_XY[0]), r1(h["ext_w"] - MAST_HOLE_XY[1])])
        tm = today.get("mast")
        if tm:
            m.update(dx_today=r1(h["u"] - tm[0]), dy_today=r1(h["w"] - tm[1]), dz_top_today=r1(h["v_hi"] - tm[4]),
                     ddepth_today=r1((h["v_hi"] - h["v_lo"]) - (tm[4] - tm[5])))
    else:
        m = dict(found=False)
    # rudder pins
    prow = []
    for zd in RUDDER_PIN_Z:
        c = [h for h in pins if abs(h["u"]) < 40.0 and abs(h["w"] - zd) < 60.0 and h["n_levels"] >= 3]
        if not c:
            prow.append(dict(z_design=zd, found=False))
            continue
        h = min(c, key=lambda h: abs(h["w"] - zd))
        r = dict(z_design=zd, found=True, y=r1(h["u"]), z=r1(h["w"]), d=r1(h["d_eq"]), x_bottom=r1(h["v_lo"]),
                 x_mouth=r1(h["v_hi"]), depth=r1(h["v_hi"] - h["v_lo"]), dz=r1(h["w"] - zd))
        tp = (today.get("pins") or {}).get(str(int(zd)))
        if tp:
            r.update(dy_today=r1(h["u"] - tp[0]), dz_today=r1(h["w"] - tp[1]), dx_bottom_today=r1(h["v_lo"] - tp[3]),
                     ddepth_today=r1((h["v_hi"] - h["v_lo"]) - (tp[4] - tp[3])))
        prow.append(r)
    pf = [p for p in prow if p["found"]]
    pins_out = dict(expected=2, found=len(pf), pins=prow)
    if pf:
        pins_out["draft_from_pins"] = r1(DRAFT + float(np.mean([p["dz"] for p in pf])))
    return dict(deck_holes=out, mast_hole=m, rudder_pins=pins_out)


# ============================================================================
# Analysis driver
# ============================================================================
def analyze(path, args):
    t0 = time.time()
    res = dict(meta=dict(stl=os.path.abspath(path), name=args.name, script=os.path.abspath(__file__),
                         version=VERSION, run_at=_dt.datetime.now().isoformat(timespec="seconds")))
    T, kind = load_stl(path)
    res["meta"]["stl_format"] = kind
    fsize = os.path.getsize(path)
    # ---- topology (model mm) ------------------------------------------------
    Vm, F = weld(T, 1e-5)
    if signed_volume(Vm, F).sum() < 0:          # inside-out file: flip, and say so
        F = F[:, ::-1].copy()
        res["meta"]["normals_flipped_on_load"] = True
    nvq, Fq = weld(T, 1e-4)
    topo_q = edge_topology(Fq, len(nvq))
    topo = edge_topology(F, len(Vm))
    degen = int(((F[:, 0] == F[:, 1]) | (F[:, 1] == F[:, 2]) | (F[:, 0] == F[:, 2])).sum())
    log(f"  loaded {len(T)} triangles, {len(Vm)} vertices  ({time.time() - t0:.1f}s)")
    # ---- frame ----------------------------------------------------------------
    fr = detect_frame(Vm, args.frame)
    V = to_build_frame(Vm, fr, args.xbow)
    fn, area, cen, aspect, lmax = face_geom(V, F)
    # ---- holes in the provisional frame (bow tip = xbow) ----------------------
    slz = Slicer(V, F, 2, 10.0)
    vholes = find_holes(slz, np.arange(600.0, 1600.0, 5.0) + 0.37, lambda u, w: True)
    vholes = [h for h in vholes if h["n_levels"] >= 2]
    mastc = [h for h in vholes if abs(h["w"]) < 60.0 and h["d_eq"] > 60.0 and h["n_levels"] >= 3
             and abs(h["u"] - MAST_STEP_X) < 400.0]
    shift = 0.0
    anchor = "bow"
    if args.anchor in ("auto", "mast") and mastc:
        hm = min(mastc, key=lambda h: abs(h["u"] - MAST_STEP_X))
        shift = MAST_STEP_X - hm["u"]
        anchor = "mast"
    elif args.anchor == "mast":
        log("  WARNING: no mast hole found, anchoring on the bow tip")
    if shift:
        V[:, 0] += shift
        cen[:, 0] += shift
        slz = Slicer(V, F, 2, 10.0)
        for h in vholes:
            h["u"] += shift
    res["meta"].update(frame=fr["frame"], rotation_deg=fr["rot_deg"], pca_deg=r1(fr["pca_deg"], 3),
                       flipped_180=fr["flip"], bow_check_agrees=fr["bow_check_agrees"], x_anchor=anchor,
                       bow_tip_x=r1(float(V[:, 0].min()), 2), x_shift_vs_bow_anchor=r1(shift, 2),
                       dwl_model_z=r1(DRAFT / SCALE, 3))
    slx = Slicer(V, F, 0, 10.0)
    pins = find_holes(slx, np.arange(7600.0, 7900.0, 3.0) + 0.37, lambda u, w: abs(u) < 300.0 and w < 0.0)
    log(f"  frame {fr['frame']} rot {fr['rot_deg']:.2f} anchor {anchor} shift {shift:+.2f}; "
        f"{len(vholes)} vertical + {len(pins)} pin holes  ({time.time() - t0:.1f}s)")
    # ---- exterior skin --------------------------------------------------------
    vh = [(h["u"], h["w"], 0.5 * max(h["ext_u"], h["ext_w"]), h["v_lo"], h["v_hi"]) for h in vholes
          if h["n_levels"] >= 3]
    hh = [(h["u"], h["w"], 0.5 * max(h["ext_u"], h["ext_w"]), h["v_lo"], h["v_hi"]) for h in pins]
    ext, wallf, cav = split_exterior(V, F, cen, vh, hh)
    skin = hull_skin_mask(cen, fn, ext)
    deck = deck_mask(cen, fn, ext)
    mq, dih = mesh_quality(topo, fn, aspect, lmax, skin)
    res["mesh"] = dict(triangles=int(len(T)), file_mb=r1(fsize / 1e6, 2), vertices=int(len(Vm)),
                       degenerate_triangles=int((area < 1e-10).sum()), **mq,
                       note="skin = hull topsides and bottom outside the strake band, keel root, window recess, "
                            "anchor roller and ends; dihedral = angle between adjacent face normals")
    # ---- shell ------------------------------------------------------------------
    vol = signed_volume(V, F) / SCALE ** 3 / 1000.0       # model cm3
    ncomp, lab = components(F, len(Vm))
    cv = np.bincount(lab, weights=vol, minlength=ncomp)
    res["shell"] = dict(
        closed_manifold=bool(topo["n_nonmanifold"] == 0 and topo["n_flipped"] == 0 and degen == 0),
        nonmanifold_edges=topo["n_nonmanifold"], boundary_edges=topo["n_boundary"],
        inconsistent_orientation_edges=topo["n_flipped"],
        meshcheck_tol1e4_nonmanifold_edges=topo_q["n_nonmanifold"],
        meshcheck_note="tools/meshcheck.py welds at 1e-4 mm; edges it calls non-manifold while the 1e-5 weld "
                       "is clean come from vertices < 0.1 um apart (harmless, but meshcheck exits 1)",
        shells=int(ncomp), material_cm3_model=r1(float(vol.sum()), 2),
        outer_enclosed_cm3_model=r1(float(cv.max()), 2), voids_cm3_model=r1(float(cv[cv < 0].sum()), 2),
        **cav)
    log(f"  mesh + shell  ({time.time() - t0:.1f}s)")
    # ---- interfaces ---------------------------------------------------------------
    res["interfaces"] = classify_holes(vholes, pins)
    # ---- stations: deck edge, profile, strake --------------------------------------
    xs = np.arange(20.0, 7900.0, 10.0)
    rows = station_sweep(slx, xs, fn)
    D = assemble_deck_line(rows)
    st = D["stb"]
    # plan outline: side part + transom top from y-planes
    sly = Slicer(V, F, 1, 10.0)
    zthr = lambda x: strake_meas(x) + 80.0
    tt = transom_top(sly, np.arange(0.0, 700.0, 10.0) + 0.37, zthr)
    m_side = st["x"] <= 7850.0
    qx = np.r_[st["x"][m_side], tt[::-1, 0] if len(tt) else []]
    qy = np.r_[st["y"][m_side], tt[::-1, 1] if len(tt) else []]
    # order the transom part from the corner to the centreline
    if len(tt):
        cut = tt[:, 1] < st["y"][m_side][-1]
        tpart = tt[cut][np.argsort(-tt[cut][:, 1])]
        qx = np.r_[st["x"][m_side], tpart[:, 0]]
        qy = np.r_[st["y"][m_side], tpart[:, 1]]
    lines = {}
    mx = (_DHB[:, 0] >= 60.0) & (_DHB[:, 0] < 7300.0)
    d1, _, _ = poly_dist(_DHB[mx, 0], _DHB[mx, 1], qx, qy)
    s1 = np.sign(np.interp(_DHB[mx, 0], st["x"], st["y"]) - _DHB[mx, 1])
    d2, _, _ = poly_dist(_SO[:, 0], _SO[:, 1], qx, qy)
    # sign for the stern points: inside the model outline = negative
    inside = _SO[:, 1] < np.interp(_SO[:, 0], qx[:len(st["x"][m_side])], qy[:len(st["x"][m_side])])
    s2 = np.where(inside, 1.0, -1.0)
    e_all = np.r_[d1 * s1, d2 * s2]
    x_all = np.r_[_DHB[mx, 0], _SO[:, 0]]
    lines["deck_outline"] = dict(**err_stats(e_all, x_all), trace_x_lt_7300=err_stats(d1 * s1, _DHB[mx, 0]),
                                 stern_outline=err_stats(d2 * s2, _SO[:, 0]),
                                 virtual_corner_fits=int(st["n_fit"]),
                                 port_minus_stb_max=r1(float(np.max(np.abs(np.interp(st["x"], D["port"]["x"], D["port"]["y"]) - st["y"]))), 2),
                                 sign="+ = model outside the drawing")
    # sheer at the table points
    xz = np.clip(_DEZ[:, 0], 80.0, 7850.0)
    keepz = _DEZ[:, 0] < 7900.0
    ez = np.interp(xz, st["x"], st["z"]) - _DEZ[:, 1]
    lines["sheer"] = dict(**err_stats(ez[keepz], _DEZ[keepz, 0]),
                          points=[[r1(a, 0), r1(b, 1)] for a, b in zip(_DEZ[keepz, 0], ez[keepz])],
                          sign="+ = model above the drawing", note="x=0 evaluated at x=80; x=7950 skipped (transom)")
    # strake
    srows = []
    for xk, _, zk, _ in HULL_STATIONS:
        if not 750.0 <= xk <= 7650.0:
            continue
        sec = slx.section(float(xk))
        if sec is None:
            continue
        sec["n"] = fn[sec["f"]]
        zc = float(np.interp(xk, st["x"], st["zc"]))
        sk = strake_at(sec, float(xk), zc, 1)
        if sk is None:
            srows.append((xk, np.nan, np.nan, False, np.nan, np.nan))
        else:
            srows.append((xk, sk["z_center"] - zk, sk["z_face"] - zk, sk["reliable"], sk["height"], sk["proud"]))
    sr = np.array(srows, float) if srows else np.zeros((0, 6))
    rel = sr[:, 3] > 0.5 if len(sr) else np.zeros(0, bool)
    lines["strake_height"] = dict(**err_stats(sr[rel, 1], sr[rel, 0]),
                                  stations=int(len(sr)), reliable=int(rel.sum()),
                                  outer_face_centre=err_stats(sr[rel, 2], sr[rel, 0]),
                                  band_height_median=r1(float(np.nanmedian(sr[rel, 4])), 1) if rel.any() else None,
                                  proud_median=r1(float(np.nanmedian(sr[rel, 5])), 1) if rel.any() else None,
                                  note="centre of the strake band seen from the side vs strake_z_mm (x 750-7650)")
    # LOA, beam, draft
    xbow = float(V[:, 0].min())
    above = V[:, 2] > strake_meas(V[:, 0]) + 80.0
    xst = float(V[above, 0].max())
    loa = xst - xbow
    beam_deck = 2.0 * float(max(st["y"].max(), D["port"]["y"].max()))
    beam_all = float(V[:, 1].max() - V[:, 1].min())
    draft = res["interfaces"]["rudder_pins"].get("draft_from_pins")
    lines["loa"] = dict(value=r1(loa), target=LOA, dev=r1(loa - LOA), x_bow=r1(xbow), x_transom_top=r1(xst),
                        overall_x_extent=r1(float(V[:, 0].max() - xbow)),
                        note="stem head to transom top on the centreline; overall extent includes the strake")
    lines["beam"] = dict(deck=r1(beam_deck), target=BEAM, dev=r1(beam_deck - BEAM), overall=r1(beam_all),
                         x_at_max=r1(float(st["x"][int(np.argmax(st["y"]))]), 0))
    lines["draft"] = dict(assumed=DRAFT, from_rudder_pins=draft,
                          dev=r1(draft - DRAFT) if draft is not None else None,
                          note="keel bottom is z=0 in the STL; the pins (built at z=-90/-200) check it")
    # underwater profile
    zl = np.array([r["zlow"] if r is not None else np.nan for r in rows])
    xl = np.array([r["x"] if r is not None else np.nan for r in rows])
    okl = np.isfinite(zl)
    seg = {}
    uw_dev = np.full(len(_UW), np.nan)
    for name, a, b in UW_SEGMENTS:
        m = (_UW[:, 0] >= a) & (_UW[:, 0] <= b)
        dd, cx, cz = poly_dist(_UW[m, 0], -_UW[m, 1], xl[okl], zl[okl])
        sgn = np.sign(np.interp(_UW[m, 0], xl[okl], zl[okl]) + _UW[m, 1])
        uw_dev[m] = dd * np.where(sgn == 0, 1, sgn)
        seg[name] = err_stats(uw_dev[m], _UW[m, 0])
    lines["underwater_profile"] = dict(segments=seg, sign="+ = model above (shallower than) the drawing",
                                       note="2-D distance from the traced lower silhouette; propeller (6030-6450) "
                                            "and rudder (>7450) are not part of the hull and are skipped")
    res["lines"] = lines
    log(f"  lines  ({time.time() - t0:.1f}s)")
    # ---- fairness -----------------------------------------------------------------
    wl, wtr = waterline_fairness(slz, fn)
    dl, dtr = deckline_fairness(D)
    sf, scv = section_fairness(slx)
    cre = [r["dwl_crease_deg"] for r in sf if r["dwl_crease_deg"] is not None]
    res["fairness"] = dict(
        waterlines=wl, deck_edge=dl, sections=sf,
        sections_total_sign_changes=int(sum(r["sign_changes"] for r in sf)),
        dwl_crease_max_deg=r1(max(cre), 1) if cre else None,
        dwl_crease_mean_deg=r1(float(np.mean(cre)), 1) if cre else None,
        note="sign changes count curvature reversals with |k| above the threshold (1/m) after Gaussian "
             "smoothing (shape: sigma 60 mm, fine: 25 mm along waterlines; 15 mm along sections). "
             "max_jump_50mm = largest change of curvature over 50 mm (1/m). wiggle = deviation from a "
             "1 m low-pass, x 1500-6800 (mm).")
    log(f"  fairness  ({time.time() - t0:.1f}s)")
    # ---- wall thickness ------------------------------------------------------------
    wt, tpts = wall_thickness(V, F, fn, area, cen, skin, deck, args.rays)
    res["shell"]["wall_thickness"] = wt
    res["shell"]["wall_nominal_model"] = dict(hull_side=1.9, deck=1.6, note="HULL_WALL 1.5 + VOID_MARGIN 0.4; DECK_THICK 1.6")
    # thinnest spots next to deck holes
    holes_xy = [(r["name"], r["x"], r["y"]) for r in res["interfaces"]["deck_holes"]["holes"] if r.get("found")]
    for spot in wt.get("hull_side", {}).get("thinnest", []):
        if holes_xy:
            nm, hx, hy = min(holes_xy, key=lambda h: math.hypot(h[1] - spot["x"], h[2] - spot["y"]))
            dd = math.hypot(hx - spot["x"], hy - spot["y"])
            spot["nearest_hole"] = nm if dd < 120 else None
    log(f"  wall thickness  ({time.time() - t0:.1f}s)")
    ctx = dict(V=V, F=F, fn=fn, ext=ext, D=D, rows=rows, wtr=wtr, dtr=dtr, scv=scv, tpts=tpts,
               uw=(xl[okl], zl[okl], uw_dev), lab=lab, sr=sr, ez=(_DEZ[keepz, 0], ez[keepz]),
               ed=(x_all, e_all), skin=skin, dih=dih)
    res["meta"]["analysis_s"] = r1(time.time() - t0, 1)
    return res, ctx


# ============================================================================
# Summary table
# ============================================================================
def dget(d, path):
    for k in path.split("."):
        if d is None:
            return None
        if isinstance(d, list):
            try:
                d = d[int(k)]
            except (ValueError, IndexError):
                return None
        else:
            d = d.get(k)
    return d


def _derived(res):
    wl = dget(res, "fairness.waterlines") or {}
    pins = [p for p in (dget(res, "interfaces.rudder_pins.pins") or []) if p.get("found")]
    return {
        "wl_sign_changes": sum(v.get("sign_changes", 0) for v in wl.values()) if wl else None,
        "wl_sign_changes_fine": sum(v.get("sign_changes_fine", 0) for v in wl.values()) if wl else None,
        "wl_max_jump": max((v.get("max_jump_50mm") or 0) for v in wl.values()) if wl else None,
        "wl_ripple": r1(float(np.sqrt(np.mean([(v.get("ripple_rms") or 0) ** 2 for v in wl.values()]))), 4) if wl else None,
        "wl_wiggle": max((v.get("wiggle_lt1m_max") or 0) for v in wl.values()) if wl else None,
        "pin_dz": max(abs(p["dz"]) for p in pins) if pins else None,
        "deck_sc": (dget(res, "fairness.deck_edge.plan.sign_changes") or 0)
        + (dget(res, "fairness.deck_edge.profile.sign_changes") or 0),
    }


# (label, getter, unit, rule) - rule: ("band", target, tol) | ("max", lim) | ("min", lim) | ("eq", v) | ("true",)
# requirement rows are V10 musts (CLAUDE.md); target rows are quality aims; None = indicator only
SUMMARY_ROWS = [
    ("REQUIREMENTS", None, None, None),
    ("LOA (stem head to transom top)", "lines.loa.value", "mm", ("band", LOA, LOA * DIM_TOL)),
    ("Beam at the deck line", "lines.beam.deck", "mm", ("band", BEAM, BEAM * DIM_TOL)),
    ("Draft (checked via rudder pins)", "lines.draft.from_rudder_pins", "mm", ("band", DRAFT, DRAFT * DIM_TOL)),
    ("Deck outline: max dev", "lines.deck_outline.max_abs", "mm", ("max", LINE_TOL)),
    ("Sheer: max dev at DECK_EDGE_Z pts", "lines.sheer.max_abs", "mm", ("max", LINE_TOL)),
    ("Strake height: max dev (x 750-7650)", "lines.strake_height.max_abs", "mm", ("max", LINE_TOL)),
    ("Deck holes found (stanchion/pulpit)", "interfaces.deck_holes.found", "", ("eq", 20)),
    ("Deck holes moved vs today (max)", "interfaces.deck_holes.max_pos_change_vs_today", "mm", ("max", 15.0)),
    ("Mast hole found / moved y", "interfaces.mast_hole.dy_today", "mm", ("max", 15.0)),
    ("Rudder pin holes found", "interfaces.rudder_pins.found", "", ("eq", 2)),
    ("Rudder pin z error (max)", "_d.pin_dz", "mm", ("max", 5.0)),
    ("Closed manifold (1e-5 weld)", "shell.closed_manifold", "", ("true",)),
    ("Min wall, hull side (model)", "shell.wall_thickness.hull_side.min_model", "mm", ("min", 0.8)),
    ("Min wall, deck (model)", "shell.wall_thickness.deck.min_model", "mm", ("min", 0.8)),
    ("LINES (indicators)", None, None, None),
    ("Deck outline rms", "lines.deck_outline.rms", "mm", None),
    ("Sheer rms", "lines.sheer.rms", "mm", None),
    ("Strake height rms", "lines.strake_height.rms", "mm", None),
    ("UW profile canoe body fwd: max", "lines.underwater_profile.segments.canoe_fwd.max_abs", "mm", None),
    ("UW profile keel LE: max", "lines.underwater_profile.segments.keel_le.max_abs", "mm", None),
    ("UW profile keel bottom: max", "lines.underwater_profile.segments.keel_bottom.max_abs", "mm", None),
    ("UW aft of keel: max", "lines.underwater_profile.segments.canoe_aft_of_keel.max_abs", "mm", None),
    ("SMOOTHNESS (lower is better)", None, None, None),
    ("Dihedral > 5 deg, hull skin", "mesh.dihedral_gt5_pct", "%", ("max", 2.0)),
    ("Dihedral > 10 deg, hull skin", "mesh.dihedral_gt10_pct", "%", ("max", 0.5)),
    ("Slivers (aspect > 20), hull skin", "mesh.sliver_gt20_pct_skin", "%", ("max", 10.0)),
    ("Waterline inflections, shape (4 WL)", "_d.wl_sign_changes", "", None),
    ("Waterline ripple (k25 - k60 rms)", "_d.wl_ripple", "1/m", None),
    ("Waterline max curvature jump", "_d.wl_max_jump", "1/m", None),
    ("Waterline wiggle < 1 m (max)", "_d.wl_wiggle", "mm", None),
    ("Deck edge inflections plan+profile", "_d.deck_sc", "", None),
    ("Section inflections (10 stations)", "fairness.sections_total_sign_changes", "", None),
    ("DWL crease, max over stations", "fairness.dwl_crease_max_deg", "deg", None),
    ("DWL crease, mean", "fairness.dwl_crease_mean_deg", "deg", None),
    ("FILE", None, None, None),
    ("Triangles", "mesh.triangles", "", None),
    ("File size", "mesh.file_mb", "MB", None),
    ("Material volume (model)", "shell.material_cm3_model", "cm3", None),
    ("Wall p1, hull side (model)", "shell.wall_thickness.hull_side.p1_model", "mm", None),
]


def _val(res, path):
    if path.startswith("_d."):
        return _derived(res).get(path[3:])
    return dget(res, path)


def _rule_text(rule):
    if rule is None:
        return ""
    k = rule[0]
    if k == "band":
        return f"{rule[1]:g} +-{rule[2]:.0f}"
    if k == "max":
        return f"<= {rule[1]:g}"
    if k == "min":
        return f">= {rule[1]:g}"
    if k == "eq":
        return f"= {rule[1]}"
    return "yes"


def _check(v, rule):
    if rule is None:
        return "-"
    if v is None:
        return "n/a"
    k = rule[0]
    if k == "band":
        ok = abs(v - rule[1]) <= rule[2]
    elif k == "max":
        ok = abs(v) <= rule[1]
    elif k == "min":
        ok = v >= rule[1]
    elif k == "eq":
        ok = v == rule[1]
    else:
        ok = bool(v)
    return "PASS" if ok else "FAIL"


def summarize(res, ref):
    table = []
    head = []
    for label, path, unit, rule in SUMMARY_ROWS:
        if path is None:
            table.append([label])
            continue
        v = _val(res, path)
        rv = _val(ref, path) if ref else None
        st = _check(v, rule)
        delta = None
        if isinstance(v, (int, float)) and isinstance(rv, (int, float)) and not isinstance(v, bool):
            delta = r1(float(v) - float(rv), 2)
        if label.startswith("Mast hole"):
            mf = dget(res, "interfaces.mast_hole.found")
            st = "FAIL" if not mf else ("PASS" if v is None or abs(v) <= 15.0 else "FAIL")
        table.append([label, v, unit, _rule_text(rule), st, rv, delta])
        head.append(dict(label=label, value=v, unit=unit, rule=_rule_text(rule), status=st, ref=rv, delta=delta))
    req_fail = [h["label"] for h in head if h["status"] == "FAIL" and h["label"] in
                [r[0] for r in SUMMARY_ROWS[1:SUMMARY_ROWS.index(("LINES (indicators)", None, None, None))]]]
    return dict(table=table, rows=head, requirements_failed=req_fail,
                requirements_ok=not req_fail)


# ============================================================================
# Rendering: z-buffer rasterizer, Bambu-Studio-like flat shading
# ============================================================================
class Cam:
    """Pinhole (f in px) or orthographic (scale px/mm) camera.  R rows are the
    camera axes in world coordinates: right, down, forward."""

    def __init__(self, C, R, W, H, f=None, scale=None, cx=None, cy=None):
        self.C, self.R, self.W, self.H = np.asarray(C, float), np.asarray(R, float), int(W), int(H)
        self.f, self.scale = f, scale
        self.cx = W / 2.0 if cx is None else cx
        self.cy = H / 2.0 if cy is None else cy

    @property
    def ortho(self):
        return self.scale is not None

    def project(self, P):
        Q = (P - self.C) @ self.R.T
        if self.ortho:
            return Q[:, 0] * self.scale + self.cx, Q[:, 1] * self.scale + self.cy, Q[:, 2]
        z = np.maximum(Q[:, 2], 1e-6)
        return self.f * Q[:, 0] / z + self.cx, self.f * Q[:, 1] / z + self.cy, Q[:, 2]

    def scaled(self, k):
        return Cam(self.C, self.R, round(self.W * k), round(self.H * k), None if self.f is None else self.f * k,
                   None if self.scale is None else self.scale * k, self.cx * k, self.cy * k)


def look_rot(fwd, up=(0, 0, 1)):
    f = np.asarray(fwd, float)
    f = f / np.linalg.norm(f)
    r = np.cross(f, up)
    if np.linalg.norm(r) < 1e-9:
        r = np.cross(f, (0, 1, 0))
    r /= np.linalg.norm(r)
    d = np.cross(f, r)
    return np.array([r, d, f])


def rot_from_euler(yaw, pitch, roll=0.0):
    """Camera looking along yaw (deg from +x towards +y), pitched down by
    pitch (deg), rolled by roll (deg, clockwise in the image)."""
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    R = look_rot(np.array([cy * cp, sy * cp, -sp]))
    if roll:
        a = math.radians(roll)
        r, d = R[0].copy(), R[1].copy()
        R = np.array([math.cos(a) * r + math.sin(a) * d, -math.sin(a) * r + math.cos(a) * d, R[2]])
    return R


RASTER_CHUNK = 1_500_000        # pixel tests per batch (memory ~ 100 MB)


def raster(cam, V, F, cull=True):
    """Face id per pixel (-1 = background) and depth."""
    W, H = cam.W, cam.H
    u, v, z = cam.project(V)
    good_v = (z > 1.0) if not cam.ortho else np.ones(len(V), bool)
    U, Vv, Z = u[F], v[F], z[F]
    ok = good_v[F].all(1)
    if cull:
        ar = (U[:, 1] - U[:, 0]) * (Vv[:, 2] - Vv[:, 0]) - (U[:, 2] - U[:, 0]) * (Vv[:, 1] - Vv[:, 0])
        ok &= ar < 0          # front faces (outward normal to the camera) have negative area, y down
    x0 = np.maximum(np.ceil(U.min(1) - 0.5).astype(np.int64), 0)
    x1 = np.minimum(np.floor(U.max(1) - 0.5).astype(np.int64), W - 1)
    y0 = np.maximum(np.ceil(Vv.min(1) - 0.5).astype(np.int64), 0)
    y1 = np.minimum(np.floor(Vv.max(1) - 0.5).astype(np.int64), H - 1)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    ok &= (bw > 0) & (bh > 0)
    U0, U1, U2 = U[:, 0], U[:, 1], U[:, 2]
    V0, V1, V2 = Vv[:, 0], Vv[:, 1], Vv[:, 2]
    den = (V1 - V2) * (U0 - U2) + (U2 - U1) * (V0 - V2)
    ok &= np.abs(den) > 1e-12
    depth = np.full(W * H, np.inf)
    fid = np.full(W * H, -1, np.int64)
    done = ~ok
    P_, Z_, F_ = [], [], []
    for b in (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 8192):
        sel = np.nonzero(~done & (bw <= b) & (bh <= b))[0]
        if len(sel) == 0:
            continue
        done[sel] = True
        bx = int(bw[sel].max())
        by = int(bh[sel].max())
        n = bx * by
        ox = np.arange(n) % bx
        oy = np.arange(n) // bx
        chunk = max(1, int(RASTER_CHUNK // n))
        for c0 in range(0, len(sel), chunk):
            s_ = sel[c0:c0 + chunk]
            gx = x0[s_][:, None] + ox[None, :]
            gy = y0[s_][:, None] + oy[None, :]
            px, py = gx + 0.5, gy + 0.5
            u2, v2, dd = U2[s_][:, None], V2[s_][:, None], den[s_][:, None]
            l0 = ((V1[s_][:, None] - v2) * (px - u2) + (u2 - U1[s_][:, None]) * (py - v2)) / dd
            l1 = ((v2 - V0[s_][:, None]) * (px - u2) + (U0[s_][:, None] - u2) * (py - v2)) / dd
            l2 = 1.0 - l0 - l1
            ins = (l0 >= -1e-7) & (l1 >= -1e-7) & (l2 >= -1e-7) & (gx <= x1[s_][:, None]) & (gy <= y1[s_][:, None])
            ti, kk = np.nonzero(ins)
            if len(ti) == 0:
                continue
            zz = l0[ti, kk] * Z[s_[ti], 0] + l1[ti, kk] * Z[s_[ti], 1] + l2[ti, kk] * Z[s_[ti], 2]
            P_.append(gy[ti, kk] * W + gx[ti, kk])
            Z_.append(zz)
            F_.append(s_[ti])
    if P_:
        pix = np.concatenate(P_)
        zz = np.concatenate(Z_)
        ff = np.concatenate(F_)
        np.minimum.at(depth, pix, zz)
        win = zz <= depth[pix]
        fid[pix[win]] = ff[win]
    return fid.reshape(H, W), depth.reshape(H, W)


# PrusaSlicer / Bambu Studio "gouraud" shader constants (eye space: y up, z to the viewer)
_L_TOP = np.array([-0.4574957, 0.4574957, 0.7624929])
_L_FRONT = np.array([0.6985074, 0.1397015, 0.6985074])
_IC = 0.6
MODEL_RGB = (0.84, 0.85, 0.83)       # light grey "white filament"
BG_RGB = (236, 238, 241)


def shade(cam, fid, fn, color=MODEL_RGB, bg=BG_RGB):
    H, W = fid.shape
    img = np.empty((H, W, 3), np.float64)
    img[:] = bg
    m = fid >= 0
    n = fn[fid[m]] @ cam.R.T                  # camera frame: x right, y down, z forward
    ne = np.c_[n[:, 0], -n[:, 1], -n[:, 2]]   # eye frame
    ne[ne[:, 2] < 0] *= -1
    nt = np.clip(ne @ _L_TOP, 0, None)
    nf = np.clip(ne @ _L_FRONT, 0, None)
    inten = 0.3 + 0.8 * _IC * nt + 0.3 * _IC * nf
    refl = 2 * (ne @ _L_TOP)[:, None] * ne - _L_TOP
    spec = 0.125 * _IC * np.clip(refl[:, 2], 0, None) ** 20
    col = np.asarray(color)[None, :] * inten[:, None] + spec[:, None]
    img[m] = np.clip(col * 255.0, 0, 255)
    return img.astype(np.uint8)


def fit_cam(V, R, W, H, persp_dist=None, margin=0.05, center=None):
    """Camera with rotation R framing the vertices V."""
    P = V[:: max(1, len(V) // 60000)]
    c = 0.5 * (P.min(0) + P.max(0)) if center is None else np.asarray(center, float)
    if persp_dist is None:
        cam = Cam(c - 1e5 * R[2], R, W, H, scale=1.0, cx=0.0, cy=0.0)
        u, v, _ = cam.project(P)
        sc = min(W * (1 - 2 * margin) / np.ptp(u), H * (1 - 2 * margin) / np.ptp(v))
        cam.scale = sc
        cam.cx = W / 2.0 - sc * 0.5 * (u.min() + u.max())
        cam.cy = H / 2.0 - sc * 0.5 * (v.min() + v.max())
        return cam
    cam = Cam(c - persp_dist * R[2], R, W, H, f=1.0, cx=0.0, cy=0.0)
    u, v, _ = cam.project(P)
    f = min(W * (1 - 2 * margin) / np.ptp(u), H * (1 - 2 * margin) / np.ptp(v))
    cam.f = f
    cam.cx = W / 2.0 - f * 0.5 * (u.min() + u.max())
    cam.cy = H / 2.0 - f * 0.5 * (v.min() + v.max())
    return cam


# name, camera yaw (deg; 0 = looking aft along +x), pitch down (deg), distance (mm, None = ortho)
FIXED_VIEWS = [
    ("3/4 bow, starboard", 180.0 + 145.0, 22.0, 17000.0),
    ("3/4 stern, port", 145.0, 22.0, 17000.0),
    ("side, port (ortho)", 90.0, 0.0, None),
    ("astern", 180.0, 5.0, 22000.0),
    ("bow head-on", 0.0, 5.0, 22000.0),
    ("top (ortho)", None, None, None),
]


def view_cam(spec, V, W, H):
    name, yaw, pitch, dist = spec
    if yaw is None:
        R = np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]])      # plan: bow left, starboard up
    else:
        R = rot_from_euler(yaw, pitch)
    return fit_cam(V, R, W, H, persp_dist=dist)


def render_view(cam, V, F, fn, ss=2):
    from PIL import Image
    c2 = cam.scaled(ss)
    fid, _ = raster(c2, V, F)
    im = Image.fromarray(shade(c2, fid, fn))
    mask = Image.fromarray(((fid >= 0) * 255).astype(np.uint8))
    if ss > 1:
        im = im.resize((cam.W, cam.H), Image.LANCZOS)
        mask = mask.resize((cam.W, cam.H), Image.BILINEAR)
    return im, np.asarray(mask) > 127


# Photo-matched cameras, solved once (dev/fit_onland.py, dev/fit9370.py) on
# today's hull: camera centre (x, y, z) in the build frame (full-scale mm),
# yaw / pitch / roll (deg, see rot_from_euler), focal length f (px of the
# EXIF-rotated photo, principal point = image centre) and the crop shown.
# iPhone shots: f fixed at 1490 px (12 Pro wide camera, 4:3 frame resized to
# 2000 px) and the camera solved by matching ~22 traced hull-outline points;
# IMG_9370 (DSLR, unknown lens): f free, 6 landmarks (stem head, transom
# corner, window ends, mast foot and head).  fit_px = residual rms in photo px.
PHOTO_VIEWS = [
    dict(file="IMG_9388.jpeg", title="bow head-on, on land", C=(-39.9, 0.0, -40.1), yaw=-3.11, pitch=5.55,
         roll=0.24, f=1490.0, crop=(60, 0, 1440, 1450), fit_px=22),
    dict(file="IMG_9391.jpeg", title="transom from astern, on land", C=(9893.5, 0.0, -355.2), yaw=174.14,
         pitch=5.74, roll=-3.38, f=1490.0, crop=(0, 0, 1500, 1650), fit_px=20),
    dict(file="IMG_9370.jpeg", title="side afloat, port (DSLR, ~10 m)", C=(1142.5, -9941.2, 2555.0), yaw=77.17,
         pitch=-15.56, roll=0.86, f=990.0, crop=(60, 1060, 1038, 1420), fit_px=8),
    dict(file="IMG_9389.jpeg", title="3/4 from the starboard bow, low", C=(1202.9, 1570.5, -523.5), yaw=-30.0,
         pitch=2.62, roll=-3.55, f=1563.4, crop=(100, 0, 2000, 1100), fit_px=20),
]


def _font(sz, bold=False):
    from PIL import ImageFont
    for f in (("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
              "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def _fit_into(im, w, h, bg=(255, 255, 255)):
    from PIL import Image
    k = min(w / im.size[0], h / im.size[1])
    im2 = im.resize((max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k))), Image.LANCZOS)
    out = Image.new("RGB", (w, h), bg)
    out.paste(im2, ((w - im2.size[0]) // 2, (h - im2.size[1]) // 2))
    return out


def photo_pair(pv, V, F, fn, photo_dir, box_w, box_h):
    """Photo crop with the model silhouette in cyan | model rendered with the
    same camera.  Returns a PIL image box_w x box_h or None if the photo is
    missing."""
    from PIL import Image, ImageOps, ImageDraw
    path = os.path.join(photo_dir, pv["file"])
    if not os.path.exists(path):
        return None
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = pv["crop"]
    stacked = (x1 - x0) / (y1 - y0) > 1.35          # wide crops: photo above the model
    if stacked:
        k = min(box_w / (x1 - x0), (box_h - 26) / 2.0 / (y1 - y0))
    else:
        k = min((box_w - 6) / 2.0 / (x1 - x0), (box_h - 22) / (y1 - y0))
    cw, ch = round((x1 - x0) * k), round((y1 - y0) * k)
    R = rot_from_euler(pv["yaw"], pv["pitch"], pv["roll"])
    cam = Cam(pv["C"], R, cw, ch, f=pv["f"] * k, cx=(W / 2.0 - x0) * k, cy=(H / 2.0 - y0) * k)
    rend, mask = render_view(cam, V, F, fn, ss=2)
    ph = im.crop((x0, y0, x1, y1)).resize((cw, ch), Image.LANCZOS)
    a = np.asarray(ph).copy()
    from scipy import ndimage as ndi
    edge = mask & ~ndi.binary_erosion(mask, iterations=1)
    edge = ndi.binary_dilation(edge, iterations=1)
    a[edge] = (0, 230, 255)
    out = Image.new("RGB", (box_w, box_h), (255, 255, 255))
    if stacked:
        out.paste(Image.fromarray(a), ((box_w - cw) // 2, 20))
        out.paste(rend, ((box_w - cw) // 2, 24 + ch))
    else:
        out.paste(Image.fromarray(a), (0, 20))
        out.paste(rend, (cw + 6, 20))
    d = ImageDraw.Draw(out)
    d.text((2, 2), f"{pv['file'][:8]}  {pv['title']}: photo + model outline (cyan), model with the same "
                   f"camera (fit ~{pv.get('fit_px', '?')} px)", fill=(20, 20, 20), font=_font(13))
    return out


def plots_image(res, ctx, width=1600, height=760):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    import io
    plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.grid": True, "grid.alpha": 0.3})
    fig, ax = plt.subplots(2, 3, figsize=(width / 100, height / 100), dpi=100)
    # (a) lines
    a = ax[0, 0]
    D = ctx["D"]["stb"]
    a.axhspan(-LINE_TOL, LINE_TOL, color="#d8ecd8", zorder=0)
    xe, ee = ctx["ed"]
    a.plot(xe, ee, ".-", color="#1f77b4", ms=3, lw=0.8, label="deck outline (plan dist.)")
    m = (D["x"] > 60) & (D["x"] < 7850)
    a.plot(D["x"][m], D["z"][m] - sheer_meas(D["x"][m]), "-", color="#ff7f0e", lw=0.8, label="sheer - DECK_EDGE_Z")
    xs, es = ctx["ez"]
    a.plot(xs, es, "o", color="#ff7f0e", ms=3)
    sr = ctx["sr"]
    if len(sr):
        ok = sr[:, 3] > 0.5
        a.plot(sr[ok, 0], sr[ok, 1], "s", color="#2ca02c", ms=3, label="strake band centre - strake_z")
    a.set_xlim(0, 8000)
    a.set_ylim(-30, 30)
    a.set_title("Measured lines: model minus drawing (mm, full scale); band = +-12.5")
    a.legend(loc="lower left", fontsize=7)
    # (b) underwater profile
    a = ax[0, 1]
    xl, zl, _ = ctx["uw"]
    a.plot(_UW[:, 0], -_UW[:, 1], "-", color="#d62728", lw=1.2, label="uw_station.csv (trace)")
    a.plot(xl, zl, "-", color="#1f77b4", lw=1.0, label="model lowest point")
    for nm, x0, x1 in UW_SEGMENTS:
        a.axvspan(x0, x1, color="#eeeeee" if "uncertain" in nm else "#f6f6ff", zorder=0)
    a.set_xlim(800, 8000)
    a.set_ylim(-1500, 200)
    a.set_aspect("equal")
    seg = res["lines"]["underwater_profile"]["segments"]
    short = dict(canoe_fwd="canoe fwd", keel_le="keel LE", keel_bottom="keel bottom",
                 canoe_aft_of_keel="aft of keel", aft_trace_uncertain="aft (trace?)")
    a.set_title("Underwater profile vs uw_station.csv; max 2-D dev (mm):\n" + ", ".join(
        f"{short.get(k, k)} {v.get('max_abs')}" for k, v in seg.items() if v.get("n")), fontsize=8)
    a.legend(loc="lower left", fontsize=7)
    # (c) waterline curvature
    a = ax[0, 2]
    off = 0.0
    for z, (xk, kk, xg, ys) in ctx["wtr"].items():
        if len(xk):
            br = np.r_[0, np.nonzero(np.diff(xk) > 20)[0] + 1, len(xk)]
            for i0, i1 in zip(br[:-1], br[1:]):
                a.plot(xk[i0:i1], kk[i0:i1] + off, lw=0.8, color=plt.cm.viridis(off / 3.0 + 0.05))
        st = res["fairness"]["waterlines"].get(f"z{int(z)}", {})
        a.text(7450, off + 0.15, f"z+{int(z)}: {st.get('sign_changes')} infl.", fontsize=7)
        a.axhline(off, color="k", lw=0.4)
        off += 1.0
    a.set_xlim(500, 8000)
    a.set_ylim(-0.8, off - 0.2)
    a.set_title("Waterline plan curvature (1/m, sigma 60 mm), offset by 1 per waterline")
    # (d) deck edge curvature
    a = ax[1, 0]
    xp, kp = ctx["dtr"]["plan"]
    xz, kz = ctx["dtr"]["profile"]
    a.plot(xp, kp, lw=0.8, label=f"plan ({res['fairness']['deck_edge']['plan']['sign_changes']} infl.)")
    a.plot(xz, kz * 5.0, lw=0.8, label=f"profile x5 ({res['fairness']['deck_edge']['profile']['sign_changes']} infl.)")
    a.axhline(0, color="k", lw=0.4)
    a.set_ylim(-1.0, 1.5)
    a.set_title("Deck edge curvature (1/m, sigma 60 mm)")
    a.legend(fontsize=7)
    # (e) sections
    a = ax[1, 1]
    sf = res["fairness"]["sections"]
    xsct = [r["x"] for r in sf]
    a.bar(xsct, [r["dwl_crease_deg"] or 0 for r in sf], width=300, color="#9467bd", label="DWL crease (deg)")
    for r in sf:
        a.text(r["x"], (r["dwl_crease_deg"] or 0) + 0.6, f"{r['sign_changes']}", ha="center", fontsize=7)
    a.set_title("Sections: DWL crease (side angle below - above, deg); numbers = inflections keel->strake")
    a.set_xlim(800, 7800)
    # (f) wall thickness
    a = ax[1, 2]
    for name, P, tm in ctx["tpts"]:
        t = tm[np.isfinite(tm)]
        a.hist(np.clip(t, 0, 4), bins=np.linspace(0, 4, 81), alpha=0.6, label=name)
    a.axvline(0.8, color="r", lw=0.8)
    wt = res["shell"]["wall_thickness"]
    a.set_yscale("log")
    a.set_title(f"Wall thickness (model mm): hull min {wt.get('hull_side', {}).get('min_model')}, "
                f"deck min {wt.get('deck', {}).get('min_model')}")
    a.legend(fontsize=7)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def header_image(res, width=1600):
    from PIL import Image, ImageDraw
    rows = res["summary"]["table"]
    sec = [i for i, r in enumerate(rows) if len(r) == 1]
    blocks = [rows[sec[i]:(sec[i + 1] if i + 1 < len(sec) else len(rows))] for i in range(len(sec))]
    cols = [blocks[0], blocks[1] + blocks[3], blocks[2]]
    lh = 17
    h = 64 + max(len(c) for c in cols) * lh + 8
    im = Image.new("RGB", (width, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    m = res["meta"]
    ok = res["summary"]["requirements_ok"]
    d.text((10, 6), f"HR 26 V10 scorecard: {m['name']}", fill=(0, 0, 0), font=_font(22, True))
    d.text((10, 36), f"{os.path.basename(m['stl'])}  |  frame {m['frame']} (rot {m['rotation_deg']} deg)  |  "
                     f"x anchor {m['x_anchor']} (bow tip x = {m['bow_tip_x']})  |  {m['run_at']}  |  "
                     f"ref: {os.path.basename(m.get('ref', '')) or '-'}  |  requirements: "
                     f"{'ALL PASS' if ok else 'FAIL: ' + str(len(res['summary']['requirements_failed']))}",
           fill=(60, 60, 60), font=_font(13))
    cw = width // 3
    f = _font(12)
    fb = _font(12, True)
    for ci, col in enumerate(cols):
        x = 10 + ci * cw
        y = 62
        for r in col:
            if len(r) == 1:
                d.text((x, y), r[0], fill=(0, 0, 120), font=fb)
                d.text((x + 300, y), "value", fill=(0, 0, 120), font=fb)
                d.text((x + 380, y), "rule", fill=(0, 0, 120), font=fb)
                d.text((x + 460, y), "d vs ref", fill=(0, 0, 120), font=fb)
                y += lh
                continue
            label, v, unit, rule, st, rv, delta = r
            vs = "-" if v is None else (("yes" if v else "no") if isinstance(v, bool) else
                                        (f"{v:g}" if isinstance(v, (int, float)) else str(v)))
            col_st = {"PASS": (0, 140, 0), "FAIL": (200, 0, 0)}.get(st, (60, 60, 60))
            d.text((x, y), label[:44], fill=(30, 30, 30), font=f)
            d.text((x + 300, y), f"{vs} {unit or ''}", fill=col_st, font=fb if st in ("PASS", "FAIL") else f)
            d.text((x + 380, y), rule or "", fill=(90, 90, 90), font=f)
            if delta is not None:
                d.text((x + 460, y), f"{delta:+g}", fill=(90, 90, 90), font=f)
            y += lh
    return im


def _safe(fn_, *a):
    try:
        return fn_(*a)
    except Exception:
        import traceback
        traceback.print_exc()
        return None


def render_sheet(res, ctx, args, png):
    from PIL import Image, ImageDraw
    t0 = time.time()
    V, F, fn, ext = ctx["V"], ctx["F"], ctx["fn"], ctx["ext"]
    W = 1600
    tw, th = 526, 300
    jobs = []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        for spec in FIXED_VIEWS:
            cam = view_cam(spec, V, tw, th - 18)
            jobs.append(("view", spec[0], ex.submit(render_view, cam, V, F, fn, 2)))
        for pv in PHOTO_VIEWS:
            jobs.append(("photo", pv["file"], ex.submit(_safe, photo_pair, pv, V, F, fn, args.photos, 795, 450)))
        plot_f = ex.submit(_safe, plots_image, res, ctx)
        head = header_image(res, W)
        views = Image.new("RGB", (W, 2 * th), (255, 255, 255))
        dv = ImageDraw.Draw(views)
        k = 0
        photos = []
        for kind, name, fut in jobs:
            r = fut.result()
            if kind == "view":
                im, _ = r
                x, y = 8 + (k % 3) * (tw + 4), (k // 3) * th
                views.paste(im, (x, y + 18))
                dv.text((x + 4, y + 2), f"{name}  (flat shading, Bambu Studio lights)", fill=(20, 20, 20), font=_font(13))
                k += 1
            elif r is not None:
                photos.append(r)
        plots = plot_f.result()
    if plots is None:
        plots = Image.new("RGB", (W, 40), (255, 255, 255))
        ImageDraw.Draw(plots).text((10, 10), "plots failed - see the console", fill=(200, 0, 0), font=_font(14))
    nrow = (len(photos) + 1) // 2
    ph = Image.new("RGB", (W, max(1, nrow) * 456), (255, 255, 255))
    for i, im in enumerate(photos):
        ph.paste(im, (4 + (i % 2) * 800, (i // 2) * 456))
    if plots.size[0] != W:
        plots = _fit_into(plots, W, round(plots.size[1] * W / plots.size[0]))
    total_h = head.size[1] + views.size[1] + (ph.size[1] if photos else 0) + plots.size[1]
    sheet = Image.new("RGB", (W, total_h), (255, 255, 255))
    y = 0
    for part in (head, views, ph if photos else None, plots):
        if part is None:
            continue
        sheet.paste(part, (0, y))
        y += part.size[1]
    sheet.save(png, optimize=True)
    log(f"  sheet {sheet.size[0]}x{sheet.size[1]}  ({time.time() - t0:.1f}s)")


# ============================================================================
# Main
# ============================================================================
def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def main(argv=None):
    ap = argparse.ArgumentParser(description="HR 26 V10 scorecard for one hull STL")
    ap.add_argument("stl")
    ap.add_argument("--frame", default="auto", choices=["auto", "plate", "boat"])
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--name", default=None)
    ap.add_argument("--ref", default=None)
    ap.add_argument("--anchor", default="auto", choices=["auto", "mast", "bow"])
    ap.add_argument("--xbow", type=float, default=4.0)
    ap.add_argument("--rays", type=int, default=30000)
    ap.add_argument("--photos", default="C:/Users/stig/Documents/Seilbåt")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args(argv)
    if args.name is None:
        args.name = os.path.splitext(os.path.basename(args.stl))[0]
    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    log(f"scoring {args.stl}")
    res, ctx = analyze(args.stl, args)
    out_json = os.path.join(args.out, f"{args.name}_score.json")
    ref_path = args.ref
    if ref_path is None:
        cand = os.path.join(HERE, "out", "baseline_fine_score.json")
        if os.path.exists(cand) and os.path.abspath(cand) != os.path.abspath(out_json):
            ref_path = cand
    ref = None
    if ref_path and os.path.exists(ref_path):
        with open(ref_path, encoding="utf-8") as fh:
            ref = json.load(fh)
        res["meta"]["ref"] = os.path.abspath(ref_path)
    res["summary"] = summarize(res, ref)
    if not args.no_render:
        try:
            png = os.path.join(args.out, f"{args.name}_score.png")
            render_sheet(res, ctx, args, png)
            res["meta"]["png"] = png
        except Exception as e:                      # never lose the numbers
            import traceback
            traceback.print_exc()
            res["meta"]["render_error"] = repr(e)
    res["meta"]["runtime_s"] = r1(time.time() - t0, 1)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(jsonable(res), fh, indent=1, ensure_ascii=False)
    log(f"wrote {out_json}  ({time.time() - t0:.0f}s)")
    for row in res["summary"]["table"]:
        log("  " + " | ".join(str(c) for c in row))
    return res


if __name__ == "__main__":
    main()
