# Minne for Claude

Dette er det felles minnet for Claude-arbeid i dette repoet, uansett modell
(Opus, Fable, Sonnet) og uansett om økten startes her, i en worktree eller fra
GitHub. Når noe lagres som minne, skrives det også hit og pushes.

## Brukeren

* Skriver norsk. Vil at Claude er «kaptein»: anbefaler, bestemmer og kjører,
  og avslutter med valgt kurs og hva som trengs fra brukeren.
* Under lange jobber skal det være lite underveisrapportering og mest mulig
  faktisk forbedring. Høyst ett bilde mellom hvert trinn.
* Minner skal lagres slik at også Fable ser dem: her i `CLAUDE.md`, pushet til
  GitHub, i tillegg til Claude Codes lokale minne.
* Om V10 (10.11.2026): «tiden er ikke problem, tokens er», og deretter «maks
  effort og ultra, ikke spar på noe, best mulig».
* **Kilderegel (13.11.2026, erstatter «tegninger fra produsent trumfer alt»
  fra 12.11):** Når bildene av den ekte båten og tegningene eller brosjyren er
  uenige, gjelder bildene. Enderleins tegning og brosjyren brukes der bildene
  ikke viser noe, og Bambu-modellen er stilmål. Tegningene stemmer stort sett
  med båten; avvikene som er funnet, lå i modellen.
* Brukeren liker linjene i Bambu-modellen, særlig dekkskanten, fenderlisten og
  akterspeilet. De er stilmålet der tegningene ikke sier noe, etter at bredden
  er rettet.
* Veggene skal ikke være tynne, heller tykke. V10 bruker minst 2 mm.
* Farger er ikke viktige nå. Bare modeller formen.
* Navnet skal ikke stå på akterspeilet (bare på skiltet).
* Mast og hull for rekke og pulpit har lav prioritet. Hullene viser bare hvor
  delene skal stå; mast og rekke limes, og litt pussing og sparkel er greit.
* Før en stor bygging vil brukeren ha spørsmålene først, og så en bekreftelse
  og oppsummering før arbeidet starter.
* Unntak for V10 (13.11.2026): «bare kjør avgjørelser på V10, V10 er tillatt
  til det». Claude bestemmer selv i V10 etter rekkefølgen for kildene, pusher
  til `v10` når alt er grønt («push hvis grønt») og samler spørsmålene som
  bare eieren kan svare på til rapporten etterpå. Under natteøkter går
  arbeidet til ukekvoten er høyst 70 %.

## V10 – glattere skrog og dekk (startet 10.11.2026)

* Mål: skrog og dekk (`01_skrog.stl`) som ligner den ekte båten, med glatte
  linjer i stedet for «robot», uten å miste de målte linjene. Ror, mast og
  rigg er utenfor.
* Utgangspunktet er den parametriske modellen, ikke Bambu-AI-modellen. Den er
  18 % for smal og mangler undervannsdel.
* Årsaker, krav og plan står i `V10.md` i grenen `v10`. Arbeidet skjer lokalt i
  worktreen `../HR26-modell-v10`.
* **Status 11.11.2026: pauset.** Alt arbeid ligger i grenen `v10`: koden for
  arbeidspakkene A, B og C (bygget hver for seg, ikke samlet), patcher,
  rapporter, bildemål, poengkort og skript i `v10/`. Les avsnittet «Status» i
  `V10.md` før du fortsetter. Neste steg er samlet bygging og eksport, så
  forbedringsrunder.
* **12.11.2026: gjenopptatt, med utvidet mål.** Enderleins tegning 448-5 er
  fasit for linjene. Taket på ruffen blir et avtakbart lokk
  (`16_ruff-tak.stl`), og innredningen fra tegningen (toalettrom, salong,
  bysse, nedgang) printes i skroget uten support. Vinduene i skrogsiden blir
  åpninger. Forbedringsrundene kjøres med workflow. Rekkefølge: utsiden,
  så innredning, lokk og vinduer, så forbedringsrunder, så dokumentasjon.
* **Status 12.11.2026 kl. 20:30: pauset igjen.** Utsiden er bygget samlet og
  består alle krav unntatt dekkslinjen ved x ≈ 2 600–3 100 (et hakk i
  brosjyresporet). 2 mm vegg, eksport 19 MB, avrundet overkant på
  akterspeilet, ikke navn på akterspeilet. `hr26/cabin.py` (lokket) er skrevet,
  men ikke koblet inn. Enderleins tegning viser at kjølen er mye større og står
  400–680 mm lenger forut; det er neste steg. Les «Status – pauset
  12. november» i `V10.md` før du fortsetter.
