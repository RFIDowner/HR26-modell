"""Ny _section_wire og hull_solid i hull.py (beholder CRLF)."""
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
fn = WT + "/hr26/hull.py"
src = open(fn, "rb").read().decode("utf-8").replace("\r\n", "\n")

old_hdr = 'STERN_STATIONS = (7850.0, 7910.0)   # ekstra spant der hekken runder av\n'
new_hdr = ('STERN_STATIONS = (7850.0, 7910.0)   # ekstra spant der hekken runder av\n'
           'BOW_STATIONS = (2.0, 6.0)           # ekstra spant der dekkslinjen rundes av i nesen\n')
assert old_hdr in src
src = src.replace(old_hdr, new_hdr, 1)

a = src.index("def _section_wire(")
b = src.index("def transom_cutter(")
wire = '''def _section_wire(x: float, n_pts: int = 28) -> cq.Wire:
    """Lukket, speilsymmetrisk spant ved stasjon x, glatt rundt hele.

    Fem kanter: siden styrbord (kjol -> avrundet dekkskant), avrundingen,
    dekksbuen tvers over, avrundingen og siden babord. Kantene moetes med
    felles tangent, saa dekkskanten blir rund (C.section_parts) i stedet
    for en skarp knekk - en OCC-fillet paa den ferdige loften feiler der.

    Hver kant samples med de samme parameterverdiene og endetangentene ved
    alle stasjoner. Da faar splinene samme knutevektor, og loften blir en
    flate med faa knuter. Foer hadde hvert spant sine egne (over 1 000
    knuter paa tvers), og STL-en fikk lange, tynne trekanter.
    """
    sp = C.section_parts(x, n_side=max(n_pts, 28))
    side, corner, deck = sp["side"], sp["corner"], sp["deck"]
    ty, tz = sp["t_side"]
    dy, dz = sp["t_deck"]
    ps = [float(v) for v in sp["side_par"]]
    pc = [float(v) for v in sp["corner_par"]]
    pd = [float(v) for v in sp["deck_par"]]

    def pts(arr, sgn=1.0):
        return [cq.Vector(x, sgn * float(y), float(z)) for y, z in arr]

    def tan(vy, vz):
        return cq.Vector(0.0, vy, vz)

    def rev(par):
        return [1.0 - v for v in reversed(par)]

    edges = [
        cq.Edge.makeSpline(pts(side), tangents=[tan(1.0, 0.0), tan(ty, tz)], parameters=ps),
        cq.Edge.makeSpline(pts(corner), tangents=[tan(ty, tz), tan(dy, dz)], parameters=pc),
        cq.Edge.makeSpline(pts(deck), tangents=[tan(dy, dz), tan(dy, -dz)], parameters=pd),
        cq.Edge.makeSpline(pts(corner[::-1], -1.0), tangents=[tan(dy, -dz), tan(ty, -tz)],
                           parameters=rev(pc)),
        cq.Edge.makeSpline(pts(side[::-1], -1.0), tangents=[tan(ty, -tz), tan(1.0, 0.0)],
                           parameters=rev(ps)),
    ]
    return cq.Wire.assembleEdges(edges)


'''
src = src[:a] + wire + src[b:]

a = src.index("    xs = C.stations(n_stations)\n")
b = src.index("    wires = [_section_wire(x, n_pts) for x in xs]\n")
stn = '''    xs = C.stations(n_stations)
    # unnga degenerte spant helt i endene; tettere spant i nesen, der
    # dekkslinjen rundes av, og rundt hekken
    xs = [x for x in xs if 10.0 < x < P.LOA - 4.0]
    xs = sorted(set(list(BOW_STATIONS) + xs + list(STERN_STATIONS) + [P.LOA - 2.0]))
    xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 3.0]

'''
src = src[:a] + stn + src[b:]
src = src.replace("def hull_solid(n_stations: int = 34, n_pts: int = 24) -> cq.Solid:",
                  "def hull_solid(n_stations: int = 34, n_pts: int = 28) -> cq.Solid:", 1)
open(fn, "wb").write(src.replace("\n", "\r\n").encode("utf-8"))
print("ok")
