"""Prototype: kubiske B-splines i ren numpy (skal inn i curves.py)."""
import numpy as np


def basis(x, t, k=3, der=0):
    """B-spline-basis (rader = x, kolonner = basisfunksjoner), Cox-de Boor."""
    x = np.atleast_1d(np.asarray(x, dtype=float))
    t = np.asarray(t, dtype=float)
    x = np.clip(x, t[k], t[-k - 1])
    # grad 0: halvaapne intervaller, siste ikke-tomme intervall lukket til hoeyre
    nint = len(t) - 1
    B = np.zeros((len(x), nint))
    for i in range(nint):
        if t[i] < t[i + 1]:
            B[:, i] = (x >= t[i]) & (x < t[i + 1])
    last = max(i for i in range(nint) if t[i] < t[i + 1])
    B[x >= t[last + 1], last] = 1.0
    for d in range(1, k + 1):
        Bn = np.zeros((len(x), nint - d))
        for i in range(nint - d):
            a = t[i + d] - t[i]
            b = t[i + d + 1] - t[i + 1]
            if d > k - der:
                # derivert: k/(t_{i+k}-t_i) B_{i,k-1} - ...
                v = 0.0
                if a > 0:
                    v = v + d / a * B[:, i]
                if b > 0:
                    v = v - d / b * B[:, i + 1]
            else:
                v = 0.0
                if a > 0:
                    v = v + (x - t[i]) / a * B[:, i]
                if b > 0:
                    v = v + (t[i + d + 1] - x) / b * B[:, i + 1]
            Bn[:, i] = v
        B = Bn
    return B


class Spl:
    def __init__(self, t, c, k=3):
        self.t = np.asarray(t, float)
        self.c = np.asarray(c, float)
        self.k = k

    def __call__(self, x, der=0):
        return basis(x, self.t, self.k, der) @ self.c

    def scalar(self, x):
        """de Boor for ett punkt (rask, ren python)."""
        t, c, k = self.t, self.c, self.k
        x = min(max(x, t[k]), t[-k - 1])
        j = int(np.searchsorted(t, x, side="right")) - 1
        j = min(max(j, k), len(t) - k - 2)
        d = [c[j - k + r] for r in range(k + 1)]
        for r in range(1, k + 1):
            for i in range(k, r - 1, -1):
                a = (x - t[i + j - k]) / (t[i + 1 + j - r] - t[i + j - k])
                d[i] = (1.0 - a) * d[i - 1] + a * d[i]
        return d[k]


def knots(x0, x1, interior, k=3):
    return np.r_[[x0] * (k + 1), interior, [x1] * (k + 1)]


def gram(t, k=3, der=2):
    """G[i,j] = integral B_i^(der) B_j^(der) dx (Gauss, eksakt for kubisk)."""
    gx, gw = np.polynomial.legendre.leggauss(k + 1)
    xs, ws = [], []
    for a, b in zip(t[:-1], t[1:]):
        if b > a:
            xs.append(0.5 * (b - a) * gx + 0.5 * (a + b))
            ws.append(0.5 * (b - a) * gw)
    xs = np.concatenate(xs); ws = np.concatenate(ws)
    D = basis(xs, t, k, der)
    return D.T @ (D * ws[:, None])


def fit(x, y, t, w=None, lam=0.0, pen_der=2, A=None, b=None, k=3):
    """Vektet minste kvadraters spline med glattestraff og likhetskrav A c = b."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    w = np.ones_like(x) if w is None else np.asarray(w, float)
    B = basis(x, t, k)
    H = B.T @ (B * w[:, None])
    g = B.T @ (w * y)
    if lam:
        H = H + lam * gram(t, k, pen_der)
    if A is None:
        c = np.linalg.solve(H, g)
    else:
        A = np.atleast_2d(A); b = np.atleast_1d(b)
        n, m = H.shape[0], A.shape[0]
        K = np.zeros((n + m, n + m))
        K[:n, :n] = H; K[:n, n:] = A.T; K[n:, :n] = A
        c = np.linalg.solve(K, np.r_[g, b])[:n]
    return Spl(t, c, k)


def curvature(s, x):
    d1 = s(x, 1); d2 = s(x, 2)
    return d2 / (1.0 + d1 ** 2) ** 1.5


def sign_changes(xx, kk, eps=0.0):
    sg = np.sign(np.where(np.abs(kk) <= eps, 0.0, kk))
    nz = sg != 0
    xs, ss = xx[nz], sg[nz]
    idx = np.nonzero(np.diff(ss) != 0)[0]
    return xs[idx]


def fit_shape(x, y, t, w=None, lam=0.0, pen_der=3, A=None, b=None, sign=0, k=3, tol=1e-9, Gx=None, hx=None):
    """Som fit, men med fortegnskrav paa 2. derivert i alle knutepunkter:
    sign=-1: y'' <= 0 overalt, sign=+1: y'' >= 0 overalt (kubisk -> y'' lineaer
    mellom knutene, saa kravet i knutene gjelder hele kurven). Aktiv-mengde."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    w = np.ones_like(x) if w is None else np.asarray(w, float)
    B = basis(x, t, k)
    H = B.T @ (B * w[:, None])
    g = B.T @ (w * y)
    if lam:
        H = H + lam * gram(t, k, pen_der)
    n = H.shape[0]
    Aeq = np.zeros((0, n)) if A is None else np.atleast_2d(A)
    beq = np.zeros(0) if b is None else np.atleast_1d(b)
    kn = np.unique(t)
    G = -sign * basis(kn, t, k, 2) if sign else np.zeros((0, n))   # G c <= h
    h = np.zeros(len(G))
    if Gx is not None:
        G = np.vstack([G, np.atleast_2d(Gx)]); h = np.r_[h, np.atleast_1d(hx)]
    active = []
    for _ in range(4 * len(kn) + 10):
        M = np.vstack([Aeq, G[active]]) if active else Aeq
        r = np.r_[beq, h[active]]
        m = M.shape[0]
        K = np.zeros((n + m, n + m)); K[:n, :n] = H
        if m:
            K[:n, n:] = M.T; K[n:, :n] = M
        sol = np.linalg.solve(K, np.r_[g, r])
        c, nu = sol[:n], sol[n + len(beq):]
        if active and nu.min() < -tol * max(1.0, np.abs(nu).max()):
            active.pop(int(np.argmin(nu)))
            continue
        v = G @ c - h if len(G) else np.zeros(0)
        if active:
            v[active] = -np.inf
        if len(v) == 0 or v.max() <= tol * max(1.0, np.abs(c).max()):
            break
        active.append(int(np.argmax(v)))
    return Spl(t, c, k)
