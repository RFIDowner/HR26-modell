"""V10 trinn 9 «magen»: STL-er for aa se endringen i en 3D-viser.

Brukeren 14.11.2026: «jeg klarer ikke å se dette uten i en stl fil». Skriver
til export/visning/ (utenfor git). Alt er i 1:30 og i samme ramme, saa filene
ligger oppaa hverandre naar de aapnes sammen: baugen ved x = 0, kjolbunnen paa
z = 0 og senterlinjen paa y = 0. 1 mm i fila er 30 mm paa baaten.

  mage_foer.stl           skroget foer trinn 9 (01_skrog.stl fra b9d0d29^)
  mage_naa.stl            skroget naa (export/stl/01_skrog.stl)
  mage_tillegg.stl        det som er fylt inn i buken (naa minus foer), regnet
                          fra spantkurvene (en tynn del ligger inne i kjolen)
  mage_sammenligning.stl  FØR, NÅ og TILLEGG side om side, med navn
  mage_snitt.stl          skroget kuttet ved 4,85 m, der buken endret seg mest:
                          venstre halvdel FØR, hoeyre halvdel NÅ, snittflaten
                          mot betrakteren (forfra i Bambu Studio)

Endringen fyller en midje uten at baaten blir bredere eller dypere, saa
omrisset forfra, akterfra og nedenfra er nesten uendret. Den synes i
lyset paa skroget og tydeligst i snittet.

  python ../../../../tools/memcap.py --gb 4 --lock -- python mage_stl_sammenlign.py [--bilder MAPPE]

Platen dreier og flytter skroget (build.export: best_bed_angle + lay_flat).
Vinkelen finnes som heltallet som gir minst bredde, og forskyvningen med ICP
mot spantkurvene forut og akter for sonen (der foer og naa er like). Avvikene
skrives ut, og det samme gjoer forskjellen foer/naa per lengdebelte.
"""
import io
import math
import os
import subprocess
import sys
import time

import numpy as np
import trimesh
import manifold3d as mf
import mapbox_earcut as earcut

import common as c
import opt_mage as M

P = c.P
S = P.SCALE
REPO = c.REPO
OUT = os.path.join(REPO, "export", "visning")
REV_FOER = "b9d0d29^"                      # siste commit foer trinn 9
STL_PATH = "export/stl/01_skrog.stl"
FONT = "C:/Windows/Fonts/arialbd.ttf"
X0, X1 = 3450.0, 7150.0                    # kroppen for tillegget: sonen 3 578-6 996 med margin
SLOTS = (("FØR", 125.0), ("NÅ", 0.0), ("TILLEGG", -125.0))   # y-forskyvning i sammenligningen (mm, 1:30)
XCUT = 4850.0                              # snittet: midt i de stoerste endringene (z -300..300 ved 4 750-4 950)
DELTA = 1.5                                # tillegget vises der det er tykkere enn dette (mm fullskala)
RIDGE_W, RIDGE_H = 18.0, 24.0              # streken for det gamle omrisset i snittet: 0,6 x 0,8 mm i 1:30


def p_naa():
    assert tuple(P.BELLY_KNOTS) == tuple(M.KNOTS) and tuple(P.BELLY_T) == (M.T0, M.T1)
    return np.r_[P.BELLY_DEADRISE, P.BELLY_N, P.BELLY_FLARE].astype(float)


P_FOER = np.zeros(3 * len(M.KNOTS))


# ------------------------------------------------------------ STL fra platen
def rotz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0.0], [math.sin(a), math.cos(a), 0.0], [0.0, 0.0, 1.0]])


def unplate(V):
    """Platen -> baatens akser i fullskala, grovt plassert etter boksen."""
    best = None
    for ang in range(0, 91):
        e = np.ptp((V @ rotz(-ang).T)[:, 1])
        if best is None or e < best[0]:
            best = (e, ang)
    ang = best[1]
    W = V @ rotz(-ang).T
    xs = W[:, 0]
    lo, hi = xs.min(), xs.max()
    L = hi - lo

    def width(x0):
        return np.ptp(W[np.abs(xs - x0) < 0.04 * L, 1])

    flip = bool(width(lo + 0.04 * L) > width(hi - 0.04 * L))   # baugen er smalest
    if flip:
        W = W @ rotz(180.0).T
    W = W * S
    W = W + [4.0 - W[:, 0].min(), -0.5 * (W[:, 1].max() + W[:, 1].min()), -P.DRAFT - W[:, 2].min()]
    return W, ang, flip


