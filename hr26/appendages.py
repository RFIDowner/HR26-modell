"""Kjol og ror."""
from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from . import curves as C
from . import params as P


def _foil(chord: float, thick: float, n: int = 22, te: float | None = None):
    """Symmetrisk NACA-lignende profil med butt bakkant.

    En knivskarp bakkant er baade uprintbar og en kilde til ugyldige
    flater i lofting og avrunding, saa bakkanten gis en liten tykkelse.
    """
    t = thick / chord
    te = (0.55 * P.SCALE) if te is None else te      # 0,55 mm i modellen
    te_half = 0.5 * min(te, 0.35 * thick) / chord
    up, lo = [], []
    for i in range(n + 1):
        beta = math.pi * i / n
        xc = 0.5 * (1.0 - math.cos(beta))          # fortetning i for- og bakkant
        yt = (
            5.0
            * t
            * (
                0.2969 * math.sqrt(xc)
                - 0.1260 * xc
                - 0.3516 * xc ** 2
                + 0.2843 * xc ** 3
                - 0.1015 * xc ** 4
            )
        )
        yt += te_half * xc
        up.append((xc * chord, yt * chord))
        lo.append((xc * chord, -yt * chord))
    pts = up + list(reversed(lo[1:]))
    return pts


def _foil_wire(x_le: float, z: float, chord: float, thick: float) -> cq.Wire:
    pts = _foil(chord, thick)
    v = [cq.Vector(x_le + px, py, z) for (px, py) in pts]
    return cq.Wire.assembleEdges(
        [cq.Edge.makeSpline(v + [v[0]])]
    )


def _offset_foil_wire(x_le: float, z: float, chord: float, thick: float, off: float) -> cq.Wire:
    """Profilet forskjoevet `off` utover langs normalen i snittplanet. Mot for-
    og bakkanten avtar forskyvningen til null (sin-vekt), saa hulkilen mot
    skroget ikke gjoer kjolen lengre enn omrisset i profil."""
    pts = np.array(_foil(chord, thick))
    if off > 0.0:
        d = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        w = np.sin(np.pi * np.clip(pts[:, 0] / chord, 0.0, 1.0)) ** 0.5
        pts = pts + (off * w)[:, None] * np.c_[-d[:, 1], d[:, 0]]   # utover: profilet gaar med klokka
    v = [cq.Vector(x_le + px, py, z) for (px, py) in pts]
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(v + [v[0]])])


def _keel_fillet_offset(d: float) -> float:
    """Kjolens utvidelse mot skroget, d mm under overgangen (negativ: inne i
    skroget). Ved overgangen er den 0,75 x KEEL_FILLET og flaten heller 30
    grader mot bunnen (et tydelig snitt, ikke tangerende, saa unionen er
    robust); KEEL_FILLET lenger ned gaar den tangentielt over i kjolsiden."""
    r = P.KEEL_FILLET
    a = 0.75 * r
    slope = 1.0 / math.tan(math.radians(30.0))
    if d <= 0.0:
        return a + slope * (-d)
    if d >= r:
        return 0.0
    k = slope * r / a
    return a * (1.0 - d / r) ** k


# ------------------------------------------------------- kjolens omriss
# Omrisset i senterplanet bygges som en polylinje: kanobunnen (curves.bottom_z)
# -> hulkil -> rett forkant -> rundet hjoerne -> flat bunn -> rundet hjoerne ->
# rett bakkant -> hulkil -> kanobunnen. Hjoernene er eksakte sirkelbuer.
# Hulkilenes sentrum ligger KEEL_*_FILLET_R fra kantlinjen og fra den sampel-
# tatte kanobunnen, saa roten foelger kanobunnen uansett hvordan den endres.
def _arc(c, p0, p1, n: int = 16):
    a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
    a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
    da = (a1 - a0 + math.pi) % (2.0 * math.pi) - math.pi      # korteste vei
    r = math.hypot(p0[0] - c[0], p0[1] - c[1])
    return [(c[0] + r * math.cos(a0 + da * i / n), c[1] + r * math.sin(a0 + da * i / n)) for i in range(n + 1)]


