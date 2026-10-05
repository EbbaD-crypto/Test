# The Little Archive – start här (för en ny chatt)

1. Läs `brand/varumarke.md`. Sektionen **"NY STIL (gäller nu)"** längst ner gäller. Allt ovanför är historik.
2. Stilen byggs av `carousel/source/v4/build.js` (Playwright + ffmpeg):
   - carousel 1080×1350: omslag + 5 namnbilder, reel 1080×1920 i stop motion (allt dyker upp, hårda klipp)
   - namn i **Milk Honey** (färgtypsnitt). Filen ligger INTE i repot, så ladda upp `MilkHoney.otf` igen och lägg den i `brand/fonts/`.
   - övriga typsnitt: Libre Caslon Text (+Italic), Gentium Book Plus Italic (finns i scratch, hämtas från Google Fonts)
   - textrader balanseras (inga horungar)
3. Innehåll: `content/namnkaruseller_A-Z.pdf` med 52 karuseller och 260 namn, publiceringsordning och engelska texter.
   Uttalet i PDF:en är lättläst, t.ex. [ah-LESS-yo], inte IPA.
4. Exempel på färdig stil: `carousel/01_omslag.png` – `06_Arthur.png`, `carousel/reel_5_boy_names.mp4`.
5. Karuseller enligt publiceringsordningen byggs av `carousel/source/v5/` (samma stil som v4):
   - `node symbols.js` ritar temasymbolerna (SVG), `python3 symbols.py` gör dem till utklippta akvarellbitar i `sym/` (jämn färg, inga fläckar)
   - `node build.js [postnr...]` bygger karusellerna till `carousel/<nr>_<bokstav>_<tema>/`
   - Milk Honey saknar å/ä/ö/é/è; prickar och accenter ritas därför till i build.js
   - Typsnitten Libre Caslon och Gentium ligger i `carousel/source/fonts/` (OFL, från @fontsource)
   - Klart: 01 V Boy (Italian Villa), 02 A Girl (Villa by the Sea), 03 B Boy (Countryside)
