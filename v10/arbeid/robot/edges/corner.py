import math
import numpy as np

def seg_dist(P, A, B):
    """distance from point P to segments A->B (arrays)"""
    AB = B - A; AP = P - A
    t = np.clip((AP * AB).sum(1) / np.maximum((AB * AB).sum(1), 1e-12), 0, 1)
    Q = A + t[:, None] * AB
    return np.hypot(*(P - Q).T), Q

def fit_line(pts):
    c = pts.mean(0)
    u, s, vt = np.linalg.svd(pts - c)
    return c, vt[0]

def in_box(P, box):
    u0, u1, v0, v1 = box
    return (P[:, 0] >= u0) & (P[:, 0] <= u1) & (P[:, 1] >= v0) & (P[:, 1] <= v1)

def densify(segs, step=1.5):
    out = [segs.reshape(-1, 2)]
    L = np.hypot(*(segs[:, 1] - segs[:, 0]).T)
    for (a, b), l in zip(segs, L):
        n = int(l // step)
        if n >= 1:
            t = (np.arange(1, n + 1) / (n + 1))[:, None]
            out.append(a + t * (b - a))
    return np.vstack(out)

def corner(segs, boxA, boxB, search=80.0):
    """segs (M,2,2). Flank boxes A and B. Returns dict with interior angle, corner-cut distance d,
    radius from d, and turning-span radius along the contour between the flanks."""
    P = densify(segs)
    A = P[in_box(P, boxA)]; Bp = P[in_box(P, boxB)]
    if len(A) < 2 or len(Bp) < 2:
        return None
    ca, da = fit_line(A); cb, db = fit_line(Bp)
    # intersection
    M = np.array([da, -db]).T
    try:
        t = np.linalg.solve(M, cb - ca)
    except np.linalg.LinAlgError:
        return None
    C = ca + t[0] * da
    # directions pointing from C to flank centroids
    ea = ca - C; ea /= np.linalg.norm(ea); eb = cb - C; eb /= np.linalg.norm(eb)
    alpha = math.acos(np.clip(np.dot(ea, eb), -1, 1))     # angle between flanks at the corner
    # distance from C to contour (segments near C)
    near = (np.hypot(*(segs[:, 0] - C).T) < search) | (np.hypot(*(segs[:, 1] - C).T) < search)
    S = segs[near]
    d, Q = seg_dist(C, S[:, 0], S[:, 1])
    i = np.argmin(d); dmin = d[i]
    # fillet radius for a circular arc tangent to both flanks: d = R (1/sin(a/2) - 1)
    k = 1.0 / math.sin(alpha / 2) - 1.0
    R = dmin / k if k > 1e-9 else float('nan')
    # rms deviation of flanks from their lines (noise level)
    na = np.array([-da[1], da[0]]); nb = np.array([-db[1], db[0]])
    rmsA = np.sqrt((((A - ca) @ na) ** 2).mean()); rmsB = np.sqrt((((Bp - cb) @ nb) ** 2).mean())
    # transition length: contour points within `search` of C that deviate > tol from both lines
    tol = max(1.0, 2.5 * max(rmsA, rmsB))
    Pn = P[np.hypot(*(P - C).T) < search]
    devA = np.abs((Pn - ca) @ na); devB = np.abs((Pn - cb) @ nb)
    trans = Pn[(devA > tol) & (devB > tol)]
    span = 0.0
    if len(trans) >= 2:
        # extent of the transition zone measured along the bisector-normal
        bis = (ea + eb); bis /= np.linalg.norm(bis) if np.linalg.norm(bis) > 1e-9 else 1
        perp = np.array([-bis[1], bis[0]])
        span = np.ptp(trans @ perp)
    # radius implied by transition span: chord between tangent points = 2 R cos(alpha/2)
    R_span = span / (2 * math.cos(alpha / 2)) if span > 0 else 0.0
    return dict(C=C, alpha=math.degrees(alpha), d=dmin, R=R, rmsA=rmsA, rmsB=rmsB, R_span=R_span,
                nA=len(A), nB=len(Bp))

def fmt(name, r):
    if r is None:
        return f"{name:38s} (no data)"
    return (f"{name:38s} corner at ({r['C'][0]:7.0f},{r['C'][1]:6.0f})  angle {r['alpha']:5.1f} deg  "
            f"cut d {r['d']:5.1f}  R(d) {r['R']:6.1f} mm full = {r['R']/30:4.2f} mm model  "
            f"R(span) {r['R_span']:6.1f}  flank rms {r['rmsA']:.1f}/{r['rmsB']:.1f}")

def circle_fit(P):
    """Kasa algebraic circle fit. Returns (cx, cy, R, rms)."""
    x, y = P[:, 0], P[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    b = x * x + y * y
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy, c = sol
    R = math.sqrt(max(c + cx * cx + cy * cy, 0))
    rms = np.sqrt(((np.hypot(x - cx, y - cy) - R) ** 2).mean())
    return cx, cy, R, rms

def bump(segs, box):
    P = densify(segs)
    Q = P[in_box(P, box)]
    if len(Q) < 5:
        return None
    return circle_fit(Q), np.ptp(Q[:, 0]), np.ptp(Q[:, 1]), len(Q)

def min_radius(segs, C, arc=60.0, w=8.0, step=1.0):
    """Chain the section, take the polyline closest to point C, resample it at `step` mm over
    +-arc around the closest point and return the smallest 3-point circle radius with
    points +-w apart (mm), plus where it occurs."""
    from lib import chain
    lines = chain(segs, tol=1e-3)
    best = None
    for L in lines:
        if len(L) < 3: continue
        d = np.hypot(L[:, 0] - C[0], L[:, 1] - C[1])
        i = np.argmin(d)
        if best is None or d[i] < best[0]:
            best = (d[i], L, i)
    if best is None: return None
    _, L, i = best
    seg = np.hypot(*np.diff(L, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    s0 = s[i]
    ss = np.arange(max(0, s0 - arc), min(s[-1], s0 + arc), step)
    if len(ss) < 2 * w / step + 3: return None
    X = np.interp(ss, s, L[:, 0]); Y = np.interp(ss, s, L[:, 1])
    k = int(round(w / step))
    Rs = []
    for j in range(k, len(ss) - k):
        p1 = np.array([X[j - k], Y[j - k]]); p2 = np.array([X[j], Y[j]]); p3 = np.array([X[j + k], Y[j + k]])
        a = np.linalg.norm(p2 - p1); b = np.linalg.norm(p3 - p2); c = np.linalg.norm(p3 - p1)
        area2 = abs((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0]))
        R = a * b * c / (2 * area2) if area2 > 1e-9 else np.inf
        Rs.append((R, X[j], Y[j]))
    Rs.sort(key=lambda t: t[0])
    return Rs[0]
