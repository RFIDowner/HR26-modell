"""Enkel sammensetning for aa se paa modellen: skrog, lokk, ror, mast med
beslag, bom, rekkepaaler, stativ og skilt i EN STL, i 1:30, staaende paa
stativet. Bare til betraktning - ikke til print.

  python tools/memcap.py --gb 3 --lock -- python tools/sammensetning.py [valg]

  --uten-lokk     ruff-taket utelates, saa man ser ned i kahytten
  --uten-rigg     mast, beslag, bom og rekkepaaler utelates
  --uten-stativ   stativ og skilt utelates
  --seil          bommen med surret seil i stedet for bar bom
  --ut FIL        utfil (standard export/visning/hr26_sammensatt.stl)

Skroget og skiltet hentes fra de ferdige STL-ene i export/stl (skroget legges
tilbake fra platen), saa det tunge skrogbygget trengs ikke; resten bygges i
baatens koordinater (x fra baugen, y mot styrbord, z opp fra vannlinjen).
Delene er ikke smeltet sammen: hver del er sitt eget lukkede skall, slik at
klaringene mellom dem synes. Pulpit, pushpit og livliner (messingtraad og
tau) er ikke med.

Utfila ligger i export/visning, som ikke sjekkes inn (den er like stor som
skroget og kan lages paa nytt paa et minutt).
"""
from __future__ import annotations

import math
import os
import struct
import sys
import time

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
STL_DIR = os.path.join(ROOT, "export", "stl")
OUT_DIR = os.path.join(ROOT, "export", "visning")
TESS_TOL = 0.6        # fullskala-mm (0,02 mm i 1:30, som eksporten)
TESS_ANG = 0.2


# ------------------------------------------------------------------ nett
def load_stl(path: str) -> np.ndarray:
    """Trekantene i en binaer STL: (n, 3, 3)."""
    with open(path, "rb") as f:
        d = f.read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]),
                        count=n, offset=84)
    return rec["v"].astype(np.float64)


def write_stl(path: str, T: np.ndarray) -> None:
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(n, axis=1)
    n = n / np.maximum(ln, 1e-30)[:, None]
    rec = np.zeros(len(T), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    rec["n"] = n.astype(np.float32)
    rec["v"] = T.astype(np.float32)
    with open(path, "wb") as f:
        f.write(b"HR 26 1:30 sammensetning (bare til betraktning)".ljust(80, b" "))
        f.write(struct.pack("<I", len(T)))
        f.write(rec.tobytes())


def rot_z(T: np.ndarray, deg: float) -> np.ndarray:
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a), 0.0], [math.sin(a), math.cos(a), 0.0], [0.0, 0.0, 1.0]])
    return T @ R.T


def move(T: np.ndarray, dx=0.0, dy=0.0, dz=0.0) -> np.ndarray:
    return T + np.array([dx, dy, dz])


def tess(wp, scale: float) -> np.ndarray:
    """Trekantene til alle volumene i en Workplane, skalert."""
    import cadquery as cq

    out = []
    for s in wp.vals():
        if not isinstance(s, cq.Shape):
            continue
        vs, tris = s.tessellate(TESS_TOL, TESS_ANG)
        V = np.array([(v.x, v.y, v.z) for v in vs], dtype=np.float64)
        F = np.array(tris, dtype=np.int64)
        if len(F):
            out.append(V[F])
    return np.concatenate(out) * scale


# ------------------------------------------------------------- delene
def hull_from_plate(P) -> np.ndarray:
    """01_skrog.stl lagt tilbake fra platen til baatens ramme, i modell-mm.

    Paa platen er skroget dreid om Z til det passer (45 grader) og sentrert
    (build.lay_flat). Tilbake: dreies samme vinkel motsatt vei; baugens spiss
    ligger paa x = 4 mm (fullskala; hull.BOW_STATIONS, poengkortet finner det
    samme fra masthullet), skroget er symmetrisk om y = 0, og kjolens
    underside er dypgangen."""
    T = load_stl(os.path.join(STL_DIR, "01_skrog.stl"))
    T = rot_z(T, -45.0)
    x = T[..., 0]
    # hvilken ende er hekken? Den brede enden (akterspeilet).
    lo = x < x.min() + 4.0
    hi = x > x.max() - 4.0
    w_lo = np.ptp(T[..., 1][lo]) if lo.any() else 0.0
    w_hi = np.ptp(T[..., 1][hi]) if hi.any() else 0.0
    if w_lo > w_hi:                      # baugen ligger mot +x: snu
        T = rot_z(T, 180.0)
    T = move(T, -T[..., 0].min() + 4.0 / P.SCALE,
             -0.5 * (T[..., 1].min() + T[..., 1].max()),
             -T[..., 2].min() - P.DRAFT / P.SCALE)
    return T


def plaque_from_plate(P) -> np.ndarray:
    """15_skilt.stl liggende foran stativet (styrbord side), teksten vendt ut."""
    path = os.path.join(STL_DIR, "15_skilt.stl")
    if not os.path.exists(path):
        return np.zeros((0, 3, 3))
    T = rot_z(load_stl(path), 180.0)
    xc = 0.5 * sum(P.STAND_STATIONS) / P.SCALE
    half_h = 0.5 * np.ptp(T[..., 1])
    y = 0.5 * P.STAND_BASE_W / P.SCALE + 12.0 + half_h
    z = (-P.DRAFT - P.STAND_CLEAR - 9.0 * P.SCALE) / P.SCALE     # bjelkens underside = bordet
    return move(T, xc, y, z)


