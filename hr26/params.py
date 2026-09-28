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
    (0.93, 0.91),
    (1.00, 0.82),
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

# ----------------------------------------------------------------- ror
RUDDER_X = 7944.0       # forkant ved topp - henger paa akterspeilet
RUDDER_CHORD_TOP = 470.0
RUDDER_CHORD_BOT = 380.0
RUDDER_TOP_Z = -60.0
RUDDER_BOT_Z = -1094.0
RUDDER_RAKE = 110.0     # forkant heller akterover nedover
RUDDER_T = 90.0

# ------------------------------------------------------------ ruff/dekk
COACH_X0 = 2680.0       # forkant ruff fra baugen
COACH_X1 = 5180.0       # bakkant ruff (nedgangskapp)
COACH_HALF_W0 = 620.0   # halvbredde forkant
COACH_HALF_W1 = 900.0   # halvbredde bakkant
COACH_H0 = 330.0        # høyde over dekk, forkant
COACH_H1 = 470.0        # høyde over dekk, bakkant
COACH_RAD = 120.0       # hjørneradius
SIDEDECK_MIN = 270.0    # minste gangbredde langs ruffen

DECK_CAMBER = 90.0      # bue på dekket over halve bredden
COCKPIT_X0 = 5180.0
COCKPIT_X1 = 7260.0
COCKPIT_HALF_W = 620.0
COCKPIT_DEPTH = 560.0
COCKPIT_RAD = 140.0
COAMING_H = 150.0       # cockpitkarm over dekk

# --------------------------------------------------------- utstyrshull
MAST_STEP_X = 3480.0    # mastefot fra baugen

# Masten er oval, slik alu-profiler er: dypere for-akter enn paa tvers.
# Maalene er modell-mm ganget opp til fullskala, saa de foelger SCALE.
# Anslag ut fra en typisk profil for denne baatstorrelsen (ca. 120 x 90 mm
# i virkeligheten) - erstatt med maalte tall naar de finnes.
MAST_SECTION_X = 4.0 * SCALE    # mast, for-akter
MAST_SECTION_Y = 3.0 * SCALE    # mast, tvers
MAST_FIT = 0.25 * SCALE         # klaring per side -> hull 4,5 x 3,5 mm

MAST_HOLE_X = MAST_SECTION_X + 2.0 * MAST_FIT
MAST_HOLE_Y = MAST_SECTION_Y + 2.0 * MAST_FIT

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

WINCH_X = 5450.0
WINCH_INSET = 430.0
CLEAT_X = [700.0, 4900.0, 7500.0]

# ------------------------------------------------------------- fenderlist
STRAKE_DROP = 112.0     # fenderlistens senter under dekkskanten
STRAKE_H = 95.0
STRAKE_PROUD = 55.0     # hvor langt den stikker ut

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

# rortapper: to pinner som limes i akterspeilet
RUDDER_PIN_D = 1.3 * SCALE
RUDDER_PIN_L = 2.2 * SCALE
RUDDER_PIN_Z = (-210.0, -830.0)

# ------------------------------------------------------------- sprayhood
SPRAY_X0 = 4280.0       # forkant kalesje (fra baugen)
SPRAY_X1 = 5190.0       # bakkant, mot nedgangen
SPRAY_H = 560.0         # hoyde over ruffen
SPRAY_OVERHANG = 30.0   # stikker saa vidt ut til side for ruffen

# ------------------------------------------------- surret storseil paa bom
SAIL_D0 = 300.0         # diameter ved masten
SAIL_D1 = 175.0         # diameter ved nokken
SAIL_START = 260.0      # starter saa langt akter for masten
