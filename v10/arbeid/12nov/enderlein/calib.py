"""Calibration of Enderlein drawing 448-5 (scan 2560 x 1772 px).

Both views share the sheet's horizontal axis: long bulkhead lines common to
profile and plan agree within 1-2 px (x = 525, 819, 962, 1085, 1432, 1581),
and the transom's aft-most point is x = 373.5 px in both. So one x scale
and one bow reference serve both views.

  x (mm from the bow) = (X_BOW - px) * S
  profile: z (mm above the drawing's DWL) = (Y_DWL(px) - py) * S
  plan:    y (half-breadth, mm, + = top/port side) = (Y_CL - py) * S

S comes from LOA = 7950 mm over the plan outline (line centres, bow tip
2240.1 px to transom 373.5 px = 1866.6 px). Independent checks: the
settee berths (2.0 m in the specification) are 469.1 px = 1998 mm, the
folding table (90 cm) 211 px = 899 mm, and the station spacing 150.1 px is
639 mm (a 640 mm grid would give S = 4.264). Vertical scale = horizontal
scale (isotropic scan; see the report for the evidence and the bound).
"""
X_BOW = 2240.1          # plan bow tip, centre of the outline ink
X_TRANSOM = 373.5       # plan transom on the centreline (= profile transom aft-most point)
LOA = 7950.0
S = LOA / (X_BOW - X_TRANSOM)      # 4.2591 mm/px
S_Y = S
Y_CL = 1333.2           # plan centreline (dash-dot line fitted over x 400-2200, rms 0.2 px)
# profile DWL: dashed line beyond the hull at both ends
Y_DWL_AFT, X_DWL_AFT = 541.35, 290.0
Y_DWL_FWD, X_DWL_FWD = 542.18, 2066.0

# uncertainty (1 sigma-ish, see report)
SIG_PX_LINE = 0.7       # centre of a traced line, px
SIG_S_REL = 0.0012      # LOA definition (line centre vs outer edge = 0.24 % span)
SIG_ANISO = 0.01        # vertical vs horizontal scale, conservative


def y_dwl(px):
    return Y_DWL_AFT + (px - X_DWL_AFT) * (Y_DWL_FWD - Y_DWL_AFT) / (X_DWL_FWD - X_DWL_AFT)


def prof_xz(px, py):
    """profile pixel -> (x from bow, z above the drawing's DWL), mm"""
    return (X_BOW - px) * S, (y_dwl(px) - py) * S_Y


def plan_xy(px, py):
    """plan pixel -> (x from bow, half-breadth; + = upper side of the sheet), mm"""
    return (X_BOW - px) * S, (Y_CL - py) * S_Y


def x_to_px(x):
    return X_BOW - x / S


def prof_px(x, z):
    px = X_BOW - x / S
    return px, y_dwl(px) - z / S_Y


def plan_px(x, y):
    return X_BOW - x / S, Y_CL - y / S_Y


if __name__ == "__main__":
    print(f"S = {S:.4f} mm/px  (1:15 => scan {15 / S * 25.4:.1f} dpi)")
    print("DWL at bow/stern px:", round(y_dwl(2240), 2), round(y_dwl(373), 2))