def one_stanchion(P):
    """En rekkepaale uten spruen (som rig.stanchions lager dem)."""
    import cadquery as cq

    part = (
        cq.Workplane("XY").circle(0.5 * P.STANCHION_SHAFT).extrude(P.STANCHION_H)
        .union(cq.Workplane("XY").circle(0.5 * P.STANCHION_SHAFT * 0.92).extrude(-P.STANCHION_PIN))
    )
    for z in P.LIFELINE_Z:
        part = part.union(
            cq.Workplane("XY").workplane(offset=z - 0.5 * P.LIFELINE_EYE_H)
            .rect(P.LIFELINE_EYE_L, P.LIFELINE_EYE_W).extrude(P.LIFELINE_EYE_H))
        part = part.cut(
            cq.Workplane("YZ").workplane(offset=-P.LIFELINE_EYE_L)
            .circle(0.5 * P.LIFELINE_EYE_D).extrude(2.0 * P.LIFELINE_EYE_L)
            .translate((0.0, 0.0, z)))
    return part


def surface_z(x: float, y: float, P, C, D) -> float:
    """Flaten et rekkehull staar i: dekket, akterdekket eller skulderen
    (V11: gangbordet)."""
    if getattr(P, "WALK", False):
        from hr26 import gangbord as G
        return G.surface_z(x, abs(y))
    hb = C.deck_half_breadth(x)
    z = D.top_z(x, abs(y)) if hasattr(D, "top_z") else C.deck_z(x, abs(y))
    if getattr(P, "KNUCKLE_Z", None) and C.knuckle_drop(x) > 0.0:
        z = min(z, C.knuckle_z(x) + (hb - abs(y)) * math.tan(math.radians(P.KNUCKLE_ANGLE)))
    return z


def main() -> None:
    a = sys.argv[1:]
    out = os.path.join(OUT_DIR, "hr26_sammensatt.stl")
    if "--ut" in a:
        out = a[a.index("--ut") + 1]
    t0 = time.time()

    from hr26 import appendages as A
    from hr26 import cabin as CB
    from hr26 import curves as C
    from hr26 import deckhouse as D
    from hr26 import params as P
    from hr26 import rig as R
    from hr26 import stand as ST

    s = 1.0 / P.SCALE
    parts = []

    def add(name, T):
        if len(T):
            parts.append((name, T))
            print(f"  {name:<14s} {len(T):7d} trekanter  {time.time() - t0:5.0f}s")

    add("skrog", hull_from_plate(P))
    add("ror", tess(A.rudder(), s))
    if P.CABIN and "--uten-lokk" not in a:
        add("ruff-tak", tess(CB.lid(), s))

    if "--uten-rigg" not in a:
        xm = P.MAST_STEP_X
        zr = D.coach_roof_z(xm)                       # taket der masten staar
        add("mastefot", tess(R.mast_foot().translate((xm, 0.0, zr)), s))
        add("mast", tess(R.mast(0.0).translate((xm, 0.0, zr)), s))          # A1-masten, i mastefoten
        # README: salingen ca. 213 mm (modell) over foten
        add("saling", tess(R.spreaders().translate((xm, 0.0, zr + 213.0 * P.SCALE)), s))
        # masttoppen er modellert med aapningen opp (slik den printes): snus,
        # saa bunnen i hullet (1,4 mm gods) hviler paa mastens topp
        cap = R.masthead().rotate((0, 0, 0), (1, 0, 0), 180.0)
        add("masttopp", tess(cap.translate((xm, 0.0, P.MAST_ABOVE_WL + 1.4 * P.SCALE)), s))
        boom = R.boom_with_sail() if "--seil" in a else R.boom()
        add("bom", tess(boom.translate((xm, 0.0, C.deck_z(xm, 0.0) + P.BOOM_Z)), s))
        st = tess(one_stanchion(P), s)
        allst = []
        for x in P.STANCHION_X:
            y = C.deck_half_breadth(x) - P.STANCHION_INSET
            if getattr(P, "WALK", False):            # V11b: samme plass som hullet
                from hr26 import gangbord as G
                y = G.hole_y(x, P.STANCHION_INSET, 0.5 * (P.STANCHION_D + 0.1 * P.SCALE))
            for sign in (1.0, -1.0):
                allst.append(move(st, x * s, sign * y * s, surface_z(x, y, P, C, D) * s))
        add("rekkepaaler", np.concatenate(allst))

    if "--uten-stativ" not in a:
        for name, wp in ST.parts().items():
            add(name, tess(wp, s))
        add("skilt", plaque_from_plate(P))

    T = np.concatenate([t for _, t in parts])
    T = move(T, 0.0, 0.0, -T[..., 2].min())           # staar paa z = 0
    os.makedirs(os.path.dirname(out), exist_ok=True)
    write_stl(out, T)
    bb = T.reshape(-1, 3)
    print(f"skrev {out}")
    print(f"  {len(T)} trekanter, {os.path.getsize(out) / 1e6:.1f} MB, "
          f"{np.ptp(bb[:, 0]):.0f} x {np.ptp(bb[:, 1]):.0f} x {np.ptp(bb[:, 2]):.0f} mm (1:{P.SCALE:.0f})")
    print(f"ferdig ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
