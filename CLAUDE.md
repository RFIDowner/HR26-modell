# Minne for Claude

Dette er det felles minnet for Claude-arbeid i dette repoet, uansett modell
(Opus, Fable, Sonnet) og uansett om økten startes her, i en worktree eller fra
GitHub. Når noe lagres som minne, skrives det også hit og pushes.

## Brukeren

* Skriver norsk. Vil at Claude er «kaptein»: anbefaler, bestemmer og kjører,
  og avslutter med valgt kurs og hva som trengs fra brukeren.
* Under lange jobber skal det være lite underveisrapportering og mest mulig
  faktisk forbedring. Høyst ett bilde mellom hvert trinn.
* Brukeren ser formendringer i en STL-fil, ikke i PNG-figurer (14.11.2026:
  «jeg klarer ikke å se dette uten i en stl fil»). Når formen endres, lag
  før og etter som STL i `export/visning/`, i samme ramme og med et snitt
  der endringen er størst (se `v10/verktoy/foto/py/mage_stl_sammenlign.py`).
  **Senere 14.11 (V11b):** «Jeg trenger kun den ene filen, altså skroget. jeg
  kan heller be om andre filer» og «Kjør kun prosesser som du trenger, jeg vil
  bare se det ferdige nå, printbar fil». Standard er nå bare den printbare
  `export/stl/01_skrog.stl` (`--only skrog`), og bare de kjøringene som trengs:
  bygg, meshcheck og poengkort. STL-er for før og etter lages bare når brukeren ber om det.
* Brukeren vurderer fasongen med øyet, ved å se 3D-modellen rett på og se på
  buen (14.11.2026). At «pølsa» vises på alle bildene, er for brukeren
  «uomtvistelig» og kan ikke konkluderes bort med usikre kameraer. Si hva en
  måling kan og ikke kan avgjøre, men ikke si at bildet «lyver».
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
* **14.11.2026: trinn 9 «magen», startet kl. 02 etter at målet var avklart.** Brukeren
  pekte på IMG_9395 og to skjermbilder av modellen: på båten er buken
  «sprengfull», rund og glatt «som en stor pølse», mens modellen er en kile.
  Claude er enig, og tallene støtter det:
  * Modellens vannlinjebredde er bare 1,80 m (bredde i dekk 2,68), og spantene
    aktenfor kjølens forkant er V-formet (fyldighet 0,53–0,60 mot 0,76–0,77
    forut). Største spantareal ligger ved x 3 500.
  * «nye 1» (aktenfra, nedenfra): bildets omriss ligger 20–30 cm utenfor
    modellens i den nedre delen, på begge sider (`out/n1_meas.json`, `sil`).
    Målingen ble gjort 13.11, men bare brukt til akterspeilet.
  * IMG_9388 (rett forfra): modellen er 50–65 px for smal under vann på begge
    sider. Kameraet er svakt, men retningen er den samme.
  * IMG_9395: modellen mangler 25, 44 og 76 mm ved x 3,1–3,7 m (kjølroten).
  * Baugen fram til ca. 2,4 m og akterspeilet stemmer (IMG_9395, IMG_9391).
  * **Brukerens rammer (14.11, etter vurderingen):** ingenting skal endres
    foran vinduet (x < 3 580). Buken er fin ved starten av vinduet, kanskje de
    første 10 cm, og fra omtrent der smalner modellen for mye inn. Den er fin
    igjen mellom vinsjen (6 540) og akterklampen (7 500), altså fra ca. 7 000,
    og helt akter. Det største spantet skal ikke bli større («vi må ikke øke
    tykkelsen på pølsa på midten»); fylden skal holdes akterover i stedet for
    å krympe. Slankingen 13.11 hadde sin egen grunn og skal ikke gjøres om
    ellers.
  * **Claudes rettelse:** 20–30 cm fra «nye 1» er omrissets avstand i et bilde
    tatt aktenfra, der nærmere spant ser større ut. Holder båten fylden
    akterover, dannes omrisset av de nærmere spantene, uten at båten er
    tykkere enn modellens største spant. Påstandene om bredere vannlinje
    (2,1–2,2 m), om endring fra 2,5 m og om at streken var for forsiktig
    midtskips, er trukket. Modellens tall passer med brukerens beskrivelse:
    spantarealet er størst ved 3 500 (0,62 m²) og faller til 0,56 (4 000),
    0,49 (4 500), 0,44 (5 000), 0,41 (5 500), 0,39 (6 000), 0,36 (6 500) og
    0,28 (7 000). Vannlinjen holder seg (halvbredde 897 → 820); det er under
    vann buken krymper (halvbredde 300 mm under vannlinjen: 633 → 202).
  * **Plan:** lås alt foran 3 580 og aktenfor ca. 7 000. Tabellpunktene ligger
    alt slik: t 0,45 (3 578) og t 0,90 (7 155) står, og bare punktene imellom
    i `SECTION_DEADRISE` og `SECTION_N` (og dødtreet) justeres. Kontroller at
    ingenting foran 3 580 flytter seg (pchip-tangenten ved 0,45 avhenger av
    naboen). Mål spantene ved løftestroppene, og tilpass mot «nye 1»,
    IMG_9395, 9389, 9391 og den blå streken. Kanobunnen øker da anslagsvis
    0,25–0,35 m³ (til ca. 2,7–2,8 m³), alt mellom 3,6 og 7,0 m. Vugge 2
    (6 100), kjølroten og innredningen akter følger med; vugge 1 (2 900) står.
  * Brukerens blå strek (`docs/foto/blå strek.png`, tegnet på et skjermbilde
    av modellen skrått ovenfra): streken ligger 4–14 px utenfor modellens
    omriss fra ca. 3 m til hekken, størst like foran og like bak kjølen. Det
    tilsvarer omtrent 4–7 cm ved kjølen og 2,5–4 cm akter (usikkert, vinkelen
    er ukjent). Sted og retning stemmer med bildene. Brukeren mener streken
    er «ikke så langt unna». Den er målet for formen, og stroppmålingen
    kontrollerer den.
  * **`docs/foto/område.png` og `blå strek.png` er frihåndsskisser.** Brukeren
    (14.11): «du må ikke se på strekene», de er tegnet med mus for å vise hva
    han mener. De sier hvor (fra vinduets forkant til ca. 7 m) og hvilken vei
    (utover), ikke hvor mye. Claude leste først tall ut av dem; de er trukket.
  * **Målet med brukerens ord:** «fylle inn det lille stykket som rett og
    slett mangler i magen på båten, så pølsa blir helt jevn og fin hele veien»,
    «fint buet og lagt inn mot alt det som ligger rundt, alt fra nede under i
    skroget og ute fra kanten oppe og bak og foran». Altså: jevnhet er
    kriteriet. Kjøllinjen, dekkskanten, alt foran vinduet og alt fra ca. 7 m
    står.
  * Brukeren gjentok kl. 02:30 (og la seg): strekene er «for å peke på
    hensikten», ikke «rettesnor for mål»; de peker på området der pølsa skal
    fikses. «Bare hold på til ferdig.»