def ref_points():
    """Punkter paa spantkurvene utenfor sonen, under listen og utenfor kjolen."""
    pts = []
    for x in np.r_[np.arange(500.0, 3300.1, 100.0), np.arange(7150.0, 7550.1, 50.0)]:
        for y, z in c.C.section(float(x), 70):
            if abs(y) > 120.0 and -300.0 < z < 550.0:
                pts += [(x, y, z), (x, -y, z)]
    return np.array(pts)


def register(mesh, pts, it=15):
    """Translasjonen t som legger mesh + t paa punktene (ICP, bare flytting)."""
    t = np.zeros(3)
    for _ in range(it):
        q = pts - t
        cp, d, _ = trimesh.proximity.closest_point(mesh, q)
        ok = d < 30.0
        step = (q[ok] - cp[ok]).mean(0)
        t = t + step
        if np.linalg.norm(step) < 1e-4:
            break
    cp, d, _ = trimesh.proximity.closest_point(mesh, pts - t)
    return t, d


def load_cad(data, pts, tag):
    m = trimesh.load(io.BytesIO(data), file_type="stl")
    W, ang, flip = unplate(np.asarray(m.vertices, float))
    cad = trimesh.Trimesh(W, np.asarray(m.faces), process=False)
    t, d = register(cad, pts)
    cad.apply_translation(t)
    print(f"  {tag}: {len(cad.faces)} trekanter, platevinkel {ang} gr{' + 180' if flip else ''},"
          f" ICP-flytt ({t[0]:+.2f}, {t[1]:+.2f}, {t[2]:+.2f}) mm, avvik mot spantkurvene"
          f" median {np.median(d):.2f} / 95 % {np.percentile(d, 95):.2f} / maks {d.max():.2f} mm (fullskala),"
          f" tett {cad.is_watertight}")
    return cad, d


# --------------------------------------------------------- tillegget (kurver)
def body(nsec=241, ndeck=24, dx=10.0):
    """Lukket skrogkropp fra spantkurvene mellom X0 og X1 (skall, dekk og endeflater)."""
    xs = np.arange(X0, X1 + 0.5 * dx, dx)
    rings = []
    for x in xs:
        sec = np.asarray(c.C.section(float(x), nsec), float)
        arc = np.asarray(c.C.deck_arc(float(x), ndeck), float)
        prt = sec[::-1].copy()
        prt[:, 0] *= -1.0
        rings.append(np.vstack([sec, arc[1:-1], prt[:-1]]))
    R = np.array(rings)
    ns, nr, _ = R.shape
    V = np.c_[np.repeat(xs, nr), R.reshape(-1, 2)]
    idx = np.arange(ns * nr).reshape(ns, nr)
    a, b = idx[:-1], np.roll(idx[:-1], -1, axis=1)
    cc, d = idx[1:], np.roll(idx[1:], -1, axis=1)
    F = [np.c_[a.ravel(), b.ravel(), d.ravel()], np.c_[a.ravel(), d.ravel(), cc.ravel()]]
    for i in (0, ns - 1):
        tri = earcut.triangulate_float64(np.ascontiguousarray(R[i]), np.array([nr], np.uint32))
        F.append(tri.reshape(-1, 3).astype(np.int64) + i * nr)
    m = trimesh.Trimesh(V, np.vstack(F), process=False)
    trimesh.repair.fix_winding(m)
    if m.volume < 0:
        m.invert()
    assert m.is_watertight and m.is_winding_consistent, "kroppen er ikke lukket"
    return m


def to_mf(m):
    man = mf.Manifold(mf.Mesh64(vert_properties=np.ascontiguousarray(m.vertices, dtype=np.float64),
                                tri_verts=np.ascontiguousarray(m.faces, dtype=np.uint64)))
    if man.status() != mf.Error.NoError:
        raise ValueError(f"ikke en lukket mangfoldighet: {man.status()}")
    return man


def from_mf(man):
    mesh = man.to_mesh64()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts, dtype=np.int64),
                           process=False)