* **13.11.2026 (natteøkt, Claude med fullmakt): kjøl, kahytt og lokk
  ferdig.** Pushet til `v10`: kjølen etter Enderlein 448-5, rettet
  dekkslinje, avtakbart ruff-tak (`16_ruff-tak.stl`), kahytt med innredning
  uten support, åpne vinduer, vugger som passer, README og eierguide
  oppdatert. Poengkortet består alle krav. **Formen under vann akter venter på
  et mål fra eieren**: tegningens deplasement (2,36 m³) og bildet akterfra
  sier at skroget er for fyldig, mens en vannlinje på 448-5 sier at det
  stemmer. Les «Status – 13. november 2026» i `V10.md` (spørsmålene til
  eieren og oppskriften for trinn 3).
* **13.11.2026 (dag): planen kjørt og pushet.** Planen står i
  `v10/PLAN_13nov_kveld.md`. Stevnen er rett (51,4°, IMG_9370), fenderlisten
  buer 42 mm opp over akterspeilet (IMG_9391), og bunnen akter er hjerte- og
  vinglassformet med dødtre (IMG_9391 rms 11/7 px, kanobunn 2,49 m³).
  Poengkortet `s5_hjerte` (`score.py` 1.2) består alle krav. Kamera- og
  bildeverktøyet ligger i `v10/verktoy/foto/py`. Les «Status – 13. november
  2026, planen kjørt» i `V10.md` før du fortsetter.
* **13.11.2026 (kveld): trinn 4, akterspeilets hjørne.** Eierens blå prikker
  på IMG_9391 (bekreftet av et blindt kantsøk) viser at akterspeilet er en
  spiss V med skarpt hjørne: ca. 200 mm halvbredde i DWL mot 600 i modellen
  før. Formen akter er tilpasset hjørnet, omrisset og glatte kurver
  (`opt_hjorne.py`), `TRANSOM_CORNER_L` er 0 (det rundede kuttet gir hull i
  STL-en når akterspeilet er smalt) og `STL_ANG` er 0,12. Poengkortet
  `s6_hjorne` (`score.py` 1.3) består alle krav. Modellens DWL stemmer med
  vannet i IMG_9370 innen ±2 cm; stripen er bare maling, men er brukt som
  høydemål akter (±4 cm). Les «Status – 13. november 2026, trinn 4» i
  `V10.md`.
* **13.11.2026 (kveld): trinn 5, forkroppen.** Eieren: «ser ut som en
  hvithai med en klump på magen». Fire målere løste kamera for IMG_9395,
  9387, 9374 og 9389. Funnene: flat bunn med en finne (dødtreet) foran
  kjølen, 30–45 mm for høy kjøllinje fra 1,4 til 2,9 m, og en for fyldig baug.
  Rettet med `BOTTOM_PHOTO_DZ`, dødtreet fra kjølens forkant, en stor hulkil
  (`KEEL_LE_FILLET_R` 1000) og spant tilpasset bildene (`opt_forkropp.py`).
  IMG_9388-kameraet er ikke til å stole på (f 2068). Fenderlisten bygges i
  kontrollerte biter (`build.union_strake`), fordi den ellers kan falle bort
  i stillhet. Poengkortet `s7_forkropp` (`score.py` 1.4) består alle krav.
  Les «Status – 13. november 2026, trinn 5» i `V10.md`.
* **13.11.2026: trinn 6 venter på eieren («lagre i minnet, jeg tar dette
  senere»).** Eieren så skjermklipp A, B og C (`~/Pictures/Screenshots`):
  forfoten ser ut som en «boble», og han tegnet en slankere linje (B). Min
  vurdering, målt i alle fire bildene:
  * Forfoten (x 0,9–1,5 m) er 1–3 cm for fyldig. Det er jeg enig i.
  * Bunnen fra 1,5 til 3 m ble trolig senket for mye i trinn 5. IMG_9389
    (eierens bilde A) og IMG_9395 sier 3–4 cm for dypt. IMG_9374 og 9387
    sier riktig, men kameraene deres har unaturlige linseparametre.
  * Eierens linje skjærer 5–8 cm, mer enn bildene støtter.
  * C: jeg er uenig i å skjære siden inn foran kjølen. Bredden stemmer med
    IMG_9395, og ved kjølroten mangler det heller materiale.
  * Foreslått trinn 6: trekke forfoten inn 2–3 cm, heve bunnen ca.
    1,5–2 cm ved x 1,5–3 m (`BOTTOM_PHOTO_DZ`) med IMG_9389 og 9395 vektet
    likt, glatte bunnreisningens dupp ved t 0,45, bygge, kjøre poengkortet og
    pushe hvis grønt. Vent på «kjør». Et bilde rett fra siden i
    vannlinjehøyde avgjør 1,5–2 cm-spørsmålet.
  * Eieren mener også at kjølen stikker for dypt. Det er ikke vist:
    dypgang 1 400 er oppgitt og stemmer med 448-5. Men stripen i bildene på
    land kan tyde på ca. 10 cm. Avgjøres med målebånd fra fenderlistens
    underkant ned til kjølbunnen midt på kjølen (modellen har 2 200 mm).
    Roret er trolig 5 cm for dypt (−1 094 mot ca. −1 045) og tas med i
    trinn 6.