* **14.11.2026 (natt): trinn 9 «magen» ferdig og pushet.** Poengkortet
  `s10_mage` består alle krav. Tillegg til bunnreisning, slag og utfall
  mellom t 0,45 (3 578) og 0,88 (6 996), null med null stigning i endene
  (`BELLY_*` i `params.py`, `curves._belly`), fra `opt_mage2.py` variant f.
  Kriteriet: ingen midje (ingen hul krumning i vannlinjer og diagonaler),
  glatt, IMG_9391 ikke verre, ingen halvbredde under DWL og intet spant
  større enn foran vinduet, og n ≤ 5 akter (det myke slaget fra trinn 4).
  Buken er 5–8 cm fyldigere under vann ved 4,7–5,0 m, 2–5 cm i DWL og opptil
  4 cm 10 cm over vannet. 40–90 cm over vannet (3,7–6,1 m) er siden opptil
  0,9 cm slankere, fordi dekkskanten står fast. Det ble funnet 14.11 om
  dagen; nattrapporten sa «under 0,6 cm ved listen». Kanobunnen er 2,52 m³
  (før 2,44), største spant er uendret, og alt utenfor sonen er uendret
  (vugge 1 byte-lik). IMG_9391 ble litt bedre (rms 11,6 mot 12,1).
  * **«nye 1» er ikke til å stole på kvantitativt** for buken. Å lukke
    avviket på 15–22 cm ville krevd 3,0–3,2 m³ og en vannlinjebredde på
    2,2–2,4 m, og IMG_9391 ville bommet med 75–110 px. Bildet er et
    skjermbilde fra redigering i Bilder-appen, og de nedre radene bommer
    motsatt vei. Det er brukt bare som retning.
  * Vil brukeren ha mer «pølse», er neste knapp variant a
    (`out/opt_mage2_a.json`: DWL-bredden holdes til ca. 5,6 m; kanobunnen
    2,54 m³, bare 0,014 m³ mer enn f) eller å løfte taket for største spant.
    Variant a er for lik f til å vises som eget alternativ. Aktenfor ca. 5,5 m er spantene fortsatt
    V-formet (17–22°); IMG_9391 bekrefter hjerteformen fra ca. 6,2 m.
  * Rettet: fenderlistens kontroll (`build._union_strake_piece`) brukte rask
    `Volume()` på hele skroget, som bommer med liter. Nå avgjør den presise.
  * `docs/foto/IMG_9395.jpg` heter nå `IMG_9395_mage.jpg` (brukerens navn),
    og verktøyene er rettet. Brukerens skjermbilder er sjekket inn.
  * Les «Status – 14. november 2026: trinn 9 «magen» ferdig» i `V10.md`.
