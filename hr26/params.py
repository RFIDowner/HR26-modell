"""
Alle mål for HR 26-modellen.

Målene i FULL SKALA er i millimeter på den virkelige båten.
`SCALE` styrer nedskaleringen til modellen; alt annet avledes av den.

Kilder:
  * Hallberg Rassy katalog 1981 og HR 26-brosjyre (hovedmål)
  * Profil 1:50 og dekksplan 1:50 fra brosjyren (kurver, se data/)
  * Fotogrammetri-scan av en virkelig HR 26 (dekkslayout, referanse)
  * Fotografier av båten på land og fortøyd
"""

# ---------------------------------------------------------------- skala
SCALE = 30.0          # 1:30
MM = 1.0 / SCALE      # ganger fullskala-mm for å få modell-mm

# ------------------------------------------------- hovedmål (fullskala)
LOA = 7950.0          # lengde over alt
LWL = 6700.0          # vannlinjelengde
BEAM = 2680.0         # største bredde
DRAFT = 1400.0        # dypgang
DISPLACEMENT_T = 2.50  # deplasement, tonn
BALLAST_T = 1.10      # kjølvekt, tonn
SAIL_AREA = 32.0      # m^2
MAST_ABOVE_WL = 12000.0   # masthøyde over vannlinjen

# vannlinjen starter/slutter (målt fra baugen, fra profiltegningen)
LWL_FWD = 1008.0
LWL_AFT = LWL_FWD + LWL

# --------------------------------------------------------- skrogseksjon
# Hvert spant er EN glatt, konveks kurve fra kjolen til dekkskanten
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

HULL_WALL = 1.5 * SCALE    # skallveggtykkelse, uttrykt i fullskala-mm
DECK_THICK = 1.6 * SCALE

# ---------------------------------------------------------------- kjøl
KEEL_LE_ROOT = 3380.0   # forkant ved rot (fra baugen)
KEEL_TE_ROOT = 5800.0   # bakkant ved rot
KEEL_LE_TIP = 4894.0    # forkant ved bunn
KEEL_TE_TIP = 5694.0    # bakkant ved bunn
KEEL_TIP_Z = -DRAFT
KEEL_ROOT_T = 320.0     # tykkelse ved rot
KEEL_TIP_T = 175.0      # tykkelse ved bunn
KEEL_FILLET = 90.0      # avrunding mot skroget: hoyden paa utvidelsen nederst ved roten
                        # (kjolen blir 0,75 x dette bredere paa hver side der den moeter skroget)

# Kanobunnen paa senterlinjen der profiltegningen ikke viser den: bak kjolen,
# og akter der propellen og roret dekker den (det sporede omrisset der er
# propell og ror, ikke bunnen). Verdiene er V9-kurven; de holder kjolroten
# (bottom_z midt paa roten) og akterspeilets underkant (ca. -250) der de var.
# Fra 7 650 fortsetter de V9-kurvens jevne stigning: V9 knakk ved 7 800, en
# endeeffekt av glattingen (de to siste tabellpunktene ble ikke glattet).
# curves.bottom_z legger en glatt spline gjennom disse, forstevnen og den
# sporede forfoten. (x fra baugen, z over DWL)
CANOE_BOTTOM_HIDDEN = [
    (3250.0, -455.3), (3500.0, -480.0), (3750.0, -496.5), (4000.0, -504.1),
    (4250.0, -505.6), (4500.0, -503.0), (4590.0, -501.4), (4750.0, -498.6),
    (5000.0, -494.7), (5250.0, -492.4), (5500.0, -492.2), (5750.0, -492.5),
    (6000.0, -491.3), (6250.0, -485.0), (6500.0, -471.5), (6750.0, -448.8),
    (7000.0, -414.2), (7250.0, -368.7), (7500.0, -314.6), (7650.0, -279.5),
    (7800.0, -240.6), (7950.0, -199.1),
]