* **13.11.2026 kl. 17: «bare å kjøre» (trinn 6 + 7).** Eieren la til nye bilder
  i `docs/foto` (`nye (1)`–`(6)`, `IMG_9526`). Originalene ligger i
  `~/Documents/Seilbåt/nye_2026-11-13`. `IMG_9526` har GPS og viser et barn, og
  `nye (3)`/`(5)` viser personer, så de skal IKKE i det offentlige repoet
  uten at eieren sier ja. Målere: `v10/verktoy/foto/py/n4_*` (fra siden,
  avgjør trinn 6) og `n6_*` (akterhjørnet, roret og kjølen). Trinn 7:
  cockpit med seter, fotbrønn og brodekk (nye 2 og 5, Enderlein 448-5).
  Modellen har bare en flat brønn.
* **13.11.2026 kl. 19: trinn 6 og 7 ferdige og pushet. Pause for natten.**
  Bunnen er 9–15 mm opp etter «nye 4», roret −1 015 og vinduet 3 580–5 150 og
  20 mm lavere. Cockpiten har seter og brodekk på z 880, fotbrønn
  5 935–7 300 med gulv på 455, og nedgangen er åpen ned til 920. Kjølen og
  akterspeilet står. Poengkortet `s8b_cockpit` består alle krav.
  **Neste: «kanten»** (kant, kant2 og kant3): dekkskanten er høyere over
  vinduet, har en knekk ved vinduets akterende og faller mot rekkepålen og
  tanklokket. I tillegg cockpitkarmens høyde, steget og avrundingene. Les
  «Status – 13. november 2026 kl. 19» i `V10.md`. Bildet IMG_9304 heter nå
  `kant2.jpg`. `kant.jpeg` (barnet) og `kant3.jpeg` holdes utenfor git.
* **14.11.2026 (natt): trinn 8 «kanten» ferdig og pushet.** Målt i «nye 4»,
  IMG_9374 og «nye 6»: dekkskanten er hevet 36–44 mm over vinduet
  (`DECK_EDGE_Z`), skrogsiden slutter i en knekk aktenfor vinduet med en 40°
  skulder over (`KNUCKLE_Z`, `hull.shoulder_cutter`), og karmtoppen går som
  akterdekk helt akter med et trinn opp fra sidedekket ved 6 040
  (`COAMING_TOP_Z`, `AFTDECK_X0`). Vinduet er litt lavere forut, og kanten
  under lokket er 1,1 mm (`LIP_H`). Poengkortet `s9_kant` (`score.py` 1.5)
  består alle krav. Rettet underveis: `shell.hollow` hulet ut kahytten når et
  «behold»-volum lå etter kahyttens, og eksporten tetter nå hull på én
  trekant. Usikkert: skulderens vinkel, trinnets plass (±100 mm) og om den
  mørke linjen langs dekkskanten er en fotlist. Ikke gjort: avrunding av
  knekken, knekken rundt akterspeilet og nye README-bilder. Eieren kan måle
  den skrå flaten ved vinsjen (modellen ca. 275 mm langs flaten). Les
  «Status – 14. november 2026» i `V10.md`.
* Krav i korte trekk: LOA 7 950 mm, bredde 2 680 mm (±0,5 %), dypgang 1 400 mm.
  Dekkslinje, spring og listehøyde skal ligge innen 12,5 mm av målepunktene.
  Rorhull, masthull og rekkehull blir der de er. Stativvuggene eksporteres på
  nytt fordi de følger tverrsnittene.

## Referanser