# --------------------------------------------------------------- maalinger
def half_breadths(mesh, x, zs):
    """Stoerste |y| der planet x = konst krysser nettet, ved hoeydene zs (fullskala)."""
    seg = trimesh.intersections.mesh_plane(mesh, [1.0, 0.0, 0.0], [x, 0.0, 0.0])
    out = []
    for z in zs:
        za, zb = seg[:, 0, 2], seg[:, 1, 2]
        sel = (np.minimum(za, zb) <= z) & (np.maximum(za, zb) >= z) & (np.abs(zb - za) > 1e-9)
        if not sel.any():
            out.append(float("nan"))
            continue
        s = seg[sel]
        f = (z - s[:, 0, 2]) / (s[:, 1, 2] - s[:, 0, 2])
        y = s[:, 0, 1] + f * (s[:, 1, 1] - s[:, 0, 1])
        out.append(float(np.abs(y).max()))
    return np.array(out)


def compare(foer, naa, n=25000):
    rng = np.random.default_rng(1)
    q = naa.vertices[rng.choice(len(naa.vertices), n, replace=False)]
    _, d, _ = trimesh.proximity.closest_point(foer, q)
    print("  forskjell naa -> foer (fullskala mm), per lengdebelte:")
    rows = []
    for b0 in np.arange(0.0, 8000.0, 250.0):
        sel = (q[:, 0] >= b0) & (q[:, 0] < b0 + 250.0)
        if sel.any():
            rows.append((b0, int(sel.sum()), float(d[sel].max()), float(np.percentile(d[sel], 99))))
            print(f"    x {b0:5.0f}-{b0 + 250:5.0f}: {sel.sum():5d} pkt  maks {d[sel].max():6.2f}"
                  f"  99 % {np.percentile(d[sel], 99):6.2f}")
    return rows


# --------------------------------------------------------------------- navn
def label(text, size=9.0, h=0.8):
    import cadquery as cq
    sh = cq.Workplane("XY").text(text, size, h, fontPath=FONT, halign="center", valign="center").val()
    vs, ts = sh.tessellate(0.01, 0.2)
    return trimesh.Trimesh(np.array([(v.x, v.y, v.z) for v in vs]), np.array(ts, dtype=np.int64))


def curve_polygon(x, n=400, ndeck=40):
    """Spantet ved x fra kurvene (kanobunnen til den virtuelle dekkskanten), fylt, i (y, z)."""
    from shapely.geometry import Polygon
    sec = np.asarray(c.C.section(float(x), n), float)
    arc = np.asarray(c.C.deck_arc(float(x), ndeck), float)
    prt = sec[::-1].copy()
    prt[:, 0] *= -1.0
    return Polygon(np.vstack([sec, arc[1:-1], prt[:-1]])).buffer(0)


def cad_section(mesh, x):
    """Materialet i snittet x = konst av CAD-nettet, som shapely-flater i (y, z)."""
    from shapely.ops import unary_union
    seg = trimesh.intersections.mesh_plane(mesh, [1.0, 0.0, 0.0], [x, 0.0, 0.0])
    path = trimesh.load_path(np.ascontiguousarray(seg[:, :, 1:]))
    return unary_union(list(path.polygons_full)).buffer(0)


def cap_mesh(poly, x, normal_sign=-1.0):
    """Trianguler en (multi)flate i (y, z) og legg den i planet x, med normalen langs normal_sign * x."""
    polys = list(poly.geoms) if hasattr(poly, "geoms") else [poly]
    out = []
    for p in polys:
        if p.is_empty or p.area < 1.0:
            continue
        v2, f = trimesh.creation.triangulate_polygon(p, engine="earcut")
        V = np.c_[np.full(len(v2), x), v2]
        m = trimesh.Trimesh(V, f, process=False)
        if np.sign(m.face_normals[:, 0].mean()) != np.sign(normal_sign):
            m.invert()
        out.append(m)
    return trimesh.util.concatenate(out)