# ------------------------------------------------------------ hekk/akterspeil
# Hekken er rundet i plan (dekksplanen 1:50): dekkskanten gaar fra 890 mm
# halvbredde ved x = 7700 gjennom et hjoerne med radius ca. 290 over i
# akterspeilets overkant, som er svakt buet i plan (radius ca. 3 000) og
# naar 7 950 paa senterlinjen. Akterspeilet heller 8,3 grader med toppen
# lengst akter (profilen: krysser DWL ved 7 806, dekkshoeyde ved 7 945).
# Skroget loftes rett akterover forbi akterspeilet, ca. 600 mm bredt
# aktenfor hjoernet, og akterspeilets flate kappes ut av loften.
STERN_OUTLINE = [            # dekkskantens halvbredde (x, y) maalt i dekksplanen
    (7300.0, 995.0), (7400.0, 968.0), (7500.0, 944.0), (7600.0, 916.0),
    (7700.0, 890.0), (7750.0, 866.0), (7800.0, 835.0), (7820.0, 812.0),
    (7840.0, 773.0), (7860.0, 730.0), (7880.0, 650.0), (7891.0, 605.0),
]
STERN_HOLD_SLOPE = 0.5       # halvbredden faller saa mye per mm aktenfor hjoernet
TRANSOM_WL_X = 7806.0        # akterspeilet krysser DWL her, paa senterlinjen
TRANSOM_RAKE = 0.146         # helning dx/dz - toppen lengst akter (8,3 grader)
TRANSOM_CAMBER_R = 3050.0    # akterspeilets bue i plan
# Hjoernene mellom skrogsiden og akterspeilet er rundet (fotoene akterfra og
# skraatt akterfra). Rundingen bygges inn i kuttet (hull.transom_cutter): i
# hvert vannrette snitt tangerer en bue akterspeilet TRANSOM_CORNER_L fra
# hjoernet og moeter skrogsiden med en liten restknekk. Baandet er dermed like
# bredt hele veien opp. Under vannlinjen trappes rundingen ned, og bunnens
# kant mot akterspeilet blir skarp, som paa baaten.
TRANSOM_CORNER_L = 110.0     # rundingens bredde paa akterspeilet (0 = skarpt hjoerne som foer)
TRANSOM_CORNER_EXIT = 7.0    # restknekk mot skrogsiden, grader (gir et robust kutt)
TRANSOM_CORNER_Z = (-220.0, -100.0)   # rundingen bygges opp mellom disse hoydene

# ----------------------------------------------------------------- ror
# Akterhengt ror. Forkanten foelger akterspeilet med en liten klaring, og
# tappene paa forkanten gaar inn i akterspeilet under vannlinjen.
RUDDER_GAP = 15.0       # klaring mellom rorets forkant og akterspeilet
RUDDER_TE_X = 8150.0    # bakkanten er loddrett (profilen), saa korden vokser nedover
RUDDER_TOP_Z = -60.0
RUDDER_BOT_Z = -1094.0
RUDDER_T = 90.0
RUDDER_X = TRANSOM_WL_X + TRANSOM_RAKE * RUDDER_TOP_Z + RUDDER_GAP   # forkant ved topp
RUDDER_RAKE = TRANSOM_RAKE * (RUDDER_BOT_Z - RUDDER_TOP_Z)   # forkanten forover nedover, som akterspeilet

