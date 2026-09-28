# Hallberg-Rassy 26 — skalamodell i 1:30

Parametrisk 3D-modell av en Hallberg-Rassy 26 (Olle Enderlein, 1978–85),
bygget med [CadQuery](https://cadquery.readthedocs.io/) og lagt til rette for
utskrift på **Bambu Lab A1** (256 × 256 × 256 mm) i PLA.

Skroget printes i **ett stykke**, stående med kjølen ned og dekket opp, plassert
diagonalt på platen. Ror, rigg­beslag og stativ printes som egne deler.

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
støpt i ett med skroget, akterhengt ror, fenderlist rundt hele skroget.

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
3. **Springet** er lest av fenderlisten i profiltegningen, som lar seg følge
   sammenhengende fra baug til akter.
4. **Tverrsnittene** er rekonstruert parametrisk: en superellipse mellom kjølen
   og vannlinjebredden under vann, og en jevn utfalling opp til dekkskanten over.
   Fyldigheten varierer langs skroget (`SECTION_FULLNESS` i `hr26/params.py`).

Tverrsnittene er altså en **rekonstruksjon**, ikke en ekte loft fra spanteriss.
Profil, dekkslinje, spring og hovedmål er derimot målt.

De uttrukne kurvene ligger i `data/`:

| Fil | Innhold |
|---|---|
| `hull_stations.csv` | fairet tabell: dekkshalvbredde, spring, kanobunn |
| `deck_halfbreadth.csv` | rå dekkslinje fra dekksplanen |
| `uw_station.csv` | rå undervannsprofil med kjøl og ror |

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

Bygget tar rundt fire minutter. Resultatet havner i `export/stl/`
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
| `hull.py` | lofting av skroget, fenderlist |
| `appendages.py` | kjøl og ror med NACA-lignende profil |
| `deckhouse.py` | dekk, ruff, vinduer, cockpit, luker |
| `fittings.py` | utsparinger: mastefot, rekkepåler, pulpit, vinsjer |
| `rig.py` | riggen som byggesett |
| `shell.py` | uthuling med innvendige spant |
| `stand.py` | stativ |
| `build.py` | setter sammen, orienterer for print, eksporterer |
| `tools/render.py` | kontrollbilder av STL |
| `tools/meshcheck.py` | sjekker at STL-ene er lukkede |

---

## Delene

| # | Del | Mål (mm) | Merknad |
|---|---|---|---|
| 01 | Skrog | 202,8 × 202,8 × 93,2 | diagonalt på platen, 45° |
| 02 | Ror | 34,5 × 3,2 × 18,1 | printes liggende, to tapper |
| 03 | Mastefot | 9,7 × 8,1 × 4,5 | støpt beslag på ruffen |
| 04 | Masttopp | 6,7 × 5,5 × 5,5 | hull for for- og akterstag |
| 05 | Saling | 56,2 × 14,7 × 3,0 | 22° tilbakesveip |
| 06 | Bom | 100,0 × 5,5 × 2,4 | med ring om masten |
| 07 | Bøyemal | 46,0 × 34,0 × 9,0 | for pulpit og pushpit i messingtråd |
| 08–09 | Stativvugger | ~77 × 100 × 6,0 | freset etter skrogets egne spant |
| 10 | Stativbjelke | 140,7 × 70,0 × 14,0 | vuggene tres ned på tappene |

Plastforbruk for skroget: ca. **164 cm³**, altså rundt 205 g PLA.

### Deler du må skaffe selv

* **Mast:** **ovalt** emne, **4,0 × 3,0 mm × 355 mm**. Ovalen skal stå med den
  lange aksen for-akter. Alle fem riggbeslag har ovalt hull på 4,5 × 3,5 mm, så
  masten kan ikke vri seg i dem — se «Om masten» under.
* **Bom:** samme materiale, 97 mm — eller bruk den printede bommen.
* **Rekkepåler, pulpit og pushpit:** **1,5 mm messingtråd**. Alle hull i dekket
  er 1,6 mm, altså 0,1 mm klaring.
* **Rekkverk (livliner):** tynn tråd eller 0,3 mm messing.

---

## Om masten

En alu-mastprofil er ikke rund. Den er tydelig dypere for-akter enn på tvers,
med likespor i bakkant. Anslått for en HR 26 blir det i størrelsesorden
120 × 90 mm i virkeligheten, altså **4,0 × 3,0 mm** i 1:30.

Alle fem hull i riggen — mastefot, masttopp, saling, bom og selve hullet i
ruffen — er derfor ovale, **4,5 × 3,5 mm**. Det gir 0,25 mm klaring per side,
som er rikelig: hull i PLA kommer typisk ut 0,1–0,2 mm trangere enn nominelt,
og det er lettere å fylle med lim enn å file ut et for trangt hull.

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

## Print

**Skroget**

* Orientering: stående, kjølen ned — STL-en ligger allerede riktig.
* Plassering: rotert 45°, opptar 203 × 203 mm av platen.
* Støtte: **bare under skroget**. I Bambu Studio: støttetype «tre (auto)»,
  «kun på plate» avslått er ikke nødvendig — kjølen står på platen, og det
  eneste som trenger støtte er den lille undersiden ved hekk og baug.
* Skroget er allerede uthult med 1,5 mm vegg og innvendige spant hver 26 mm.
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

## Montering

1. Rens hullene i dekket med et 1,6 mm bor for hånd.
2. Kapp rekkepåler av 1,5 mm messingtråd, ca. 20 mm, og lim dem i hullene.
3. Bøy pulpit og pushpit rundt tappene på bøyemalen (del 07) og lim dem i.
4. Lim mastefoten i utsparingen i ruffen.
5. Tre salingen på masten ca. 220 mm over foten, og masttoppen i enden. Alle
   beslagene er ovale og kan bare tres på én vei — lang akse for-akter.
6. Sett masten i foten. Stag og vant: tynn tråd fra masttoppen til
   rekkepåle­festene.
7. Roret: tappene passer i de to hullene i akterspeilet.

---

## Videre arbeid

* Cockpiten er forenklet — ingen brodekk, benker eller luker.
* Ruffens forkant er noe kantet mot originalen.
* Ingen innredning. Skroget er uthult, så den kan legges til senere.
* Skroget har 11 ikke-manifolde kanter av 169 000 — rester etter boolske
  operasjoner rundt utsparingene. Bambu Studio reparerer dette automatisk ved
  import. Alle øvrige deler er helt lukkede. Kjør
  `python tools/meshcheck.py export/stl/*.stl` for å se status.

### Plass til større målestokk

Skroget opptar 203 × 203 mm diagonalt. Platen er 256 × 256 mm. Fordi baugen er
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
