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
# Fyldighetseksponent for tverrsnittene: 1 = V, 2 = ellipse, >2 = fyldig.
# (stasjon i andel av LOA fra baugen, eksponent)
SECTION_FULLNESS = [
    (0.00, 1.10),
    (0.10, 1.25),
    (0.20, 1.45),
    (0.32, 1.70),
    (0.45, 1.90),
    (0.58, 1.95),
    (0.72, 1.85),
    (0.85, 1.72),
    (1.00, 1.60),
]

# Storste halvbredde i vannlinjen, som andel av storste dekkshalvbredde
WL_BEAM_FRACTION = 0.845

# Vannlinjens form: (andel av LWL fra vannlinjens forkant,
#                    halvbredde som andel av storste vannlinjehalvbredde)
WATERPLANE = [
    (0.00, 0.00),
    (0.04, 0.17),
    (0.08, 0.30),
    (0.15, 0.48),
    (0.25, 0.67),
    (0.35, 0.80),
    (0.45, 0.90),
    (0.55, 0.96),
    (0.65, 0.99),
    (0.75, 1.00),
    (0.85, 0.97),
    (0.93, 0.88),
    (1.00, 0.56),
    (1.015, 0.40),   # ved akterspeilet (7 808): vannlinjen smalner inn mot det
]

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
KEEL_FILLET = 90.0      # avrunding mot skroget

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
SIDEDECK = 210.0             # sidedekk mellom ruffside og dekkskant (plan)
COACH_FRONT_R = 700.0        # rundet front i plan
COACH_MIN_HALF_W = 220.0
COACH_RAD = 140.0            # hjorneradius akter, i plan
COACH_ROOF_CAMBER = 58.0     # takets bue, senter over kant

# luker og ventiler paa taket (x_fra, x_til, bredde, hoyde over tak)
FOREHATCH = (2490.0, 2980.0, 500.0, 40.0)
SLIDE_HATCH = (4352.0, 4940.0, 620.0, 60.0)
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
COAMING_MIN_H = 40.0         # karmen staar minst saa mye over dekket ved ytterkanten
COAMING_TOP_Z = [            # karmens overkant (x, z over DWL), fra profilen
    (5680.0, 1190.0), (5800.0, 1180.0), (6000.0, 1148.0), (6200.0, 1118.0),
    (6400.0, 1101.0), (6600.0, 1078.0), (6800.0, 1064.0),
]

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

WINCH_X = 5900.0
WINCH_INSET = 400.0
CLEAT_X = [700.0, 4900.0, 7500.0]

# ------------------------------------------------------------- fenderlist
# Listens senterlinje er maalt ut av profiltegningen (strake_z_mm i
# data/hull_stations.csv). Den ligger under dekkskanten og bygges som en
# egen list utenpaa skrogsiden, halvt begravd.
STRAKE_H = 95.0
STRAKE_PROUD = 55.0     # hvor langt den stikker ut
STRAKE_X0 = 200.0       # starter her - helt i stevnen er skroget for spisst

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
SPRAY_X0 = 5135.0       # forkant, paa ruffens bakre del
SPRAY_X1 = 6150.0       # bakkant, henger ut over cockpiten
SPRAY_TOP_Z = 1745.0    # topp over DWL (profil)
SPRAY_OVERHANG = 30.0   # stikker saa vidt ut til side for ruffen

# ------------------------------------------------- surret storseil paa bom
SAIL_D0 = 300.0         # diameter ved masten
SAIL_D1 = 175.0         # diameter ved nokken
SAIL_START = 260.0      # starter saa langt akter for masten

# ------------------------------------------------------------- baatens navn
BOAT_NAME = "HUGO"          # settes i relieff paa akterspeilet og paa skiltet
NAME_SIZE = 5.0 * SCALE     # bokstavhoyde i modell-mm
NAME_RAISE = 0.35 * SCALE   # hoyde over akterspeilet
NAME_Z = 640.0              # senterhoyde over DWL