# ------------------------------------------------------------ dekkskant
# Dekkskanten er den tynne linjen over fenderlisten i profiltegningen 1:50,
# der rekka staar. Skrogsiden fortsetter opp forbi listen: 130 mm over
# listens senter i baugen, 270 midtskips og ca. 200 i hekken. Listen er en
# list utenpaa (STRAKE_*). (x fra baugen, z over DWL.) Aktenfor 6400 ligger
# cockpitkarmen over linjen; aktenfor 7000 er den oevre linjen rorkulten.
DECK_EDGE_Z = [
    (0.0, 1204.0), (1000.0, 1204.0), (2000.0, 1200.0), (2500.0, 1175.0),
    (3000.0, 1150.0), (3750.0, 1122.0), (4200.0, 1115.0), (4500.0, 1105.0),
    (5000.0, 1095.0), (5500.0, 1085.0), (6000.0, 1080.0), (6500.0, 1075.0),
    (7000.0, 1056.0), (7200.0, 1040.0), (7400.0, 1020.0), (7600.0, 992.0),
    (7800.0, 962.0), (7950.0, 940.0),
]
# Springet er en utjevnende spline gjennom DECK_EDGE_Z (curves.sheer_z):
# straffen paa krumningen. 4e7 gir maks 5 mm avvik fra punktene og fjerner
# S-bukten tabellen har mellom 3 000 og 4 500 (2 vendepunkter i stedet for 5).
SHEER_SMOOTHING = 4.0e7
DECK_CAMBER = 30.0           # bue paa dekket, senter over kant (fordekkets
                             # silhuett ligger 15-25 mm over dekkskanten)

# ------------------------------------------------------------ ruff/dekk
# Hoyder og lengder er maalt ut av profiltegningen 1:50, bredder av
# dekksplanen - se data/deckhouse_features.json. z over DWL, x fra baugen.
# Fordekket er flatt helt fram; den lave "forruffen" i tegningens silhuett
# (1216-1226) er dekket selv.

# ruffens skraa front, fra dekket opp til taket
STEP_X0 = 2200.0
STEP_X1 = 2330.0

# ruff: topp (x, z); bredden er dekkshalvbredden minus sidedekket
COACH_X0 = STEP_X1
COACH_X1 = 5625.0            # nedgangsskott / ruffens bakkant
COACH_TOP = [(2330.0, 1350.0), (3000.0, 1375.0), (4200.0, 1385.0), (5625.0, 1375.0)]
COACH_TOP_BLEND = 300.0      # knekkene i COACH_TOP rundes av over +-300 mm; mastefoten
                             # (3 400) ligger utenfor, saa masten staar som foer
SIDEDECK = 210.0             # sidedekk mellom ruffside og dekkskant (plan)
COACH_FRONT_R = 700.0        # rundet front i plan
COACH_MIN_HALF_W = 220.0
COACH_RAD = 140.0            # hjorneradius akter, i plan
COACH_ROOF_CAMBER = 58.0     # takets bue, senter over kant
# Ruffens profil paa tvers av omrisset: en skraa side fra dekket som runder
# av over i taket. Omrisset (SIDEDECK, COACH_FRONT_R) er foten mot dekket.
COACH_FRONT_ANGLE = 45.0     # fronten, fra dekket ved STEP_X0 til taket ved STEP_X1
COACH_SIDE_ANGLE = 78.0      # sidene heller 12 grader innover (fotoene)
COACH_EDGE_R = 40.0          # takkantens radius langs sidene (1,3 mm i 1:30)
COACH_FRONT_EDGE_R = 60.0    # takkantens radius over fronten

# luker og ventiler paa taket (x_fra, x_til, bredde, hoyde over tak)
FOREHATCH = (2490.0, 2980.0, 500.0, 40.0)
SLIDE_HATCH = (4352.0, 4940.0, 620.0, 60.0)
HATCH_RAD = 70.0             # lukenes hjorneradius i plan
HATCH_EDGE_R = 20.0          # avrunding av lukenes overkant
VENT_D, VENT_H = 150.0, 45.0
VENTS = [(1900.0, "deck"), (3894.0, "roof")]

# nedgang i ruffens bakkant: bredde, dybde inn i skottet, terskel over dekket
COMPANION_W = 620.0
COMPANION_DEPTH = 180.0
COMPANION_SILL = 60.0        # over dekket paa senterlinjen ved ruffens bakkant

