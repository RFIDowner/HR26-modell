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

## V10 – glattere skrog og dekk (startet 10.11.2026)

* Mål: skrog og dekk (`01_skrog.stl`) som ligner den ekte båten, med glatte
  linjer i stedet for «robot», uten å miste de målte linjene. Ror, mast og
  rigg er utenfor.
* Utgangspunktet er den parametriske modellen, ikke Bambu-AI-modellen. Den er
  18 % for smal og mangler undervannsdel.
* Årsaker, krav og plan står i `V10.md` i grenen `v10`. Arbeidet skjer lokalt i
  worktreen `../HR26-modell-v10`.
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

## Tekniske merknader

* `01_skrog.stl` ligger dreid +45° om Z på platen.
* Skroget alene bygger på ca. 150 s. `python -m hr26.build` sletter alle
  STL-er i `export/stl` før eksport.
* CadQuery eksporterer STL med relativ toleranse som standard, og det gir
  flis-trekanter. Bruk `Shape.exportStl(..., relative=False)`.
* OCC-avrunding feiler på skrogets dekkskant, på akterspeilet og på ruffens
  takkant. Der må rundingen bygges inn i tverrsnitt og profiler.
