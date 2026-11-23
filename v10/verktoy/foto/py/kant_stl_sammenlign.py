"""V11 «gangbordet»: STL-er for aa se endringen av kanten akter i en 3D-viser.

Brukeren ser formendringer i STL, ikke i bilder (14.11.2026). Skriver til
export/visning/ (utenfor git), alt i 1:30 og i samme ramme: baugen ved x = 0,
kjolbunnen paa z = 0 og senterlinjen paa y = 0.

  kant_foer.stl    skroget foer V11 (V10, med den skraa skulderen)
  kant_naa.stl     skroget naa (flatt gangbord og loddrett, rundet kant)
  kant_snitt.stl   hekken aktenfor 6,7 m (rekkepaalen akter), snittflaten
                   forover: babord halvdel FOER, styrbord halvdel NAA

  python ../../../../tools/memcap.py --gb 3 -- python kant_stl_sammenlign.py FOER.stl [NAA.stl]

FOER.stl og NAA.stl er plate-STL-er (01_skrog.stl, dreid paa platen). NAA er
export/stl/01_skrog.stl hvis den ikke er gitt.
"""
import os
import sys

import numpy as np
import trimesh

import kd_render as K

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OUT = os.path.join(REPO, "export", "visning")
XCUT = 6700.0          # fullskala: rekkepaalen akter, midt i den stoerste endringen


def boat_frame(path):
    """Plate-STL -> baatramme i 1:30 (baugen x 0, kjolbunnen z 0, senterlinjen y 0)."""
    m = trimesh.load(path)
    best = None
    for ang in (45.0, -45.0, 135.0, -135.0):
        Vr = K._rot(m.vertices, ang)
        ext = Vr.max(0) - Vr.min(0)
        if best is None or ext[0] > best[1][0]:
            best = (ang, ext)
    V = K._rot(m.vertices, best[0])
    xs = V[:, 0]
    lo, hi = xs.min(), xs.max()

    def wn(x0):
        s = np.abs(xs - x0) < 0.05 * (hi - lo)
        return np.ptp(V[s, 1])
    if wn(lo + 0.05 * (hi - lo)) > wn(hi - 0.05 * (hi - lo)):
        V[:, 0] *= -1.0
        V[:, 1] *= -1.0
    V = V - [V[:, 0].min(), 0.5 * (V[:, 1].max() + V[:, 1].min()), V[:, 2].min()]
    return trimesh.Trimesh(V, m.faces, process=True)


def half_aft(m, side):
    """Delen aktenfor XCUT, bare den ene siden (side +1 styrbord, -1 babord),
    med lukkede snittflater."""
    x = XCUT / 30.0 - 4.0 / 30.0          # byggerammen har baugen paa x 4
    a = m.slice_plane([x, 0, 0], [1, 0, 0], cap=True)
    return a.slice_plane([0, 0, 0], [0, side, 0], cap=True)


def main():
    foer = boat_frame(sys.argv[1])
    naa = boat_frame(sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "export", "stl", "01_skrog.stl"))
    os.makedirs(OUT, exist_ok=True)
    foer.export(os.path.join(OUT, "kant_foer.stl"))
    naa.export(os.path.join(OUT, "kant_naa.stl"))
    snitt = trimesh.util.concatenate([half_aft(foer, -1.0), half_aft(naa, 1.0)])
    snitt.export(os.path.join(OUT, "kant_snitt.stl"))
    for n in ("kant_foer.stl", "kant_naa.stl", "kant_snitt.stl"):
        p = os.path.join(OUT, n)
        print(f"  {n:<16s} {os.path.getsize(p) / 1e6:5.1f} MB")


if __name__ == "__main__":
    main()