# Vinduet sitter i skrogsiden, i baandet mellom fenderlisten og dekkskanten,
# slik profiltegningen og fotoene viser (maalt 3700-4900, z 905-1105).
# Over- og underkant foelger de to linjene det ligger mellom.
WIN_X0 = 3700.0
WIN_X1 = 4900.0
WIN_ABOVE_STRAKE = 70.0      # underkant over listens senter (22 mm klaring)
WIN_BELOW_DECK = 30.0        # overkant under dekkskanten (1 mm leppe i 1:30)
WIN_DEPTH = 15.0             # forsenkning, 0,5 mm i 1:30
WIN_RAD = 55.0

# cockpit: bronnen er dekkshalvbredden minus COCKPIT_INSET langs sidene, og
# foelger hekkens runding akterover (COCKPIT_AFT, maalt i dekksplanen) fram
# til en nesten rett bakkant paa 7 735. Karmen ligger langs bronnen fra
# COCKPIT_X0 og gaar i ett med dekket ved 6 800; toppen er maalt i profilen.
COCKPIT_X0 = 5660.0
COCKPIT_HALF_W = 850.0       # bronnen, oevre grense
COCKPIT_INSET = 290.0        # bronnens side innenfor dekkskanten
COCKPIT_AFT = [              # bronnens bakre runding (x, halvbredde)
    (7640.0, 598.0), (7666.0, 550.0), (7682.0, 500.0), (7695.0, 450.0),
    (7703.0, 400.0), (7710.0, 350.0), (7716.0, 300.0), (7721.0, 250.0),
    (7724.0, 200.0), (7729.0, 150.0), (7733.0, 100.0), (7735.0, 50.0),
    (7735.0, 0.0),
]
COCKPIT_FLOOR_Z = 294.0      # bronnens gulv over DWL
COCKPIT_RAD = 140.0          # hjorneradius forut, i plan
COAMING_HALF_W = 980.0       # karmens ytterkant
COAMING_X1 = 6900.0          # karmen slutter her (den er nede i dekket fra 6 800)
COAMING_DOWN_X = 6750.0      # herfra glir karmtoppen jevnt ned i dekket (til COAMING_X1)
COAMING_MIN_H = 40.0         # karmen staar minst saa mye over dekket ved ytterkanten
# karmtoppen er en glatt kurve gjennom tabellen (innen 5 mm av punktene)
COAMING_TOP_Z = [            # karmens overkant (x, z over DWL), fra profilen
    (5680.0, 1190.0), (5800.0, 1180.0), (6000.0, 1148.0), (6200.0, 1118.0),
    (6400.0, 1101.0), (6600.0, 1078.0), (6800.0, 1064.0),
]
COAMING_FWD = 80.0           # karmen begynner saa langt foran bronnen (under sprayhooden)
COAMING_RAD = 200.0          # karmens hjorneradius forut, i plan
COAMING_EDGE_R = 25.0        # avrunding av karmens overkant, begge sider (0,8 mm i 1:30)
COAMING_GAP = 2.0            # karmens innerside staar saa langt utenfor bronnveggen
WIDTH_BLEND = 40.0           # myk overgang der karm og bronn gaar fra fast bredde
                             # til aa foelge dekkskanten

# --------------------------------------------------------- utstyrshull
MAST_STEP_X = 3400.0    # mastefot fra baugen (profil: 3324-3471)

# Masten er oval, slik alu-profiler er: dypere for-akter enn paa tvers.
# Maalene er modell-mm ganget opp til fullskala, saa de foelger SCALE.
# Anslag ut fra en typisk profil for denne baatstorrelsen (ca. 120 x 90 mm
# i virkeligheten) - erstatt med maalte tall naar de finnes.
MAST_SECTION_X = 4.0 * SCALE    # mast, for-akter
MAST_SECTION_Y = 3.0 * SCALE    # mast, tvers
MAST_FIT = 0.25 * SCALE         # klaring per side -> hull 4,5 x 3,5 mm