* **14.11.2026 (dag): magen som STL.** Brukeren: «jeg klarer ikke å se dette
  uten i en stl fil», så «lag det». `v10/verktoy/foto/py/mage_stl_sammenlign.py`
  skriver `export/visning/mage_foer.stl`, `mage_naa.stl`, `mage_tillegg.stl`,
  `mage_sammenligning.stl` og `mage_snitt.stl` (snitt ved 4,85 m: venstre
  halvdel før, høyre nå, strek for det gamle omrisset). Kjør med
  `memcap --gb 4 --lock` fra mappen (ca. 50 s). Filene ligger utenfor git.
* **14.11.2026 (dag): stroppen i «nye 1» vurdert; brukeren ba om «ikke endre
  nå, kun uttalelse».** Brukerens øye: buken må «pølses» litt mer, «veldig
  forsiktig», der skroget svinger inn (innsvingen). Overdelen fra midten og
  opp er en flat linje. Måling med `v10/verktoy/foto/py/n1_strap.py`: den aktre
  stroppen er et spant ved ca. 5,6–6,2 m, like foran propellen. Med fem
  kameraløsninger ligger stroppen tydelig utenfor modellen i svingen på
  begge sider og litt innenfor ved kjølen. Båten er altså fyldigere i svingen
  og flatere i bunnen der. Trinn 9 endret nesten ingenting ved 6 m
  (bunnreisning 22,8° → 21,3°). Størrelsen i bildet (9–15 cm) er ikke til å
  stole på, og IMG_9391 tillater bare et par cm fra 6,2 m og akterover.
  Claudes anbefaling, ikke gjort: et forsiktig trinn 10 med 2–4 cm mer i
  svingen ved ca. 5,0–6,2 m, flatere bunn der og jevnt til null før 6,5 m.
  Ikke dypere, ikke mer ved 4,5–5,2 m, og største spant står. Gi samtidig
  tilbake de 9 mm slanking høyt på siden, og vis det som STL med snitt ved
  5,6 m før bygging. IMG_9389 (brukerens «bilde A») måler bare kjøllinja
  forut og kan ikke avgjøre svingen. Et mål på hvor stroppmerket sitter
  (avstand fra akterspeilet) ville gjort stroppen til et ekte mål.
  * **Brukerens beslutning samme dag:** etter slicing i Bambu Studio er
    skroget «ganske bra slik vi har det i dag». Trinn 10 er lagt bort; ikke
    gjør det uten at brukeren ber om det. Brukeren printer båten slik den er
    nå (trinn 9, b9d0d29).
* **14.11.2026: V11 «gangbordet», grenen `v11`.** Brukeren: kanten akter
  på sidene har «ingen 45 graders vinkel»; «rekka der du går, den er flat
  hele veien rundt, og så kommer det en kant, en forhøyning opp», og ved
  trosse-snella akter «90 grader ned ... en buet kant» (kant2.jpg). Brukeren
  ba Claude gjøre endringen selv som versjon 11. Gjort og pushet til `v11`:
  V10s skrå skulder (40°, et anslag) er erstattet av et flatt gangbord i
  knekkens høyde, 210 mm bredt langs sidene og 110 mm over akterspeilet
  (anslag), og en 85° kant med R 40 opp til karm og akterdekk, rundt hjørnet
  (`hr26/gangbord.py`, `WALK_*`, `AFTDECK_X0` 6 000). Langs ruff og
  sprayhoodbein går kanten bare opp til dekket, og lokket passer som før.
  Poengkortet `s11_gangbord` (`score.py` 1.6, to nye krav for gangbordet)
  består 19 av 19. STL-er: `export/visning/kant_foer.stl`, `kant_naa.stl`,
  `kant_snitt.stl`. Lærdom: et OCC-kutt med kanter på 0,07 mm feilet stille og
  lot skroget være urørt; bygget sjekker nå volumet kuttet tar. Les «V11 –
  14. november 2026» øverst i `V10.md`.
