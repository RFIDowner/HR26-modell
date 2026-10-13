# Hallberg-Rassy 26 — skalamodell i 1:30

Parametrisk 3D-modell av en Hallberg-Rassy 26 (Olle Enderlein, 1978–85),
bygget med [CadQuery](https://cadquery.readthedocs.io/) og lagt til rette for
utskrift på **Bambu Lab A1** (256 × 256 × 256 mm) i PLA.

Skroget printes i **ett stykke**, stående med kjølen ned og dekket opp, plassert
diagonalt på platen. Ror, rigg­beslag og stativ printes som egne deler.

> Skal du bare eie, male eller reparere modellen? Se **[EIERGUIDE.md](EIERGUIDE.md)**.

![Modellen sett skrått ovenfra](docs/images/modell-iso.jpg)

| | |
|---|---|
| ![](docs/images/modell-side.jpg) | ![](docs/images/modell-top.jpg) |

---

## Hovedmål

Fullskala, fra Hallberg Rassy-katalogen 1981 og HR 26-brosjyren:

| | Fullskala | 1:30 |
|---|---|---|
| Lengde over alt | 7 950 mm | 265,0 mm |
| Vannlinjelengde | 6 700 mm | 223,3 mm |
| Bredde | 2 680 mm | 89,3 mm |
| Dypgang | 1 400 mm | 46,7 mm |
| Deplasement | 2,5 t | – |
| Kjølvekt | 1,1 t | – |
| Seilareal | 32 m² | – |
| Masthøyde over vl | 12 000 mm | 400 mm |

Konstruktør: Olle Enderlein. 7/8-rigg med tilbakesveipte salinger, finnekjøl
støpt i ett med skroget, akterhengt ror, fenderlist langs skrogsidene.

---

## Hvordan skroget er loftet

Det fantes **ikke noe spanteriss** i kildematerialet. Det som fantes var
profiltegning og dekksplan i 1:50, og de er brukt slik:

1. **Dekkslinjen** er sporet ut av dekksplanen, piksel for piksel, og kalibrert
   mot LOA = 7 950 mm. Målt bredde blir da 2 700 mm mot oppgitt 2 680 mm — 0,7 %
   avvik, som sier at tegningen er dimensjonsriktig.
2. **Undervannsprofilen** (kanobunn, kjøl og ror) er sporet ut av profil­tegningen.
   Med vannlinjen lagt der antifoulingen starter blir dypgangen 1 391 mm mot
   oppgitt 1 400 mm — 0,6 % avvik. De to tegningene er altså i samme målestokk,
   og kalibreringen er uavhengig bekreftet.
3. **Springet** er dekkskanten: den tynne linjen *over* fenderlisten i
   profiltegningen, der rekka står (`DECK_EDGE_Z` i `params.py`). Fenderlisten
   er lest for seg; den ligger 80 mm under dekkskanten i baugen, 270 midtskips
   og rundt 200 i hekken, og skrogsiden fortsetter opp forbi den.
4. **Tverrsnittene** er rekonstruert parametrisk: en superellipse mellom kjølen
   og vannlinjebredden under vann, og en jevn utfalling opp til dekkskanten over.
   Fyldigheten varierer langs skroget (`SECTION_FULLNESS` i `hr26/params.py`).

Tverrsnittene er altså en **rekonstruksjon**, ikke en ekte loft fra spanteriss.
Profil, dekkslinje, spring og hovedmål er derimot målt.

De uttrukne kurvene ligger i `data/`:

| Fil | Innhold |
|---|---|
| `hull_stations.csv` | fairet tabell: dekkshalvbredde, fenderlistens senterlinje, kanobunn |
| `deck_halfbreadth.csv` | rå dekkslinje fra dekksplanen |
| `uw_station.csv` | rå undervannsprofil med kjøl og ror |
| `profile_top_silhouette.csv` | rå topp-silhuett av profiltegningen (ruff, luker, sprayhood) |
| `scan_roof_outline.csv` | ruffens halvbredde per stasjon fra scannet — pålitelig bare midtskips |
| `deckhouse_features.json` | ruff, trinn, luker, nedgang, sprayhood og cockpit med kilde og sikkerhet per verdi |

**Merk om ruffen (trinn 5a):** fordekket er flatt og høyt (dekkskant 1 204 mm
over vannlinjen i baugen, 1 115 midtskips), og det som ser ut som en lav
forruff i profilens silhuett (1 216–1 226) er dekket selv. Ruffen er derfor
lav og bred: taket ligger på z ≈ 1 350–1 385 fra den skrå fronten ved
2 200–2 330 mm til nedgangsskottet ved 5 625, altså 250–300 mm over dekket.
I plan er ruffsiden dekkshalvbredden minus et sidedekk på 210 mm (`SIDEDECK`),
med rundet front (`COACH_FRONT_R`), slik dekksplanen viser. Forluken sitter på
taket foran masten (2 490–2 980), skyveluken over nedgangen (4 352–4 940), én
ventil på fordekket (1 900) og én på taket (3 894), og sprayhooden står over
nedgangen og ut over cockpiten (5 135–6 150). Høyder og lengder er fra
profiltegningen, bredder fra dekksplanen. Overlegget under viser modellens
silhuett (rødt) på profiltegningen 1:50 — dekkskant, ruff, luker, ventiler,
vindu og sprayhood faller på tegningens linjer.

![Modellens silhuett lagt over profiltegningen 1:50](docs/images/overlegg-profil.jpg)

**Merk om vinduet:** langvinduet sitter i **skrogsiden**, i båndet mellom
fenderlisten og dekkskanten, rett under rekka — slik både profiltegningen,
dekksplanen og fotografiene viser. Målt i profilen går det fra 3 700 til
4 900 mm fra baugen og fra 905 til 1 105 mm over vannlinjen. Modellen legger
underkanten 70 mm over listens senter og overkanten 30 mm under dekkskanten
(`WIN_*` i `params.py`), som en 0,5 mm dyp forsenkning i skrogsiden. Bak
vinduet står full veggtykkelse igjen (`hull_windows` gir uthulingen et
`keep`-volum). Tidligere versjoner hadde vinduet i en ruffside 450 mm inne på
dekket; det var feil.

**Merk om fenderlisten:** listen er en list utenpå skrogsiden, 95 mm høy og
55 mm utstikkende (`STRAKE_*`), bygget som en loft langs den målte senter-
linjen (`strake_z_mm` i `data/hull_stations.csv`). Den ligger *under*
dekkskanten, ikke i den: trinn 2 la dekkskanten ned på listen, og det
flyttet vinduet opp i ruffen og gjorde skrogsiden 130–280 mm for lav. Rundt
hekken følger listen skrogsiden fram til akterspeilet og går tvers over det,
som ett sammenhengende loft fra babord forende til styrbord.

**Merk om hekken og akterspeilet (trinn 5b):** hekken er rundet i plan, slik
dekksplanen viser: dekkskanten går fra 890 mm halvbredde ved 7 700 gjennom et
hjørne med radius rundt 290 mm over i akterspeilets overkant, som er svakt
buet i plan (radius ca. 3 000 mm) og når 7 950 mm på senterlinjen
(`STERN_OUTLINE`, målt punkt for punkt). Akterspeilet heller 8,3° med toppen
lengst akter — i profilen krysser det vannlinjen ved 7 806 og dekkskanten ved
7 945 (`TRANSOM_WL_X`, `TRANSOM_RAKE`, `TRANSOM_CAMBER_R`). Skroget loftes
rett akterover forbi akterspeilet, ca. 600 mm bredt aktenfor hjørnet, og
akterspeilets flate kappes ut av loften (`hull.transom_cutter`). Vannlinjen
smalner inn mot akterspeilet (`WATERPLANE` fortsetter forbi t = 1), så
akterspeilet er bredest oppe og smalner nedover til bunnen møter det rundt
260 mm under vannlinjen. Tidligere endte modellen i et loddrett, flatt
akterspeil 1 331 mm bredt med skarpe hjørner.

**Merk om cockpitbrønnen:** brønnen følger dekkskanten 290 mm innenfor langs
sidene (`COCKPIT_INSET`) og hekkens runding akterover etter den målte tabellen
`COCKPIT_AFT`, fram til en nesten rett bakkant ved 7 735 mm — som i
dekksplanen, der brønnen følger hekkens kurve hele veien rundt. Karmen
(`COAMING_TOP_Z`) faller fra 1 190 mm over vannlinjen ved forkanten til den
går i ett med dekket ved 6 800–6 900. Overlegget under viser modellens
dekksutlinje (rødt) og brønnen (blått, snitt 850 mm over vannlinjen) på
dekksplanen 1:50.

![Modellens dekksutlinje og brønn lagt over dekksplanen 1:50](docs/images/overlegg-plan.jpg)

**Merk om deplasementet:** modellen har et beregnet undervannsvolum på ca. 3,9 m³,
mens brosjyren oppgir 2,5 tonn. Avviket kommer av at profiltegningen gir en
forholdsvis dyp og flat kanobunn. For en utstillingsmodell betyr det ingenting —
formen er hentet fra tegningen — men tallet skal ikke brukes til hydrostatikk.

---

## Kjør

```bash
pip install -r requirements.txt
python -m hr26.build                 # alt: skrog, ror, rigg, stativ
python -m hr26.build --hull          # bare skroget (raskt ved utvikling)
python -m hr26.build --no-hollow     # massivt skrog
python -m hr26.build --stations 48   # finere lofting
```

Bygget tar rundt tjue minutter; fenderlisten rundt hekken er det tyngste
steget. Resultatet havner i `export/stl/`
(print-orienterte STL-er) og `export/step/hr26.step` (hele modellen som STEP).
STEP-fila er på 17 MB og ligger derfor ikke i repoet — den lages av samme
kommando.

Alle mål ligger øverst i `hr26/params.py`. Vil du ha en annen målestokk er det
nok å endre `SCALE` — alt annet følger med, inkludert veggtykkelser og hull­
diametre, som er definert i modell-millimeter og ganget opp.

### Moduler

| Fil | Ansvar |
|---|---|
| `params.py` | alle mål og parametre |
| `curves.py` | fairede skrogkurver, tverrsnitt, deplasement |
| `hull.py` | lofting av skroget, akterspeilet, fenderlist |
| `appendages.py` | kjøl og ror med NACA-lignende profil |
| `deckhouse.py` | ruff, luker, ventiler, nedgang, vindu i skrogsiden, sprayhood, cockpit |
| `fittings.py` | utsparinger: mastefot, rekkepåler, pulpit, vinsjer |
| `rig.py` | riggen som byggesett |
| `shell.py` | uthuling med innvendige spant |
| `stand.py` | stativ |
| `plaque.py` | skiltplate |
| `build.py` | setter sammen, orienterer for print, eksporterer. Boolske operasjoner som ikke gir ett volum stopper bygget i stedet for å miste deler i stillhet |
| `tools/render.py` | kontrollbilder av STL |
| `tools/meshcheck.py` | sjekker at STL-ene er lukkede |

---

## Delene

Femten filer i `export/stl/`. Materialtallene er reell geometri ganget med
1,24 g/cm³ — legg til litt for støtte og skjørt.

| # | Fil | Mål (mm) | PLA |
|---|---|---|---|
| 01 | `01_skrog.stl` | 205,9 × 205,9 × 104,8 | 228 cm³ / 283 g |
| 02 | `02_ror.stl` | 34,5 × 3,2 × 16,4 | 1,0 cm³ / 1 g |
| 03 | `03_mast-354mm-A1.stl` | 354,1 × 4,0 × 3,0 — ligger diagonalt, 253,2 × 253,2 | 3,3 cm³ / 4 g |
| 04 | `04_mast-365mm-ikke-A1.stl` | 365,1 × 4,0 × 3,0 | 3,4 cm³ / 4 g |
| 05 | `05_mastefot.stl` | 9,7 × 8,1 × 4,5 | 0,1 cm³ |
| 06 | `06_masttopp.stl` | 6,7 × 5,5 × 5,5 | 0,1 cm³ |
| 07 | `07_saling.stl` | 15,3 × 56,2 × 3,0 | 0,1 cm³ |
| 08 | `08_bom.stl` | 100,0 × 5,5 × 2,4 | 0,3 cm³ |
| 09 | `09_bom-med-seil.stl` | 100,0 × 10,0 × 8,6 | 3,6 cm³ / 4 g |
| 10 | `10_rekkepaaler.stl` | 24,9 × 54,4 × 1,6 | 0,5 cm³ |
| 11 | `11_boyemal.stl` | 46,0 × 34,0 × 9,0 | 4,8 cm³ / 6 g |
| 12 | `12_stativ-vugge1.stl` | 79,7 × 94,6 × 6,0 | 36,0 cm³ / 45 g |
| 13 | `13_stativ-vugge2.stl` | 77,1 × 106,4 × 6,0 | 37,0 cm³ / 46 g |
| 14 | `14_stativ-bjelke.stl` | 140,7 × 70,0 × 14,0 | 49,9 cm³ / 62 g |
| 15 | `15_skilt.stl` | 104,0 × 46,0 × 3,7 | 14,4 cm³ / 18 g |

**03 og 04 er alternativer, og 08 og 09 er alternativer** — print én av hver.
Til sammen blir det rundt **380 cm³, altså ca. 470 g PLA**: skroget 283 g,
stativet 152 g, resten under 35 g. Én rull på 1 kg holder med god margin.

### Slik printes hver del

**01 Skrog** — den store jobben, 12–16 timer.
* Ligger ferdig orientert: kjølen ned, rotert 45°, 206 × 206 mm av platen.
* **Infill 0 %.** Skroget er uthult med minst 1,5 mm vegg (1,9 mm nominelt,
  3,4 mm i baugkilen), og innvendige spant hver 26 mm bærer dekket. Setter du
  infill blir det bare tyngre og tregere. Innsiden er skrogsnittet flyttet
  innover langs normalen med litt margin, så veggen holder tykkelsen også der
  skroget er en tynn kile — den gamle, skalerte innsiden ga 0,2–0,5 mm vegg i
  baugen og et hull i stevnen ved vannlinjen.
* Støtte på, bare under skroget ved baug og hekk. Ingen støtte trengs oppe:
  dekket og cockpitgulvet spenner mellom spantene (26 mm), det broer PLA fint.
* Lag 0,12–0,16 mm. Ingen brim — kjølen gir god vedheft, og det er plass til
  brim om du vil ha det.
* Vil du ha rødt bunnstoff: fargeskift på **46,7 mm**, som er vannlinjen.

**02 Ror** — printes liggende, 3 mm tykt. Støtte av. Forkanten følger
akterspeilets helning, og de to tappene på den passer i hullene i akterspeilet
rett under vannlinjen.

**03 Mast, 354 mm, for A1** — ligger allerede diagonalt og fyller
253,2 × 253,2 mm av platen. Uten sokkel: den limes bare i mastefot-beslaget.
Ingen plass til brim. Se «Masten».

**04 Mast, 365 mm, ikke A1** — med 11 mm sokkel ned i ruffen. Trenger en
plate med minst 365 mm langs én akse eller 261 × 261 mm diagonalt. Se «Masten».

**05–08 Riggbeslag** — små, flate, ligger rett på platen. Ingen støtte.
4 vegger og 25 % infill, ellers blir salingarmene skjøre. Alle har ovalt
4,5 × 3,5 mm hull og kan bare tres på masten én vei.

**09 Bom med seil** — alternativ til 08. Har det surrede storseilet med
kalesje på, slik båten ligger fortøyd.

**10 Rekkepåler** — 16 stk på sprue, ligger flatt. **Ikke roter dem opp.**
Liggende blir øyehullene loddrette og kommer rene ut, og lagene løper langs
pålen, som er den sterke retningen. Bruk brim — delene er små og lette.

**11 Bøyemal** — hjelpeverktøy, ikke en del av modellen. Til å bøye pulpit og
pushpit av 1,0 mm messingtråd rundt.

**12–14 Stativ** — vuggene liggende, 6 mm tykke, ingen støtte. Bjelken har
lettelseshull. 15 % infill holder. Tre vuggene ned på tappene.

**15 Skilt** — flatt, ingen støtte. Teksten står 0,7 mm opphøyd. Legg inn
**fargeskift på 3,0 mm**, så kommer HUGO og resten ut i egen farge.

### Deler du må skaffe selv

* **Masten printes** (del 03 eller 04) — se «Masten». Vil du heller lage den av et ovalt 4,0 × 3,0 mm emne på 365 mm,
  passer det i de samme hullene.
* **Pulpit og pushpit:** **1,0 mm messingtråd**, bøyd rundt tappene på bøyemalen.
* **Livliner:** tynt tauverk eller tråd, opptil 0,4 mm. Tres gjennom øynene på
  rekkepålene — se under.

Rekkepålene printes (del 08) og trenger ikke messingtråd.

---

## Masten

Masten printes i ett stykke: rett oval profil **4,0 × 3,0 mm** hele veien,
faset i begge ender. Salingen og masttoppen tres på ovenfra før masten
settes i ruffen, bommen til slutt. Det finnes to filer:

| Fil | Lengde | Sokkel i ruffen | Plate |
|---|---|---|---|
| `03_mast-354mm-A1.stl` | 354,1 mm | ingen — limes i mastefoten | A1, diagonalt, under 3 mm margin, **uten brim** |
| `04_mast-365mm-ikke-A1.stl` | 365,1 mm | 11 mm | minst 365 mm langs én akse, eller 261 × 261 mm |

Synlig masthøyde er den samme for begge: 354 mm over ruffen, som er 12 m over
vannlinjen i 1:30. Forskjellen er bare hva som står nede i hullet.

**354-varianten** er et sjansespill på A1: (354,1 + 4) / √2 = 253,2 mm på en
256 mm plate, så det er ikke plass til brim, og en 354 mm strek med 15 cm²
fotavtrykk kan løsne i enden underveis. Går det bra, fungerer den fint — hullet i
ruffen er der fortsatt, så skyver du masten i bunn står den 11 mm lavere (343 mm
synlig); vil du ha full høyde, holder du den oppe mens limet i mastefoten herder.

**365-varianten** er den riktige om du har tilgang til en større printer. En
Bambu X1 eller P1 har samme plate som A1 og går ikke; en 300 × 300 mm plate gjør
det.

Profilen er jevntykk med vilje. En 26-fots cruiser fra rundt 1980 har en rett
alu-profil uten avsmalning, og en eventuell avsmalning i toppen ville uansett
vært under en halv millimeter i 1:30.

### Slik printes den

Det er en 365 mm lang strek på 4 × 3 mm. Alt handler om å holde den rett.

* **Liggende med den brede siden ned** — STL-en ligger allerede slik. Da er den
  bare 3 mm høy, og lagene løper langs masten, som er den sterke retningen.
  Ingen støtte trengs; ingenting henger i lufta.
* **Brim, 6–8 mm.** Fotavtrykket er bare 15 cm², og uten brim løsner enden
  halvveis ut i printen.
* **Bare vegger, ingen infill.** Sett veggantallet til 6, så fylles hele
  tverrsnittet av sammenhengende perimetre. Det gir maksimal stivhet.
* **Sakte og kaldt.** Ytre vegg 40–50 mm/s, vifte 100 %. PLA, ikke PETG eller
  ASA: PLA er stivest og krymper minst, og det er nettopp stivhet og rettlinjethet
  som betyr noe her. ASA krøller seg opp fra platen på en åpen printer.
* **Print to eller tre samtidig** og bruk den retteste. Det koster 4 gram.
* **La platen bli helt kald** før du tar den løs. Trekker du i en varm, tynn del
  bøyer du den.
* Legg den ferdige masten på et flatt bord og se etter bue. En svak bue rettes
  ved å holde den i 60 °C vann i et halvt minutt og legge den under en bok
  til den er kald.

Stående i ruffen bærer masten seg selv med god margin: den veier 4 gram, og
knekklasten for en 365 mm PLA-stav med dette tverrsnittet er rundt 60 gram.
Det som kan knekke den, er å miste den på gulvet før den er limt.

## Om mastprofilen

En alu-mastprofil er ikke rund. Den er tydelig dypere for-akter enn på tvers,
med likespor i bakkant. Anslått for en HR 26 blir det i størrelsesorden
120 × 90 mm i virkeligheten, altså **4,0 × 3,0 mm** i 1:30.

Det er **én mast**, men fem separate deler sitter på den, hver med sitt eget
hull — som fem perler på samme snor:

| Høyde over ruffen | Del | Hullets rolle |
|---|---|---|
| −11 mm | hullet i ruffen | masten stikker ned i dekket |
| 0 mm | mastefot | beslaget limes rundt masten |
| ca. 220 mm | saling | tres på og skyves opp |
| ca. 354 mm | masttopp | hetten helt øverst |
| ca. 50 mm | bom | ringen i enden går rundt masten |

Alle fem er derfor ovale, **4,5 × 3,5 mm**. Var bare hullet i ruffen ovalt,
ville masten sitte riktig nede ved dekket, men slingre i de fire beslagene
lenger oppe.

Klaringen på 0,25 mm per side er rikelig: hull i PLA kommer typisk ut 0,1–0,2 mm
trangere enn nominelt, og det er lettere å fylle med lim enn å file ut et for
trangt hull i en ferdig printet del.

Den ovale formen låser samtidig masten mot å vri seg. Salingarmene kan altså
ikke snurre rundt og peke feil vei, slik de ville gjort med et rundt hull.

Målene er et **anslag**. Har du skyvelær på den virkelige masten, eller et
nærbilde av masten ved foten med noe av kjent størrelse inntil, sett de målte
tallene inn i `MAST_SECTION_X` og `MAST_SECTION_Y` i `hr26/params.py` og bygg
på nytt — alle fem hullene følger med. Mastens *lengde* trenger du ikke måle;
katalogens 12 m over vannlinjen er verftets eget tall.

Mastefoten er beholdt selv om hullet i ruffen kunne tatt masten alene: HR 26 har
dekksmontert mast, og fotbeslaget er godt synlig på ruffen. Den er gjort lav og
platelignende slik originalen er, i stedet for en høy hylse.

---

## Rekkverket

Rekkepålene printes med **ekte øyer**: hver påle har to gjennomgående hull på
0,5 mm, i 10 og 20 mm høyde, som livlinene tres gjennom. Arket har 16 påler —
12 til båten og 4 i reserve — på en sprue under tappene, så øynene står fritt
og pålene kan klippes av uten å korte inn tappen.

Pålene er 1,1 mm tykke, som svarer til 33 mm i virkeligheten. En ekte rekkepåle
er ca. 25 mm, så de er fortsatt litt grove, men de er nå tynne nok til å lese
riktig — og tykke nok til å tåle å bli håndtert.

De printes **liggende**. Det gir to fordeler: øyehullene står loddrett og
kommer rene ut av printeren, og lagene løper langs pålen, som er den sterke
retningen i bøyning. Står de derimot oppreist, knekker de ved første berøring.

Et 0,5 mm hull kommer typisk ut 0,35–0,40 mm med en 0,4 mm dyse. Det holder til
tråd opp til ca. 0,3 mm. Vil du ha tykkere tauverk, kjør et 0,5 mm bor gjennom
for hånd, eller øk `LIFELINE_EYE_D` i `params.py` og bygg på nytt.

Hullene i dekket er 1,1 mm. Vil du heller bruke messingtråd til pålene, passer
1,0 mm rett i.

---

## Print

**Skroget**

* Orientering: stående, kjølen ned — STL-en ligger allerede riktig.
* Plassering: rotert 45°, opptar 206 × 206 mm av platen.
* Støtte: **bare under skroget**. I Bambu Studio: støttetype «tre (auto)»,
  «kun på plate» avslått er ikke nødvendig — kjølen står på platen, og det
  eneste som trenger støtte er den lille undersiden ved hekk og baug.
* Skroget er allerede uthult med minst 1,5 mm vegg og innvendige spant hver 26 mm.
  **Sett infill til 0 %** — spantene bærer dekket.
* Lag: 0,12–0,16 mm. Fin dyse (0,2 mm) gir tydeligere fenderlist og vinduer.
* Ingen brim nødvendig; kjølen gir god vedheft. Vil du ha brim, er det plass.

**De små delene**

Ligger flatt og trenger verken støtte eller brim. Salingen og bommen er tynne —
print dem med 4 vegger og 25 % infill.

**Stativet**

Vuggene printes liggende (6 mm tykke). Bjelken har lettelseshull. Tre vuggene
ned på tappene; ingen lim nødvendig om passformen blir stram.

---

## Skiltet

Del 13 er en liten plate med opphøyd tekst, ment å stå foran eller ved siden
av stativet:

```
                     HUGO
              Hallberg-Rassy 26
  Konstruktør Olle Enderlein · bygget 1978–1985
 Lengde 7,95 m · Bredde 2,68 m · Dypgang 1,40 m
       Deplasement 2,5 t · Seilareal 32 m²
                 Skala 1:30
```

Teksten står 0,7 mm over platen, altså rundt seks lag med 0,12 mm laghøyde.
Legger du inn et **fargeskift på 3,0 mm** i Bambu Studio, kommer teksten ut i
en annen farge enn platen — svart tekst på hvit plate ser bra ut, og på A1
er det bare å bytte rull manuelt når printeren stopper.

Båtens navn står også **i relieff på akterspeilet**, 0,35 mm opphøyd, slik
en Hallberg-Rassy bærer navnet sitt. Akterspeilet heller 8°, så bokstavene
står med et lite utheng oppover — det printes fint uten støtte. Bokstavene
følger akterspeilets bue, så relieffet er like høyt over hele navnet.

Navnet ligger i `BOAT_NAME` i `hr26/params.py` og brukes begge steder. Sett
det til `""` for å droppe det. Resten av skiltteksten ligger i
`hr26/plaque.py` som `TYPE_LINE`, `LINES` og `SCALE_LINE`.

---

## Montering

1. Rens hullene i dekket med et 1,6 mm bor for hånd.
2. Klipp rekkepålene av sprua (del 08), puss tappen flat, og lim dem i hullene.
   Sørg for at øynene peker for-akter, ellers går ikke livlinene gjennom.
3. Bøy pulpit og pushpit av 1,0 mm messingtråd rundt tappene på bøyemalen
   (del 09) og lim dem i.
4. Lim mastefoten i utsparingen i ruffen.
5. Tre salingen på masten til ca. 213 mm over foten, og masttoppen i enden.
   Alle beslagene er ovale og kan bare tres på én vei — lang akse for-akter.
6. Sett masten i foten. Stag og vant: tynn tråd fra masttoppen til
   rekkepåle­festene.
7. Roret: tappene passer i de to hullene i akterspeilet, rett under
   vannlinjen. Forkanten skal ligge parallelt med akterspeilet.
8. Tre livlinene gjennom øynene, stram lett, og lim endene i pulpit og pushpit.

---

## Videre arbeid

* Cockpiten er forenklet — brønnen har bunn og vegger og følger hekkens
  runding, men ingen brodekk, benker eller luker.
* Roret er bare bladet under vannlinjen. På originalen går rorhodet opp til
  dekkshøyde, med rorkulten inn over akterdekket.
* Sprayhooden er massiv. En ekte kalesje er åpen bakover, men i 1:30 ville
  veggene blitt under en halv millimeter. Frontvinduet er utelatt av samme
  grunn — skjæres det dypt nok til å synes, blir det en tunnel tvers gjennom.
  Males heller inn.
* Ruffens front er en rett 45°-flate. På originalen er den avrundet.
* Rundt akterdekket har tegningen en lav kant — karmen fortsetter rundt
  hekken, men under 50 mm høy etter profilen (under 2 mm i 1:30), med
  pushpiten oppå. Den er utelatt; karmen slutter der den går i ett med dekket
  (6 900 mm), og akterdekket ligger i dekkshøyde.
* Ruffen er massiv over dekket; skroget er uthult bare under dekket. Det
  koster noen gram plast, men gir en stiv og enkel print.
* Ingen innredning. Skroget er uthult, så den kan legges til senere.
* Skroget har 4 ikke-manifolde kanter av 214 000 — rester etter boolske
  operasjoner rundt utsparingene. Bambu Studio reparerer dette automatisk ved
  import. Alle øvrige deler er helt lukkede. Kjør
  `python tools/meshcheck.py export/stl/*.stl` for å se status.

### Plass til større målestokk

Skroget opptar 206 × 206 mm diagonalt. Platen er 256 × 256 mm. Fordi baugen er
spiss blir det roterte fotavtrykket mindre enn et rektangel ville tilsi, og det
er derfor rom for opptil omtrent **1:24** (LOA 331 mm, fotavtrykk ~254 mm).
Endre `SCALE` i `hr26/params.py` og bygg på nytt.

---

## Kilder

* Hallberg Rassy: *Katalog 1981* — hovedmål, masthøyde, motor
* Hallberg Rassy: *HR 26*-brosjyre — profil 1:50, dekksplan 1:50, sailplan 1:100
* Fotogrammetri-scan av en HR 26 — brukt som referanse for dekkslayout,
  ruff og cockpit. Scannet er ikke dimensjonsriktig (ca. 20 % for langt i
  forhold til bredden) og er derfor ikke brukt som geometri.
* Fotografier av båten på land og fortøyd — kjølprofil, spring, akterspeil
