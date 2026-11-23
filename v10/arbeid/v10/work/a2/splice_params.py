"""Bytter tverrsnittsparametrene i params.py (beholder CRLF og UTF-8)."""
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
fn = WT + "/hr26/params.py"
src = open(fn, "rb").read().decode("utf-8").replace("\r\n", "\n")
a = src.index("# Fyldighetseksponent for tverrsnittene")
b = src.index("HULL_WALL = ")
new = '''# Hvert spant er EN glatt, konveks kurve fra kjolen til dekkskanten
# (curves.section): hjoernet mellom en bunnlinje gjennom kjolpunktet og en
# sidelinje gjennom dekkskanten rundes av med en superellipse. Kjolpunkt,
# dekkskant og spring ligger fast; vannlinjebredden blir et resultat.
# Tabellene er (stasjon i andel av LOA fra baugen, verdi); mellom punktene
# en monoton kubisk kurve (PCHIP), uten oversving. Bildene IMG_9388/9395
# (baugen) og IMG_9389/9391 (hekken) viser buede, utfallende sider og myk
# slag. Foer V10: superellipse under DWL og hul side over, med knekk i DWL
# og en vannlinjebredde (WATERPLANE, WL_BEAM_FRACTION) uten kilde.
SECTION_FLARE = [            # utfall ved dekkskanten, grader fra loddrett
    (0.00, 24.0), (0.10, 19.0), (0.20, 13.5), (0.30, 11.0), (0.45, 9.5),
    (0.60, 9.0), (0.75, 9.0), (0.90, 10.0), (1.00, 10.5),
]
SECTION_N = [                # superellipsens eksponent: 2 = ellipse,
    (0.00, 2.4), (0.15, 3.1), (0.35, 3.4),       # hoyere = fastere slag
    (0.60, 3.5), (0.80, 3.3), (1.00, 3.1),
]
SECTION_DEADRISE = [         # bunnreisning ved kjolen, grader: V forut,
    (0.00, 45.0), (0.127, 15.0), (0.20, 4.0),     # flat kanobunn akter
    (0.27, 0.0), (1.00, 0.0),
]
DECK_EDGE_R = 25.0           # avrundet dekkskant, bygget inn i spantene
                             # (0,83 mm i 1:30; OCC-fillet feiler her)
STEM_R = 20.0                # stevnens radius i vannlinjene (0,67 mm i 1:30)
BOW_NOSE_L = 15.0            # dekkslinjen rundes av over de forreste mm

'''
src = src[:a] + new + src[b:]
open(fn, "wb").write(src.replace("\n", "\r\n").encode("utf-8"))
print("ok")
