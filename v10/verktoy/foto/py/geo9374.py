"""3D-trekk fra modellen til kameraet for IMG_9374 (babord side, baaten i
stroppene i travelliften).

Kopi av de delene av geo9387.py som trengs her (egen fil, saa arbeidet med
andre bilder ikke kan endre dette kameraet): fenderlisten, vannlinjestripen
paa siden, vinduets ender, kjolen (A._KeelProfile, 240 mm tykk, fas i
bunnen), roret og stevnen over z +260. Ingen CAD: kjol og ror bygges som
stablede profiler (appendages._foil) i et trekantnett.
"""
import numpy as np

import common as c
import uwlib as U

P, C = c.P, c.C


class Cam9374(U.Cam):
    """uwlib.Cam med valgfritt forskjoevet hovedpunkt (du, dv px fra bildets
    midte), radial fortegning k1 (u_d = c + x (1 + k1 r^2), r = |x| / f) og
    piksel-forhold asp (fy / fx). Med du = dv = k1 = 0 og asp = 1 er den
    akkurat uwlib.Cam(p[:7], W, H)."""

    def __init__(self, p, W=761, H=472, du=0.0, dv=0.0, k1=0.0, asp=1.0):
        super().__init__(p[:7], W, H)
        self.cx += du
        self.cy += dv
        self.k1 = k1
        self.asp = asp

    def project(self, X):
        Q = (np.asarray(X, float) - self.C) @ self.R.T
        z = np.maximum(Q[:, 2], 1e-6)
        a, b = Q[:, 0] / z, Q[:, 1] / z
        if self.k1:
            s = 1.0 + self.k1 * (a * a + b * b)
            a, b = a * s, b * s
        return self.f * a + self.cx, self.f * self.asp * b + self.cy, Q[:, 2]


def load_cam(mode=None, path=None):
    """Kameraet fra ../out/cam9374.json: hovedkameraet (mode=None) eller en
    navngitt modus ('pin', 'k1_bt', 'ppk1_bt', ...). Gir (Cam9374, dict)."""
    import json
    J = json.load(open(path or (c.W + "/out/cam9374.json")))
    key = mode or J["main"]
    d = J["modes"][key]
    q = d["q"]
    names = {"pin": [], "pp": ["du", "dv"], "k1": ["k1"], "ppk1": ["du", "dv", "k1"], "asp": ["asp"],
             "ppasp": ["du", "dv", "asp"], "k1asp": ["k1", "asp"]}[d["cmode"]]
    kw = dict(zip(names, q[7:7 + len(names)]))
    return Cam9374(q[:7], J["W"], J["H"], **kw), d


MODEL_REV = "0976477"      # modellen IMG_9374-kameraet er loest med (V10 trinn 4, foer trinn 5)
_SEC_CACHE = {}


def use_model(rev=MODEL_REV):
    """Last parameterne fra commit rev (git show rev:hr26/params.py) inn i
    hr26.params i minnet og bygg hr26.curves paa nytt. Endrer ingen filer.
    rev=None: arbeidstreet slik det ligger (hovedoekta endrer det underveis i
    trinn 5). Trengs fordi kameraet bruker kjolens hulkil-frie del, listen og
    vinduene fra modellen, og forkroppen skal vurderes mot modellen eieren saa."""
    import importlib
    import subprocess
    import sys
    if rev is not None:
        src = subprocess.run(["git", "-C", c.REPO, "show", "%s:hr26/params.py" % rev], capture_output=True,
                             check=True).stdout.decode("utf-8")
        ns = {}
        exec(compile(src, "params@%s" % rev, "exec"), ns)
        for k in [k for k in vars(P) if k.isupper()]:
            if k not in ns:
                delattr(P, k)
        for k, v in ns.items():
            if k.isupper():
                setattr(P, k, v)
    else:
        importlib.reload(sys.modules["hr26.params"])
    importlib.reload(sys.modules["hr26.curves"])
    c.C = sys.modules["hr26.curves"]
    if "hr26.appendages" in sys.modules:
        importlib.reload(sys.modules["hr26.appendages"])
    _SEC_CACHE.clear()
    _KEEL.clear()
    return rev


def side_y(x, z, sec_cache=_SEC_CACHE):
    """Skrogets halvbredde i hoeyden z ved stasjon x (fra C.section)."""
    key = round(float(x), 3)
    s = sec_cache.get(key)
    if s is None:
        s = np.asarray(C.section(float(x), 160), float)
        sec_cache[key] = s
    zz = s[:, 1]
    i0 = int(np.argmax(zz > zz[0] + 1.0))          # forbi den flate bunnen
    zs, ys = zz[i0:], s[i0:, 0]
    o = np.argsort(zs)
    return float(np.interp(z, zs[o], ys[o], left=np.nan, right=np.nan))


def strake_end_x():
    lo, hi = 6000.0, P.LOA
    for _ in range(40):
        m = 0.5 * (lo + hi)
        z = C.strake_z(m)
        y = side_y(m, z)
        if np.isfinite(y) and m < C.transom_x(z, y):
            lo = m
        else:
            hi = m
    return lo