def snitt(foer, naa, x_cut):
    """Akterdelen fra x_cut med fylt snittflate: styrbord (y >= 0) fra FØR, babord fra NÅ.

    Flaten er unionen av kurvespantet (kanobunnen fylt til dekket) og CAD-materialet
    (kjolen, listen og karmen), saa skroget ser massivt ut i snittet."""
    from shapely.geometry import box
    parts = []
    for mesh, p, side in ((foer, P_FOER, 1.0), (naa, p_naa(), -1.0)):
        M.install(p)
        face = curve_polygon(x_cut).union(cad_section(mesh, x_cut)).buffer(0)
        half = face.intersection(box(0.0, -5000.0, 5000.0, 5000.0) if side > 0 else box(-5000.0, -5000.0, 0.0, 5000.0))
        aft = trimesh.intersections.slice_mesh_plane(mesh, [1.0, 0.0, 0.0], [x_cut, 0.0, 0.0], cap=False)
        aft = trimesh.intersections.slice_mesh_plane(aft, [0.0, side, 0.0], [0.0, 0.0, 0.0], cap=False)
        parts += [aft, cap_mesh(half, x_cut, -1.0)]
        print(f"    snitt {x_cut:.0f} {'FOER styrbord' if side > 0 else 'NAA babord'}: flate {half.area / 1e6:.3f} m2")
    # streken: FØR-spantet (kjolpunktet til dekkskanten) speilet over paa NÅ-halvdelen
    M.install(P_FOER)
    old = np.asarray(c.C.section(x_cut, 400), float)
    M.install(p_naa())
    old[:, 0] *= -1.0
    parts.append(ridge(old, x_cut))
    new = np.asarray(c.C.section(x_cut, 400), float)
    for z in (-300.0, -200.0, -100.0, 0.0):
        yo = np.interp(z, old[:, 1], -old[:, 0]) if np.all(np.diff(old[:, 1]) > 0) else float("nan")
        yn = np.interp(z, new[:, 1], new[:, 0]) if np.all(np.diff(new[:, 1]) > 0) else float("nan")
        print(f"    snitt {x_cut:.0f} z {z:5.0f}: halvbredde foer {yo:6.1f}, naa {yn:6.1f} (streken {yn - yo:+5.1f} mm inne)")
    return trimesh.util.concatenate(parts)


def ridge(line_yz, x, width=None, height=None):
    """En smal list langs linja (y, z) foran snittflaten i x (mot -x)."""
    from shapely.geometry import LineString
    width = RIDGE_W if width is None else width
    height = RIDGE_H if height is None else height
    poly = LineString(line_yz).buffer(width / 2.0, cap_style=2, join_style=1)
    m = trimesh.creation.extrude_polygon(poly, height + 1.0)
    V = np.asarray(m.vertices, float)
    m = trimesh.Trimesh(np.c_[x + 1.0 - V[:, 2], V[:, 0], V[:, 1]], np.asarray(m.faces), process=False)
    if m.volume < 0:
        m.invert()
    return m


def to_model(m, z0):
    V = np.asarray(m.vertices, float)
    return trimesh.Trimesh(np.c_[V[:, 0] / S, V[:, 1] / S, (V[:, 2] - z0) / S], np.asarray(m.faces), process=False)


# ------------------------------------------------------------------- bilder
def render(meshes, path, azim, elev, W=1600, H=900, zoom=1.0, focus=None):
    import vtk
    from vtk.util import numpy_support as ns
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    lo = np.min([m.bounds[0] for m, _ in meshes], 0)
    hi = np.max([m.bounds[1] for m, _ in meshes], 0)
    for m, col in meshes:
        pts = vtk.vtkPoints()
        pts.SetData(ns.numpy_to_vtk(np.ascontiguousarray(m.vertices, dtype=np.float64), deep=True))
        F = np.asarray(m.faces, dtype=np.int64)
        cells = vtk.vtkCellArray()
        cells.SetCells(len(F), ns.numpy_to_vtkIdTypeArray(np.c_[np.full(len(F), 3), F].ravel(), deep=True))
        pd = vtk.vtkPolyData()
        pd.SetPoints(pts)
        pd.SetPolys(cells)
        nrm = vtk.vtkPolyDataNormals()
        nrm.SetInputData(pd)
        nrm.SetFeatureAngle(50.0)
        mp = vtk.vtkPolyDataMapper()
        mp.SetInputConnection(nrm.GetOutputPort())
        ac = vtk.vtkActor()
        ac.SetMapper(mp)
        ac.GetProperty().SetColor(*col)
        ac.GetProperty().SetSpecular(0.25)
        ac.GetProperty().SetSpecularPower(30)
        ren.AddActor(ac)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(W, H)
    ctr = 0.5 * (lo + hi) if focus is None else np.asarray(focus, float)
    a, e = math.radians(azim), math.radians(elev)
    dirn = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*ctr)
    cam.SetPosition(*(ctr + dirn * 3.0 * np.linalg.norm(hi - lo)))
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.SetFocalPoint(*ctr)
    cam.Zoom(zoom)
    ren.ResetCameraClippingRange()
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(path)
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()


