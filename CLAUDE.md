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
  * IMG_9304 og 9372: dekket ovenfra
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
* `01_skrog.stl` ligger dreid +45° om Z på platen.
* Skroget alene bygger på ca. 150 s. `python -m hr26.build` sletter alle
  STL-er i `export/stl` før eksport. Med `--only skrog,stativ-vugge1,...`
  bygges og eksporteres bare de delene, og de andre fila blir liggende.
  Delnumrene er faste (`PART_NO` i `build.py`).
* CadQuery eksporterer STL med relativ toleranse som standard, og det gir
  flis-trekanter. Bruk `Shape.exportStl(..., relative=False)`.
* OCC-avrunding feiler på skrogets dekkskant, på akterspeilet og på ruffens
  takkant. Der må rundingen bygges inn i tverrsnitt og profiler.