class _KeelProfile:
    def __init__(self):
        zb = P.KEEL_TIP_Z
        self.zb = zb
        fwd = self._edge_chain(P.KEEL_LE_LINE, P.KEEL_LE_TIP_R, P.KEEL_LE_FILLET_R, -1.0)
        aft = self._edge_chain(P.KEEL_TE_LINE, P.KEEL_TE_TIP_R, P.KEEL_TE_FILLET_R, +1.0)
        self.fwd = np.array(fwd)          # fra kanobunnen ned til bunnen
        self.aft = np.array(aft)
        self.x_fwd, self.x_aft = self.fwd[0, 0], self.aft[0, 0]

    @staticmethod
    def _edge_chain(line, r_tip, r_fil, side):
        """En kant (side -1 forkant, +1 bakkant) fra kanobunnen til bunnen."""
        (xa, za), (xb, zb_) = line
        d = np.array([xb - xa, zb_ - za], float)
        d /= np.linalg.norm(d)
        if d[1] > 0.0:
            d = -d                                        # nedover
        p = np.array([xa, za], float)
        zb = P.KEEL_TIP_Z
        # hjoernet mot bunnen: bunnen gaar innover (-side) fra kanten
        q = p + d * (zb - p[1]) / d[1]
        bdir = np.array([-side, 0.0])
        th = math.acos(float(np.clip(d @ bdir, -1.0, 1.0)))
        t = r_tip * math.tan(0.5 * th)
        t1, t2 = q - t * d, q + t * bdir
        corner = _arc(t2 + np.array([0.0, r_tip]), t1, t2)
        # hulkilen: sentrum paa linjen parallelt med kanten, r_fil utenfor
        n_out = np.array([-d[1], d[0]])
        if n_out[0] * side < 0.0:
            n_out = -n_out
        # Hulkilen regnes mot kanobunnen loftet KEEL_FILLET_LIFT opp, saa den
        # krysser den ekte kanobunnen med en liten vinkel (ca. 12-14 grader) i
        # stedet for aa tangere den: et tydelig snitt gir en robust union.
        lift = P.KEEL_FILLET_LIFT
        xs = np.arange(max(q[0] - 3000.0, 300.0), min(q[0] + 3000.0, P.LOA - 100.0), 5.0)
        cb = np.c_[xs, [C.bottom_z(float(x)) + lift for x in xs]]

        def gap(s):
            c = p + s * d + r_fil * n_out
            dist = np.hypot(cb[:, 0] - c[0], cb[:, 1] - c[1])
            i = int(np.argmin(dist))
            below = c[1] < C.bottom_z(float(c[0])) + lift
            return (dist[i] - r_fil) if below else -dist[i] - r_fil, cb[i], c
        lo, hi = -3000.0, float(np.dot(q - p, d))         # hi: ved bunnen, langt fra kanobunnen
        for _ in range(60):
            m = 0.5 * (lo + hi)
            if gap(m)[0] > 0.0:
                hi = m
            else:
                lo = m
        _, tb, c = gap(hi)
        te = p + hi * d                                   # tangentpunktet paa kanten
        fillet = _arc(c, tb, te)
        line_pts = [tuple(te), tuple(t1)]
        return [tuple(v) for v in fillet] + line_pts[1:] + corner[1:]

    def edges(self, z):
        """(forkant, bakkant) i hoyden z. Over hulkilenes ytterpunkter (inne
        i skroget) staar de fast der."""
        def at(chain):
            if z >= chain[0, 1]:
                return float(chain[0, 0])
            if z <= chain[-1, 1]:
                return float(chain[-1, 0])
            return float(np.interp(-z, -chain[:, 1], chain[:, 0]))
        return at(self.fwd), at(self.aft)


def keel_outline():
    """Kjolens omriss i senterplanet som (x, z)-liste fra kanobunnen foran,
    ned forkanten, langs bunnen og opp bakkanten. Til kontroll og overlegg."""
    k = _KeelProfile()
    return [tuple(map(float, v)) for v in k.fwd] + [tuple(map(float, v)) for v in k.aft[::-1]]


