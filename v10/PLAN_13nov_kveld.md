# V10, kvelden 13.11: rett stevn, fenderlist i bue over akterspeilet og hjerteform under vann akter

## Kontekst

Eieren så på skjermklippene (IMG_9374, IMG_9370 og IMG_9391 mot modellen) og ga ny retning:

* **Ny rekkefølge for kildene:** Når bildene av båten og tegningene eller brosjyren er
  uenige, gjelder bildene. Tegningene (Enderlein 448-5 og brosjyren) brukes der bildene
  ikke viser noe, og Bambu brukes bare som stilmål. Dette erstatter «tegninger fra
  produsent trumfer alt».
* **Kjølens tykkelse er avgjort:** 240 mm, målt på IMG_9388. Den saken er lukket.

Funnene:

1. **Stevnen:** I IMG_9374 og IMG_9370 er stevnen rett fra fenderlisten ned til
   vannlinjestripen. Avviket fra en rett linje er 0,2–0,7 px, det vil si 2–6 mm.
   Enderlein 448-5 viser det samme: rett med ca. 49° mot vannlinjen. Modellen bruker en
   gammel potensformel (`curves._bottom_spline`, `_STEM_EXP = 1.30`) som buer: 56° øverst
   og 44° ved stripen. Midt på buler den 39 mm ut fra korden, og 20–60 cm over
   vannlinjen ligger den 4–4,5 cm for langt forut. Her er bildene og tegningen enige.
2. **Fenderlisten over akterspeilet:** I IMG_9391 buer den opp mot midten over roret. I
   modellen ligger den vannrett tvers over: `hull._strake_path` har konstant `zs`.
3. **Under vann akter:** Akterfra smalner bunnen inn som bunnen av et hjerte (vinglass)
   med hul overgang inn mot roret. Modellen er en bred U som går for dypt, 115–140 px for
   bred i IMG_9391. Volumet er 3,4 m³ mot 2,36 m³ (448-5) og 2,44 m³ (2,5 t). Med den nye
   regelen er trinn 3 avgjort: formen følger IMG_9391. Strekprikklinjen på 448-5 taper.

## Valgt kurs

Rekkefølgen er stevn, så akterspeil, så formen under vann. Hvert trinn får egen commit og
pushes til `v10` når det er grønt. Rammer for natteøkta:

* Alle tunge jobber kjøres via `python tools/memcap.py --gb 5 --lock -- ...`.
* Høyst 2 agenter i gang samtidig.
* Arbeidet stopper når ukekvoten er 70 %.

### 0. Forberedelse (ca. 15 min)

* Oppdater CLAUDE.md og minnet (`hr26-stil-og-tykkelse.md`) med den nye
  kilderekkefølgen og med at kjølens tykkelse er lukket på 240 mm. Commit og push.
* Kamera- og bildeverktøyet ligger bare i en gammel scratchpad
  (`…/74d216f8-…/scratchpad/kontroll/undervann/py`). Kopier det inn i repoet under
  `v10/verktoy/foto/`, med relative stier, før temp-mappa forsvinner. Det gjelder
  `common.py`, `uwlib.py`, `photos.py`, `t9391.py`, `sil9391.py`, `eval9391.py`,
  `ovl9391.py`, `dw.py` og `opt*.py`.
* Gjenbruk kameraet `v10/rapporter/13nov/undervann_out/cam9391.json` («zc5»), sporet
  `t9391.json` (red_outline) og `v10/arbeid/v10/photo/fit9370c.json`.

### 1. Rett stevn (`hr26/curves.py`)

* **Mål på IMG_9370** (båten flyter, nesten rett fra siden, 9,6 mm/px):
  * Kameraet stilles inn bare etter fenderlisten, vannlinjestripen og vannflaten, ikke
    etter stevnen.
  * Mål stevnens vinkel og overhenget, altså den vannrette avstanden fra toppen av
    stevnen til der stevnen møter vannet.
  * Kryssjekk mot at IMG_9374 er rett, og mot 448-5 (49°). Ventet resultat: 49 ± 2°.
* **Endringen i `_bottom_spline`:** Formelen (`_STEM_EXP` og `_STEM_FIT_X1`) byttes ut
  med punkter på en rett linje fra fenderlistens høyde (z ≈ 1 100) ned til z ≈ 300, med
  vinkelen fra bildet.
  * `eq` beholdes: toppen av stevnen i (0, sheer_z(0)).
  * `LWL_FWD` får flytte seg høyst 30 mm hvis bildet sier det. Splinen glatter over i den
    sporede forfoten under z ≈ 250.
  * Rundingen øverst ved toppen av stevnen tas av nesa som finnes fra før (`BOW_NOSE_L`).