* Bilder av den ekte båten ligger i `docs/foto/`, uten metadata og nedskalert
  til høyst 2400 px. Originalene ligger lokalt i `~/Documents/Seilbåt`.
  * IMG_9388: baugen forfra
  * IMG_9391: akterspeilet
  * IMG_9389: skrått bakfra
  * IMG_9387, 9374 og 9370: fra siden
  * IMG_9395: baugen nedenfra
  * kant2.jpg (før IMG_9304) og IMG_9372: dekket ovenfra
  * nye4_babord_side (fra siden, beste kamera), nye6_akterhjorne,
    nye1_akter_nedenfra og nye2_cockpit_ovenfra (13.11). kant3.jpeg:
    dekkskanten ved vinduet (privat, ikke i git)
* Samme mappe har Bambu-modellen. Den er bra for utseende og for posisjoner
  langs båten, men ikke for bredder.
* Verftets side for HR 26 (hallberg-rassy.com, «previous models») har
  brosjyren som modellen er sporet fra (profil og dekksplan 1:50), katalogen
  fra 1981, Enderleins egen tegning 448-5 (profil og plan med innredning,
  1:15, 1977), en vuggeskisse og mer. Kopier ligger i
  `~/Documents/Seilbåt/Hallberg-Rassy-kilder`, ikke i repoet.
* HR 26 er trolig Enderleins konstruksjon nr. 448. Sjöhistoriska museet har
  arkivet hans (DigitaltMuseum, nummer `1996:10:<nr>:<ark>`), men ingen
  HR 26-tegninger ligger ute på nett. DigitaltMuseum stenger ute automatiske
  oppslag, så det må sjekkes i nettleser eller ved å spørre museet.

## Tekniske merknader

* **Minne (13.11.2026):** PC-en (16 GB RAM) har krasjet fire ganger under
  V10, sist 13.11 kl. 00:15, da fem agenter jobbet samtidig og én kjørte
  CadQuery-test av lokket. Loggen viste tomt minne og så feilkode 0x133. Kjør
  derfor alle tunge Python- og CadQuery-jobber med minnetak og lås:
  `python tools/memcap.py --gb 5 --lock -- python skript.py ...`. Taket gir
  MemoryError i stedet for krasj, og låsen gjør at bare én CAD-jobb kjører om
  gangen. Ha høyst to agenter i gang samtidig.
  **Fra 13.11 kl. 17:** eieren har satt sidefila fast til 32 GB (før ca.
  15,5 GB automatisk) og sier at flere agenter går. Nå gjelder høyst fire
  agenter samtidig. Python-jobber kjøres med `--gb 3`, CadQuery med
  `--gb 5 --lock` (fortsatt bare én CAD-jobb om gangen).
* **Når eieren spiller (13.11.2026 kl. 23: «ikke kjør så store prosesser for
  jeg har en game med CSGO»):** så lenge `cs2.exe` kjører (ca. 3,3 GB, og
  bare ca. 3,5 GB ledig), kjøres ikke skrogbygget (topp 2,6 GB, 135 s) eller
  poengkortet (1,4 GB). Lette jobber går fint: måleskriptene for bildene
  (0,2–0,4 GB) og én liten CadQuery-del med `--gb 2 --lock` (0,6–1,2 GB).
  Legg det tunge bygget i kø med et bakgrunnsskript som venter til `cs2.exe`
  er avsluttet (`tasklist //FI "IMAGENAME eq cs2.exe"`), og som så bygger og
  kjører poengkortet. Merk: å stoppe bakgrunnsjobben i Claude Code stoppet
  ikke selve skriptet 14.11. Det levde videre og bygde en gang til da spillet
  ble avsluttet (resultatet ble byte-likt). La skriptet sjekke en stoppfil,
  eller avslutt `bash`-prosessen selv.
* `01_skrog.stl` ligger dreid +45° om Z på platen.
* `python tools/sammensetning.py` lager `export/visning/hr26_sammensatt.stl`:
  alle delene satt sammen i én STL, bare til å se på (eieren ba om det
  14.11.2026). Lett jobb (1,2 GB, 30 s), fordi skroget hentes fra den ferdige
  STL-en. Fila ligger utenfor git; lag den på nytt etter hvert bygg.
* Skroget alene bygger på ca. 150 s. `python -m hr26.build` sletter alle
  STL-er i `export/stl` før eksport. Med `--only skrog,stativ-vugge1,...`
  bygges og eksporteres bare de delene, og de andre fila blir liggende.
  Delnumrene er faste (`PART_NO` i `build.py`).
* CadQuery eksporterer STL med relativ toleranse som standard, og det gir
  flis-trekanter. Bruk `Shape.exportStl(..., relative=False)`.
* OCC-avrunding feiler på skrogets dekkskant, på akterspeilet og på ruffens
  takkant. Der må rundingen bygges inn i tverrsnitt og profiler.