MAST_HOLE_X = MAST_SECTION_X + 2.0 * MAST_FIT
MAST_HOLE_Y = MAST_SECTION_Y + 2.0 * MAST_FIT
MAST_SOCKET = 11.0 * SCALE      # hvor dypt masten staar i ruffen
MAST_CHAMFER = 0.3 * SCALE      # fas i begge ender av masten
MAST_POST_W = 100.0             # massiv soyle under mastesteget, ned til bunnen

# rekkepåler: stasjon fra baugen, styrbord og babord speiles
STANCHION_X = [1450.0, 2500.0, 3550.0, 4600.0, 5650.0, 6700.0]
STANCHION_D = 1.1 * SCALE     # hull for 1,0 mm tråd / printet rekkepåle
STANCHION_INSET = 70.0        # inn fra dekkskanten

# rekkepaaler: hoyde og livline-oyer (fullskala)
STANCHION_H = 600.0           # 20 mm i modellen
STANCHION_SHAFT = 1.1 * SCALE
STANCHION_PIN = 2.2 * SCALE   # tapp ned i dekket
LIFELINE_Z = (300.0, 600.0)   # to livliner over dekket
LIFELINE_EYE_D = 0.5 * SCALE  # hull for tauverket
LIFELINE_EYE_L = 1.6 * SCALE  # oyets lengde langs hullet (for-akter)
LIFELINE_EYE_W = 1.3 * SCALE  # oyets bredde
LIFELINE_EYE_H = 1.3 * SCALE  # oyets hoyde
STANCHION_SPARES = 4          # ekstra paaler paa arket

PULPIT_X = [520.0, 900.0]     # pulpit-bein (baug)
PUSHPIT_X = [7250.0, 7680.0]  # pushpit-bein (akter)

# vinsjene staar midt paa cockpitkarmen, akter for sprayhooden: dekksplanen
# viser dem som sirkler ved x = 6 555 og profilen ved 6 450-6 590
WINCH_X = 6540.0
WINCH_BASE_D = 110.0          # sokkel (karmen er 110-130 mm bred her)
WINCH_DRUM_D = 84.0           # trommel
WINCH_H = 90.0                # hoyde over karmen, med kuppel paa toppen
CLEAT_X = [700.0, 4900.0, 7500.0]
CLEAT_INSET = 150.0           # klampene staar saa langt inn fra dekkskanten
CLEAT_L, CLEAT_W, CLEAT_H = 180.0, 45.0, 60.0   # hornklamp: lengde, bredde, hoyde
STEMHEAD_X = (60.0, 360.0)    # stevnbeslaget paa fordekket, for-akter
STEMHEAD_W = 90.0
STEMHEAD_H = 55.0             # over dekket; beslaget staar bare paa dekket

# ------------------------------------------------------------- fenderlist
# Listens senterlinje er maalt ut av profiltegningen (strake_z_mm i
# data/hull_stations.csv). Den ligger under dekkskanten og bygges som en
# egen list utenpaa skrogsiden, med baksiden begravd i skroget. Paa fotoene
# er den en slank, moerk gummilist (Bambu-modellen: ca. 56 x 16 mm). Her er
# den avrundet ytterst og paa toppen, og undersiden ender i 45 grader mot
# skroget, saa den printes uten utheng. Den foelger hekkens rundede hjoerne
# og gaar tvers over akterspeilet.
STRAKE_H = 58.0         # synlig hoyde (ca. 1,9 mm i 1:30)
STRAKE_PROUD = 26.0     # hvor langt den stikker ut (ca. 0,9 mm i 1:30)
STRAKE_BURY = 30.0      # hvor langt baksiden gaar inn i skroget
STRAKE_X0 = 200.0       # starter her - helt i stevnen er skroget for spisst
STRAKE_TAPER = 250.0    # forenden dykker jevnt inn i skroget over denne lengden
STRAKE_STEP = 100.0     # avstand mellom listens tverrsnitt (glatt loft mellom dem)

