# Korpus och metod

[Hem](Home.md) · [Verkindex](Verkindex.md) · [Genre och form](Genre-och-form.md) · [Teman](Teman-och-motiv.md) · [Ämnen och fokus](Amnen-och-fokus.md) · [Figurer](Figurer.md) · [Semantik](Semantik.md) · [Metod](Korpus-och-metod.md)

## Analysenhet och täckning

- Enheten är **en textfil**, inte ett unikt litterärt verk.
- Omfattning: **120 analysbara filer**. Editoriala transkriptioner ligger utanför korpus.
- Explicit versions-/backupmärkta filer: **2** (gäller inte oidentifierade innehållsvarianter).
- Läsbara versioner analyseras; originalformaten förblir oförändrade i originals/.
- Dokument i samlingsfiler kan motsvara flera verk. Inga upphov har gissats fram.
- Ursprungsdatum saknas för många verk. Git-importdatum får inte användas som skrivdatum.

## Mätdefinitioner

- **Ordförekomst:** token separerad med Unicode-bokstäver och tillåtna bindestreck/apostrofer, skiftlägesnormaliserad.
- **Distinkt ordform:** exakt normaliserad token, inte lemma eller synonym.
- **Dokumentfrekvens:** antal källfiler där ordformen finns minst en gång.
- **Refrängjusterat tokenmått:** samma identiska textrad räknas bara en gång *inom ett och samma dokument*.
- **Innehållsord:** enkla handbyggda funktionsordslistor för svenska, engelska och patois; urvalet är inte en fullständig lingvistisk taggning.
- **Tema:** minst tre lexikala träffar och två olika signalord; flera teman kan matcha samma text.
- **Ämne:** minst två lexikala träffar och två olika signalord.
- **Fokus:** prioriterad, provisorisk enkelklassning. 'Ej fastställt' är tillåtet.
- **Figur:** exakt matchning mot ett redovisat litet namnlexikon; typer skiljs åt.
- **Konkordans:** upp till tre autentiska textrader per sökord och källfil, med länk till källa.
- **Ordgrannar:** ord inom högst tre positioner i samma matchade rad; frekvens visar närhet, inte nödvändigtvis verklig semantisk relation.

## Kvalitetsbegränsningar

Refränger driver upp frekvenser. Källornas stavningsvariation och flerspråkighet gör att närliggande former ofta räknas separat. Arkivmappar kan innehålla genreblandade texter. Namngivna historiska och fiktiva figurer är inte automatiskt huvudpersoner. Automatisk kategorisering kan ge både falska positiva och negativa träffar. Kategorier behöver senare kontrolleras av författaren.

## Reproducerbarhet

- [Fullt analysprogram](https://github.com/Hybrismannen/Texts-n-Lyrics/blob/main/tools/analyze_archive.py)
- [Maskinläsbar sammanfattning](https://github.com/Hybrismannen/Texts-n-Lyrics/blob/main/analytics/summary.json)
- [Fullständig dokumentmatris](https://github.com/Hybrismannen/Texts-n-Lyrics/blob/main/analytics/documents.csv)
- [Källmanifest med Git-hashar](https://github.com/Hybrismannen/Texts-n-Lyrics/blob/main/catalog/SOURCE_MANIFEST.md)

Det går att köra analysen lokalt med kommandot 'python3 tools/analyze_archive.py'.