def strake3(x0=450.0, x1=None, n=300):
    """Fenderlistens senter paa babord side: (x, -(skrog + proud/2), strake_z)."""
    if x1 is None:
        x1 = strake_end_x()
    xs = np.linspace(x0, x1, n)
    out = []
    for x in xs:
        z = C.strake_z(x)
        y = side_y(x, z)
        out.append((x, -(y + 0.5 * P.STRAKE_PROUD), z))
    return np.array(out)


def zline3(zfun, x0, x1, n=200):
    """Linje i hoeyden zfun(x) paa babord skrogside, fra x0 til x1 (stopper
    ved akterspeilet)."""
    xs = np.linspace(x0, x1, n)
    out = []
    for x in xs:
        z = zfun(x)
        y = side_y(x, z)
        if not np.isfinite(y):
            continue
        if x > C.transom_x(z, y):
            break
        out.append((x, -y, z))
    return np.array(out)


def bt_top_z(x, z0=146.0, z1=125.0):
    """Blaa overkant (IMG_9370): 146 ved x 1000, 125 fra x 5500."""
    t = np.clip((np.asarray(x, float) - 1000.0) / 4500.0, 0.0, 1.0)
    return z0 + (z1 - z0) * t


def window_ends():
    """Vinduets forreste og bakerste punkt (ytre ramme), som modellen har det:
    forenden rund, midt mellom under- og overkant; akterenden skraa, bakerste
    punkt naer underkanten. Usikkerhet ca. +-50 mm i x."""
    rf, ra = P.WIN_RAKE
    x0 = P.WIN_X0 + 0.5 * rf * 0.6
    zlo0 = C.strake_z(x0) + P.WIN_ABOVE_STRAKE
    zhi0 = C.sheer_z(x0) - P.WIN_BELOW_DECK
    zm = 0.5 * (zlo0 + zhi0)
    f = (x0, -side_y(x0, zm), zm)
    x1 = P.WIN_X1 - 15.0
    z1 = C.strake_z(x1) + P.WIN_ABOVE_STRAKE + 25.0
    a = (x1, -side_y(x1, z1), z1)
    return np.array([f, a])


def _stack_mesh(slices):
    """slices: liste av (k, 3) lukkede ringer med like mange punkter -> V, F."""
    Rr = np.array(slices)
    ns, nr, _ = Rr.shape
    V = Rr.reshape(-1, 3)
    idx = np.arange(ns * nr).reshape(ns, nr)
    a = idx[:-1, :]; b = np.roll(idx[:-1, :], -1, axis=1)
    cc = idx[1:, :]; d = np.roll(idx[1:, :], -1, axis=1)
    F = np.r_[np.c_[a.ravel(), b.ravel(), d.ravel()], np.c_[a.ravel(), d.ravel(), cc.ravel()]]
    for ring in (0, ns - 1):
        i0 = idx[ring, 0]
        fan = np.c_[np.full(nr - 2, i0), idx[ring, 1:-1], idx[ring, 2:]]
        F = np.r_[F, fan]
    return V, F


_KEEL = {}


def keel_mesh(z_top=-300.0, dz=12.0):
    """Kjolen som stablede profiler fra z_top ned til bunnen, med 45 graders
    fas (KEEL_BOT_CHAMFER) i bunnkanten. Over kanobunnen er den inne i skroget
    og skjult; hulkilen mot skroget er med i profilens for- og bakkant."""
    key = (z_top, dz)
    if key in _KEEL:
        return _KEEL[key]
    from hr26 import appendages as A
    k = A._KeelProfile()
    zb = k.zb
    cf = P.KEEL_BOT_CHAMFER
    zs = list(np.arange(z_top, zb + cf, -dz)) + list(np.linspace(zb + cf, zb, 5))
    slices = []
    for z in zs:
        le, te = k.edges(z)
        th = P.KEEL_TIP_T
        e = z - zb
        if e < cf:
            th -= 2.0 * (cf - e)
        th = max(th, 4.0)
        pts = np.array(A._foil(te - le, th, n=30))
        slices.append(np.c_[le + pts[:, 0], pts[:, 1], np.full(len(pts), z)])
    _KEEL[key] = _stack_mesh(slices)
    return _KEEL[key]


def keel_outline_xz():
    from hr26 import appendages as A
    return np.array(A.keel_outline())


def rudder_mesh(n=24):
    from hr26 import appendages as A
    slices = []
    for i in range(n + 1):
        t = i / n
        z = P.RUDDER_TOP_Z + (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z) * t
        le = P.RUDDER_X + P.RUDDER_RAKE * t
        ch = P.RUDDER_TE_X - le
        th = P.RUDDER_T * (1.0 - 0.28 * t)
        pts = np.array(A._foil(ch, th, n=20))
        slices.append(np.c_[le + pts[:, 0], pts[:, 1], np.full(len(pts), z)])
    return _stack_mesh(slices)


def stem_top3(z0=300.0, z1=1080.0, n=60):
    """Stevnen paa senterlinjen der den er rett (P.STEM_LINE)."""
    (xa, za), (xb, zb) = P.STEM_LINE
    zz = np.linspace(z0, z1, n)
    xx = xa + (zz - za) * (xb - xa) / (zb - za)
    return np.c_[xx, np.zeros(n), zz]


def hull_mesh():
    return U.hull_mesh(220, 60)