def keel() -> cq.Workplane:
    """Finnekjol, loftet gjennom vannrette snitt fra et stykke inne i skroget
    ned til bunnen. Omrisset (for- og bakkant i hver hoyde) kommer fra
    _KeelProfile, med hulkiler i profil mot curves.bottom_z.

    Mot skroget utvides tverrsnittet i tillegg (KEEL_FILLET), saa overgangen
    blir en hulkil ogsaa sett forfra. Bunnkanten fases 45 grader i tverrsnitt
    (KEEL_BOT_CHAMFER): fasen er printbar uten stoette, og en flat stripe
    staar igjen som kjolen staar paa ved print. Det store hjoernet mellom
    forkant og bunn (KEEL_LE_TIP_R) heller mer enn 45 grader de nederste
    ca. 170 mm og trenger stoette ved platen.
    """
    k = _KeelProfile()
    xs = np.linspace(k.x_fwd, k.x_aft, 80)
    z_cb = [C.bottom_z(float(x)) for x in xs]
    z_top = max(z_cb) + P.KEEL_ROOT_UP
    z_root = float(np.mean(z_cb))
    cf = P.KEEL_BOT_CHAMFER

    def thick(z):
        t = min(max((z_root - z) / (z_root - k.zb), 0.0), 1.0)
        th = P.KEEL_ROOT_T + (P.KEEL_TIP_T - P.KEEL_ROOT_T) * t
        e = z - k.zb
        if e < cf:                                   # 45 graders fas paa bunnkanten
            th -= 2.0 * (cf - e)
        return th

    # overgangen: kanobunnens hoyde der kjolsiden moeter den, midlet langs roten
    le0, te0 = k.edges(z_root - 120.0)
    th0 = thick(z_root - 120.0)
    z_j = []
    for x in np.linspace(le0 + 0.1 * (te0 - le0), le0 + 0.9 * (te0 - le0), 9):
        sec = np.asarray(C.section(float(x), 60), dtype=float)
        z_j.append(float(np.interp(0.5 * th0, sec[:, 0], sec[:, 1])))
    zj = float(np.mean(z_j))
    r = P.KEEL_FILLET

    # hoyder: ett snitt inne i skroget, saa jevnt hver KEEL_DZ fra toppen av
    # hulkilen mot skroget ned til bunnen. Jevn avstand er viktig: loften
    # svinger ut mellom tett og glissent plasserte snitt.
    z1 = zj + 0.7 * r
    n = max(int(math.ceil((z1 - k.zb) / P.KEEL_DZ)), 2)
    zs = [z1 - (z1 - k.zb) * i / n for i in range(n + 1)]
    if cf > 0.0:                                     # et snitt noyaktig der fasen slutter
        zs = sorted([z for z in zs if abs(z - (k.zb + cf)) > 0.25 * P.KEEL_DZ] + [k.zb + cf], reverse=True)

    # inne i skroget: snitt med samme avstand opp til z_top, der utvidelsen
    # trappes ned til null (rent profil oeverst)
    m = max(int(math.ceil((z_top - z1) / P.KEEL_DZ)), 1)
    off1 = _keel_fillet_offset(zj - z1) if r > 0.0 else 0.0
    wires = []
    for i in range(m):
        z = z_top - (z_top - z1) * i / m
        le, te = k.edges(z)
        wires.append(_offset_foil_wire(le, z, te - le, thick(z1), off1 * i / m))
    for z in zs:
        le, te = k.edges(z)
        off = _keel_fillet_offset(zj - z) if r > 0.0 else 0.0
        wires.append(_offset_foil_wire(le, z, te - le, thick(z), off))
    # Rett (ruled) loft: snittene staar saa tett (KEEL_DZ) at kantene mellom
    # dem ikke synes (buehoeyde under 0,01 mm i 1:30 i hulkilene), og den
    # glatte loften svinger ut gjennom saa mange snitt.
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=True)])


def _pin_positions():
    for z in P.RUDDER_PIN_Z:
        t = (z - P.RUDDER_TOP_Z) / (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z)
        yield P.RUDDER_X + P.RUDDER_RAKE * t, z


def rudder_pins(extra: float = 0.0) -> cq.Workplane:
    """Tappene paa rorets forkant (og malen for hullene i akterspeilet)."""
    out = None
    d = P.RUDDER_PIN_D + extra
    for x, z in _pin_positions():
        c = (
            cq.Workplane("YZ")
            .workplane(offset=x - P.RUDDER_PIN_L)
            .circle(0.5 * d)
            .extrude(P.RUDDER_PIN_L + 0.3 * P.SCALE)
            .translate((0, 0, z))
        )
        out = c if out is None else out.union(c)
    return out


def rudder() -> cq.Workplane:
    """Akterhengt ror. Forkanten foelger akterspeilets helning (RUDDER_RAKE
    er negativ: forover nedover), med RUDDER_GAP klaring til akterspeilet."""
    wires = []
    steps = 5
    for i in range(steps + 1):
        t = i / steps
        z = P.RUDDER_TOP_Z + (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z) * t
        le = P.RUDDER_X + P.RUDDER_RAKE * t
        ch = P.RUDDER_TE_X - le
        th = P.RUDDER_T * (1.0 - 0.28 * t)
        wires.append(_foil_wire(le, z, ch, th))
    solid = cq.Solid.makeLoft(wires, ruled=False)
    return cq.Workplane("XY").newObject([solid]).union(rudder_pins())