* **14.11.2026: V11b, vinsjen og akterklampen (pushet til `v11`).** Brukeren
  tegnet på `kant2.1.jpg` (i `~/Downloads`, ikke i git) at gangbordet fra
  «trossesnellen» og akterover bare er 4–6 cm, og at forhøyningen smalner inn
  mot B like bak sprayhoodens bein. «Fortøyningssnurren» skal henge loddrett
  på veggen. Claudes tolkning: trossesnellen er vinsjen (6 540), og
  fortøyningssnurren er akterklampen (7 500). Gjort:
  * Gangbordet er 170 mm ved B, 55 mm fra 6 450 og 45 mm ved 7 600
    (`WALK_W_SIDE_TAB`, `WALK_TAPER_X1`).
  * Vinsjen står nå på flat topp. Akterklampen henger på veggens utside med
    45° fas under, så den printes uten support (brukeren: «kan den legge
    minste grad undenfra»).
  * Hullene ved 6 700, 7 250 og 7 680 er flyttet inn på akterdekket
    (`gangbord.hole_y`).
  * Poengkortet `s12_vinsj` (`score.py` 1.7).

  Lærdom: snittparet ved trinnet (2 mm fra hverandre) krysset hverandre, og
  gangbordkuttet tok da ingenting uten å si fra. Nå får tette par samme
  normal. Brukeren håper V11 er skroget man blir fornøyd med. Les «V11b» i
  `V10.md`.
* **Kalesjen (14.11.2026, bare vurdert):** brukeren vil spørre båtens eier om
  kalesjen (sprayhooden) skal være åpen, kanskje i stoff. Anbefaling: gjør den
  til en egen løs del, så både tynt printet skall og bøyler med stoff er
  mulig; det under (nedgang, skyveluke) må da modelleres. Dremel frarådes
  (lokket har 15 % infill). Vinduer i kalesjen: «vi lar vinduet være».
* **Hvem er hvem (14.11.2026, Claudes tolkning):** brukeren bygger modellen.
  Båten ser ut til å eies av en annen («han eieren»). Eldre notater her
  kaller brukeren «eieren».
* Krav i korte trekk: LOA 7 950 mm, bredde 2 680 mm (±0,5 %), dypgang 1 400 mm.
  Dekkslinje, spring og listehøyde skal ligge innen 12,5 mm av målepunktene.
  Rorhull, masthull og rekkehull blir der de er. Stativvuggene eksporteres på
  nytt fordi de følger tverrsnittene.

* **14.11.2026: private bilder fjernet fra GitHub («sjefsavgjørelse: slett
  alle private bilder fra GitHub, men ikke lokalt»).** Repoet er offentlig.
  En gjennomgang fant et identifiserbart ansikt i utsnitt av IMG_9304 som
  originalen har dekket til, personer i utsnitt av IMG_9370, og et bilskilt og
  et nabobåtnummer i IMG_9395. Historikken på alle grener er skrevet om med
  `git filter-repo` og force-pushet:
  * Alle bildene i `docs/foto` er fjernet, og det samme gjelder alle utsnitt,
    overlegg og poengkort laget av dem (91 stier, listet i `.gitignore`).
  * E-posten i alle commits er byttet til GitHubs noreply-adresse.

  Filene ligger fortsatt lokalt. Commit-ID-ene som er nevnt i dette notatet
  og i `V10.md`, er fra før omskrivingen. En sikkerhetskopi av den gamle
  historikken ligger lokalt i `~/Documents/HR26-backup-foer-rensing-2026-11-14.git`.
  **Regel:** bilder av den ekte båten og alt som lages av dem (utsnitt,
  overlegg, poengkort med foto) skal aldri committes. Legg nye slike
  utdatafiler i `.gitignore` eller skriv dem utenfor repoet.
* **Fargefil for Bambu (14.11.2026).** Brukeren ville bare ha fargeskift i
  høyden («ikke en to-timers jobb»). `python tools/lag_3mf.py` lager
  `export/3mf/01_skrog_farger.3mf`: rødt fra kjølen, sort fra 46,76 mm og hvitt
  fra 50,6 mm, med innstillingene fra README. Velg den enkle løsningen først.

## Referanser

* Bilder av den ekte båten ligger i `docs/foto/`, uten metadata og nedskalert
  til høyst 2400 px. Originalene ligger lokalt i `~/Documents/Seilbåt`.
  * IMG_9388: baugen forfra
  * IMG_9391: akterspeilet
  * IMG_9389: skrått bakfra
  * IMG_9387, 9374 og 9370: fra siden
  * IMG_9395_mage.jpg (før 14.11 IMG_9395.jpg): baugen og buken nedenfra
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
* **Volumkontroller (14.11.2026):** OCCs raske `Volume()` på hele skroget
  (18 m³ i full skala) kan bomme med flere liter. En kontroll som sammenligner
  små volumer (en fenderlistbit er 0,3–0,7 liter) må bruke den presise
  beregningen (`build._volume`, ca. 1 s) når den raske sier nei. Ellers
  stopper bygget på en riktig union, eller godtar en gal en.
* En endring i spantene midtskips flytter loftflaten ørlite også forut (loften
  er en spline gjennom alle spantene), så skjøre OCC-operasjoner forut kan
  oppføre seg annerledes selv om spantene der er uendret.
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