* **Krav:**
  * LOA 7 950 ± 40.
  * Stevnen rett innen 5 mm for z 300–1 090.
  * Veggen minst 2 mm i baugen (`VOID_BOW_EXTRA`).
  * Fenderlistens start (`STRAKE_X0`), stevnbeslaget og pulpithullene står fortsatt i
    materiale.

### 2. Fenderlisten i bue over akterspeilet (`hr26/hull.py`, `hr26/params.py`)

* **Mål på IMG_9391** med zc5-kameraet: fenderlistens senter og akterspeilets overkant
  tvers over.
  * Trekk fra den delen av buen som perspektivet lager ut av akterspeilets bue i plan
    (`TRANSOM_CAMBER_R` 3 050).
  * Tilpass løftet midt på. Anslaget fra bildet er 3–6 cm.
* **Ny parameter `STRAKE_TRANSOM_RISE`.** I `_strake_path` blir delen over akterspeilet
  z = zs + løft·(1 − (y/yt)²)², som går glatt over i hjørnebuen.
* **Hvis overkanten av akterspeilet også buer mer** enn dagens dekksbue (ca. 20 mm der):
  * Legg en akterbue inn i `curves.deck_camber`, ramp fra x 7 300, slik at båndet over
    listen blir like bredt.
  * `transom_cutter` og rundingen av overkanten (`TRANSOM_TOP_R`/`_EXIT`) må følge med.
  * Test overkanten med prøvestykket av akterspeilet før hele skroget bygges, fordi OCC
    er følsom her.
* **Krav:** Listen ligger innen ±1,5 px av sporet i IMG_9391, og nettet er lukket.

### 3. Hjerteform under vann akter (trinn 3 i `V10.md`)

* **Utgangspunkt:** `v10/rapporter/13nov/patcher/undervann.patch` og
  `v1_on_top_of_undervann.patch`.
  * Delen for `curves.py` går rett inn. `params.py` må flettes for hånd etter trinn 1.
  * Patchene gir dødtre (`DEADWOOD_H`, `DEADWOOD_W`) med hul overgang, altså
    vinglass-spant, en dyp senterlinje til akterspeilets fot (≈ −410, Enderlein) og nye
    `SECTION_N`/`SECTION_DEADRISE`.
* **Tilpasning uten CAD:** Formen justeres i `curves` og nettet fra `photos.py`
  (sekunder per runde). Målene, i prioritert rekkefølge:
  1. Omrisset i IMG_9391: rms ≤ 20 px (i dag 115–140 px for bredt), og hjertets spiss
     møter roret der bildet viser det.
  2. Bildene fra siden og skrått bakfra (IMG_9387 og IMG_9389) skal ikke bli dårligere.
  3. Volumet med kjøl og ror skal være 2,2–2,6 m³, med LCB 4 450–4 800.
  4. Bunnen midtskips ved kjølen: eieren svarte «følg bildet». Midtpartiet med hul
     overgang fra V1 (`DEADWOOD_H` fra 2 900) får stå hvis IMG_9391 og volumet krever
     det. Rapporten oppgir avstanden fra kjølsiden ut til skroget ved x 4 750, z −300.
* **I samme commit** (oppskriften i `V10.md`):
  * `KEEL_FILLET` blir 0 hvis det blir dødtre under kjølen, ellers 90.
  * `hull._CUT_LEVELS[0]` endres fra −450 til −550.
  * Rortappene (`RUDDER_PIN_Z`) skal stå i massivt materiale.
  * Akterspeilets fot testes med `transom_cutter`.
  * Innredningen: durken (`INT_SOLE_Z` −285, toalettrom −212) og hulrommet skal ha minst
    2 mm vegg mot den nye, smalere bunnen.
  * Vuggene følger med.

### 4. Bygging, kontroll og push (etter hvert av trinn 1–3)

* Bygg: `python tools/memcap.py --gb 5 --lock -- python -m hr26.build --only skrog,stativ-vugge1,stativ-vugge2,ruff-tak`
  (ca. 3 min).
* Kjør poengkortet `v10/arbeid/v10/score/score.py`. Alle gamle krav skal være grønne.
  Legg til nye kontroller: at stevnen er rett, løftet på listen, rms for omrisset i
  IMG_9391, og volum/LCB.
* Lag på nytt prøvebitene i `export/test/` som berøres (`tools/proevebiter.py`).
* Oppdater statusavsnittet i `V10.md` og README hvis delene endres. Push til `v10` når
  alt er grønt.

## Verifisering

* Overleggsbilder, ett per trinn: IMG_9370 og IMG_9374 med stevnen, IMG_9391 med hjertet
  og listen, IMG_9389 skrått bakfra.
* Poengkortet: LOA, bredde, dypgang, dekkslinje, spring, list, rekkehull, masthull,
  vegg ≥ 2 mm og lukket nett. Alt grønt.
* Toppminne under 5 GB. Byggetid og toppminne logges i commiten.
* Rapporten til eieren: hva som er endret, bildene og spørsmålene som står igjen.