# ------------------------------------------------------------------ rigg
BOOM_Z = 1500.0               # bommens høyde over dekk ved masten
BOOM_LEN = 2900.0
SPREADER_Z = 6600.0           # saling over dekk
SPREADER_LEN = 900.0
SPREADER_SWEEP = 22.0         # grader tilbakesveip

# ---------------------------------------------------------------- stativ
STAND_STATIONS = (2900.0, 6100.0)   # hvor vuggene griper skroget
STAND_CLEAR = 18.0 * SCALE          # klaring under kjølen (modell-mm -> full)
STAND_BASE_W = 70.0 * SCALE
STAND_THICK = 6.0 * SCALE

# ------------------------------------------------- innvendige spant (print)
RIB_THICK = 1.2 * SCALE     # tykkelse paa innvendige spant
RIB_PITCH = 26.0 * SCALE    # senteravstand mellom spantene
VOID_FWD = 620.0            # hulrommet starter her (fra baugen)
VOID_AFT = 470.0            # og slutter saa langt fra hekken
# Hulrommet legges lenger inn enn HULL_WALL. Skrogloften (36 stasjoner)
# avviker inntil 0,7 mm (modell) fra de analytiske snittene som innsiden
# regnes fra, og rundt forfoten, der stevnen moeter vannlinjen, runder
# loften av profilen med inntil 2,5 mm. Marginene gjoer at veggen aldri
# blir tynnere enn HULL_WALL; innsiden av skroget er det ikke saa noeye med.
VOID_MARGIN = 0.4 * SCALE       # overalt
VOID_BOW_EXTRA = 1.5 * SCALE    # i tillegg i det fremste kammeret

# rortapper: to pinner paa rorets forkant som gaar inn i akterspeilet, begge
# under vannlinjen der akterspeilet er massivt (bunnen ligger paa ca. -260)
RUDDER_PIN_D = 1.3 * SCALE
RUDDER_PIN_L = 2.2 * SCALE
RUDDER_PIN_Z = (-90.0, -200.0)

# ------------------------------------------------------------- sprayhood
# Profilen (stiplet): fronten gaar fra rufftaket ved 4 945 skraatt opp til
# toppen ved 5 155 (ca. 57 grader), og toppen gaar til 5 975 der akterbuen
# staar. Fotoene: rundet front i plan, runde skuldre.
SPRAY_X0 = 4945.0       # fronten moeter rufftaket, paa senterlinjen
SPRAY_TOP_X0 = 5155.0   # frontens overkant
SPRAY_X1 = 5990.0       # akterkant, henger ut over cockpiten
SPRAY_TOP_Z = 1745.0    # topp over DWL ved akterkanten (profil)
SPRAY_TOP_FALL = 20.0   # toppen ligger saa mye lavere ved fronten
SPRAY_CAMBER = 60.0     # buen paa tvers av toppen
SPRAY_SIDE_ANGLE = 70.0  # sidene, fra vannrett
SPRAY_EDGE_R = 150.0    # skuldrenes radius
SPRAY_FRONT_R = 110.0   # avrunding mellom front og topp
SPRAY_AFT_R = 90.0      # avrunding av akterkanten
SPRAY_FRONT_L = 400.0   # fronten er rundet i plan over saa mange mm
SPRAY_INSET = 120.0     # foten staar saa langt innenfor ruffens side; sidene
                        # gaar videre ned til sidedekket aktenfor ruffen

# ------------------------------------------------- surret storseil paa bom
SAIL_D0 = 300.0         # diameter ved masten
SAIL_D1 = 175.0         # diameter ved nokken
SAIL_START = 260.0      # starter saa langt akter for masten

# ------------------------------------------------------------- baatens navn
BOAT_NAME = "HUGO"          # settes i relieff paa akterspeilet og paa skiltet
NAME_SIZE = 5.0 * SCALE     # bokstavhoyde i modell-mm
NAME_RAISE = 0.35 * SCALE   # hoyde over akterspeilet
NAME_Z = 640.0              # senterhoyde over DWL