# --------------------------------------------------------------------- main
def main():
    bilder = sys.argv[sys.argv.index("--bilder") + 1] if "--bilder" in sys.argv else None
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    pts = ref_points()
    print(f"Referansepunkter paa spantkurvene: {len(pts)}")
    blob_foer = subprocess.run(["git", "show", f"{REV_FOER}:{STL_PATH}"], cwd=REPO, capture_output=True,
                               check=True).stdout
    blob_naa = open(os.path.join(REPO, STL_PATH), "rb").read()
    foer, d_foer = load_cad(blob_foer, pts, "foer")
    naa, d_naa = load_cad(blob_naa, pts, "naa ")
    rows = compare(foer, naa)

    # tillegget fra spantkurvene: kropp naa minus kropp foer
    M.install(P_FOER)
    kf = body()
    zs = (-380.0, -300.0, -200.0, -100.0, 0.0, 100.0, 300.0, 600.0)
    M.install(p_naa())
    kn = body()
    A, B = to_mf(kn), to_mf(kf)
    add, rem = A - B, B - A
    print(f"  kurvekropper {X0:.0f}-{X1:.0f}: foer {B.volume() / 1e9:.4f} m3, naa {A.volume() / 1e9:.4f} m3;"
          f" tillegg {add.volume() / 1e6:.1f} l, fjernet {rem.volume() / 1e6:.2f} l (fullskala)")
    if rem.volume() > 0:
        rb = rem.bounding_box()
        print(f"  fjernet ligger i x {rb[0]:.0f}-{rb[3]:.0f}, z {rb[2]:.0f}-{rb[5]:.0f}")
    # Kjolen trekkes ikke fra: med CAD-nettet ble tillegget stripete (fasettene og
    # vinduet skar i de tynne delene). Den tynne delen inne i kjolen synes ikke.
    # Der endringen er under ca. 1 mm, krysser de to kurvenettene hverandre i
    # striper (sampling), saa foer-kroppen blaases opp DELTA foer differansen.
    try:
        add = A - to_mf(trimesh.Trimesh(kf.vertices + kf.vertex_normals * DELTA, kf.faces, process=False))
        print(f"  tillegg tykkere enn {DELTA:.1f} mm: {add.volume() / 1e6:.1f} l")
    except ValueError as e:
        print(f"  (oppblaast foer-kropp ble ikke lukket: {e}; bruker hele tillegget)")
    try:
        slank = B - to_mf(trimesh.Trimesh(kn.vertices + kn.vertex_normals * DELTA, kn.faces, process=False))
        for p in slank.decompose():
            if p.volume() > 1e3:
                rb = p.bounding_box()
                _, ts, _ = trimesh.proximity.closest_point(kn, from_mf(p).vertices)
                print(f"  slankere (mer enn {DELTA:.1f} mm): {p.volume() / 1e6:.2f} l i x {rb[0]:.0f}-{rb[3]:.0f},"
                      f" |y| {min(abs(rb[1]), abs(rb[4])):.0f}-{max(abs(rb[1]), abs(rb[4])):.0f},"
                      f" z {rb[2]:.0f}-{rb[5]:.0f}, tykkest {ts.max():.1f} mm")
    except ValueError:
        pass
    pieces = add.decompose()
    keep = [p for p in pieces if p.volume() > 1e3]      # bort med smuler under 1 cm3 i fullskala
    print(f"  tillegget: {len(pieces)} biter, beholder {len(keep)} (volum > 1 cm3)")
    till_mf = mf.Manifold.compose(keep).simplify(0.2)
    till = from_mf(till_mf)
    _, th, _ = trimesh.proximity.closest_point(kf, till.vertices)
    print(f"  tillegget: x {till.bounds[0][0]:.0f}-{till.bounds[1][0]:.0f}, z {till.bounds[0][2]:.0f}-"
          f"{till.bounds[1][2]:.0f}, tykkest {th.max():.1f} mm fullskala ({th.max() / S:.2f} mm i 1:30)")
    if rem.volume() > 0:
        _, thr, _ = trimesh.proximity.closest_point(kn, from_mf(rem).vertices)
        print(f"  fjernet: tykkest {thr.max():.1f} mm fullskala")

    # halvbredder: STL foer/naa og kurvene
    print("  halvbredde (fullskala mm)        STL foer  STL naa  endring | kurve foer  kurve naa  endring")
    checks = [(3000.0, 0.0), (4750.0, -300.0), (4850.0, -200.0), (4900.0, -100.0), (4900.0, 0.0),
              (4950.0, 100.0), (4950.0, 300.0), (6000.0, -100.0), (7300.0, 0.0)]
    for x, z in checks:
        a1, b1 = half_breadths(foer, x, [z])[0], half_breadths(naa, x, [z])[0]
        if X0 < x < X1:
            a2, b2 = half_breadths(kf, x, [z])[0], half_breadths(kn, x, [z])[0]
        else:
            a2 = b2 = float("nan")
        print(f"    x {x:5.0f} z {z:5.0f}:           {a1:8.1f} {b1:8.1f} {b1 - a1:+8.1f} | {a2:10.1f} {b2:10.1f} {b2 - a2:+8.1f}")

    # 1:30, kjolbunnen paa z = 0
    z0 = -P.DRAFT
    mf_ = to_model(foer, z0)
    mn_ = to_model(naa, z0)
    mt_ = to_model(till, z0)
    for name, m in (("mage_foer.stl", mf_), ("mage_naa.stl", mn_), ("mage_tillegg.stl", mt_)):
        m.export(os.path.join(OUT, name))
    sl = []
    for (name, dy), m in zip(SLOTS, (mf_, mn_, mt_)):
        mm = m.copy()
        mm.apply_translation([0.0, dy, 0.0])
        lab = label(name)
        lab.apply_translation([-38.0, dy, 0.0])
        sl += [mm, lab]
    comb = trimesh.util.concatenate(sl)
    comb.export(os.path.join(OUT, "mage_sammenligning.stl"))

    # snittet der buken endret seg mest: FØR til venstre, NÅ til hoeyre, flaten mot -y
    sn = to_model(snitt(foer, naa, XCUT), z0)
    sn.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2.0, [0.0, 0.0, 1.0]))
    sn.apply_translation([0.0, -sn.bounds[0][1], 0.0])
    labs = []
    for text, xx, yy, size in (("FØR", -22.0, -12.0, 8.0), ("NÅ", 22.0, -12.0, 8.0),
                               ("STREKEN = FØR", 22.0, -21.0, 4.0),
                               (f"SNITT {XCUT / 1000:.2f} M".replace(".", ","), 0.0, -32.0, 6.0)):
        lab = label(text, size)
        lab.apply_translation([xx, yy, 0.0])
        labs.append(lab)
    snm = trimesh.util.concatenate([sn] + labs)
    snm.export(os.path.join(OUT, "mage_snitt.stl"))
    for name in ("mage_foer.stl", "mage_naa.stl", "mage_tillegg.stl", "mage_sammenligning.stl", "mage_snitt.stl"):
        fn = os.path.join(OUT, name)
        m = trimesh.load(fn)
        b = m.bounds
        print(f"  {fn}: {os.path.getsize(fn) / 1e6:.1f} MB, {len(m.faces)} trekanter,"
              f" x {b[0][0]:.1f}..{b[1][0]:.1f}, y {b[0][1]:.1f}..{b[1][1]:.1f}, z {b[0][2]:.2f}..{b[1][2]:.2f} mm,"
              f" tett {m.is_watertight}")

    if bilder:
        os.makedirs(bilder, exist_ok=True)
        grey, red, blue = (0.80, 0.80, 0.78), (0.85, 0.15, 0.10), (0.55, 0.65, 0.85)
        render([(comb, grey)], os.path.join(bilder, "sammenligning_under.png"), -70, -35)
        render([(comb, grey)], os.path.join(bilder, "sammenligning_akter.png"), 20, -25)
        focus = [5000.0 / S, 0.0, 30.0]
        for tag, m in (("foer", mf_), ("naa", mn_)):
            render([(m, grey)], os.path.join(bilder, f"mage_{tag}_under.png"), -60, -30, zoom=2.2, focus=focus)
            render([(m, grey)], os.path.join(bilder, f"mage_{tag}_side.png"), -90, -8, zoom=2.0, focus=focus)
        render([(mf_, grey), (mt_, red)], os.path.join(bilder, "foer_med_tillegg_under.png"), -60, -30, zoom=2.2,
               focus=focus)
        render([(mf_, grey), (mt_, red)], os.path.join(bilder, "foer_med_tillegg_akter.png"), 15, -20, zoom=1.6,
               focus=focus)
        render([(mt_, red)], os.path.join(bilder, "tillegg_alene.png"), -60, -30, zoom=1.4)
        render([(snm, grey)], os.path.join(bilder, "snitt_forfra.png"), -90, 12, zoom=1.3)
        render([(snm, grey)], os.path.join(bilder, "snitt_skraatt.png"), -60, 30, zoom=1.2)
        print(f"  bilder i {bilder}")
    print(f"Ferdig paa {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
