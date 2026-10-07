# Handgjort typsnitt i lera – projektöversikt

Läs den här filen först i en ny chatt. Svara alltid på svenska.

## Arbetsregler
- Visa alltid före/efter-bilder innan filer ändras.
- Gör inga komplicerade filer eller 3D-filer förrän jag uttryckligen ber om det (spara användning).
- Behåll mina originalfiler om jag inte säger annat.

## Projektet
- Typsnittet är skulpterat i Nomad. Varje bokstav 3D-printas (Bambu Lab A1, Bambu Studio) i en printad låda.
- Gips hälls i och ger tvådelade formar (framsida + baksida).
- Leran slamgjuts ihålig, väggen ca 4 mm. PLA-mastern smälts ur med värmepistol.
- Lera krymper 10–15 %.
- Skala: 61 mm per enhet (x-höjd ca 122 mm).

## Filer
- `alfabet_nu.png` – bild på alla gemener som de ser ut nu. `versaler_alla.png` – alla versaler.
- `form.py` – formgeneratorn:
  `python3 form.py <stl[,prick.stl,...]> <utmapp> <namn>`
- `arkiv/gemener_mastrar.zip` – de valda bokstavsmastrarna (se tabellen nedan).
- `arkiv/forslag_cg_f_e.zip` – förslag som inte är godkända:
  - c_A, c_B, c_C och g_ny
  - f_rak
  - e-varianter
- `e_drag.py`, `e_form.py` – nya e:t i ett drag (inte godkänt än).
- `namn.py` – sätter ihop namn med spacing längs lutningen (satt_ihop_sb).
- `versaler.py` – versaler, 10 % tunnare (HALV 0,29). Kör `python3 versaler.py` för att skapa versaler.pkl (ligger inte i git), sedan `versaler_3d.py` för 3D.
- `BESLUT.md` – beslut som är testade i 2D men inte inlagda i källfilerna.
- `fonts/Jost-600.ttf` – Futura-lik font till texten i formarna (OFL).

### Vilken fil som är vilken bokstav (i gemener_mastrar.zip)
| Bokstav | Fil | Bokstav | Fil |
|---|---|---|---|
| a | a1.stl | o | o.stl |
| b | b.stl | p | p.stl |
| c | c1.stl | q | q2.stl |
| d | d1.stl | r | r.stl |
| g | g.stl | s | s1.stl |
| h | h_blandning.stl | t | t1_mid.stl |
| i | i.stl + i-prick.stl | v | v.stl |
| j | j.stl + j-prick.stl | w | w1.stl |
| k | k.stl | x | x.stl |
| l | l_mid.stl | y | y.stl |
| m | m.stl | z | z.stl |
| n | n.stl | u | u.stl (original, ej klar) |
| f | f.stl (gamla f:et; nya förslaget f_rak ligger i forslag-zippen) | e | e-varianter i forslag-zippen |

Prickbokstäverna:
- å = a1 + i-prick (ringen)
- ä = a1 + 2 × i-prick
- ö = o + 2 × i-prick

Exempel: `python3 form.py a1.stl,i-prick.stl,i-prick.stl ut ä`

## Formdesign (färdig och testad)
**Låda och väggar**
- Lådan har varierande storlek, högst 246 mm (10 mm marginal på bädden).
- Bokstaven ligger diagonalt om det behövs, med minst 6 mm kant.
- Väggar 1 mm, framsidans platta 1 mm, baksidans platta 2 mm.
- Rundade innerhörn (R8) och 3° släppvinkel.

**Tappar och text**
- Tappar: grunda kalotter, Ø14 × 1,5 mm. Upphöjda på framsidan, försänkta på baksidan. Inga lösa kulor.
- Texten "x framsida" / "x baksida" sitter upphöjd 0,6 mm på alla fyra innerväggar, i Jost. Den läses rättvänd i gipset.
- Bokstavsmärket är nedsänkt i baksidans gips.

**Trattar och gips**
- Trattar (gjuthål): hals Ø19, 30° från lodrätt. De krymps automatiskt så att minst 10 mm gips finns kvar (minst 18°) och hålls borta från väggarna.
  - Hålen används för att hälla ut leran och senare för att hänga upp bokstäverna.
- Prickar (i, j, å, ä, ö) gjuts i samma form, med egen tratt.
- Underskärningar fylls automatiskt (fyll_underskarningar).
- Gips över bokstaven: ca 15 mm.

**Status**
- Alla gemener utom e, u och f har färdiga formar.
- Alla formar är kontrollerade: vattentäta, en del, text på 4 väggar och inga underskärningar.

## Gips (pottery plaster)
- Blandning: 100 delar gips till 70 delar vatten, i vikt. Gips ströms i vatten, får dra 2–3 min, röres 2–3 min.
- Det går åt ca 920 g gips + 645 g vatten per liter gips.
- a (båda halvorna): 1 880 g gips + 1 315 g vatten.

| Gips per bokstav (båda halvorna) | Bokstäver |
|---|---|
| ca 1,5–2,0 kg | a c i n o r s v x z |
| ca 2,3–3,4 kg | m w å ö ä |
| ca 3,8–4,3 kg | b d g h j k l p q t y |

- Alla 26 färdiga formarna: 77 kg gips + 54 l vatten. Med e, u och f: ca 85 kg (ca 3,5 säckar à 25 kg).
- Versaler (29 st, A–Ö): uppskattning ca 130 kg gips (4–5 kg per bokstav, flera med delad låda). Inga versalformar är byggda än, så siffran är osäker.
- Två uppsättningar formar, gemener + versaler: ca 430 kg gips (ca 17–18 säckar).
- Två lerbokstäver av varje kräver INTE dubbla formar. En gipsform klarar 30–50 gjutningar, så det räcker med en uppsättning: ca 215 kg (ca 9 säckar).

## Plan: gemener först, två formar av varje
- Gips: ca 170 kg. Efter egna säcken på 25 kg återstår ca 145 kg = 7 säckar formgips à 22,7 kg från Art4Fun.
- Kostnad: ca 5 100 kr plus frakt (729 kr/säck, okt 2026, kontrollera dagspriset).

## Printinställningar (Bambu)
- Topptjocklek 1,2 mm, "ensure vertical shell thickness", 3 väggar, gyroid 10 %.
- Adaptiva lager med max lagerhöjd 0,2 för bokstaven.
- Söm: "Back" + scarf joint.
- Z-offset ställs in manuellt (0,3 gav vågor). Det är inte samma sak som Z-seam.

## Designbeslut, gemener (testade i 2D, inte inlagda i källfilerna)
- **f:**
  - rak stapel 11,5°, armar vid x-höjden (1,41–2,01), topp 3,35, svans ned till −2,1 (f_rak)
  - **Problem:** f får inte plats på bädden (267 mm). Välj delad låda eller kortare f.
- **t och l:** samma böj upptill, "mellantinget" (t1_mid, l_mid). t:s armar som originalet, i linje med f:s.
- **h:** blandning (h_blandning). **n:** vänster ben som m. **u, o:** original.
- **q:** q2, längden inte bestämd (nu / −2,25 / −2,40).
- **e:** nytt e i ett drag, jämntjockt, öga som lutar som a:s hål, svansen lyft 0,03 ("tvåan"), lite rundare öga.
  - Senast: ögats spets uppe till höger var för spetsig. Två varianter visades: "rund ände på ögat" och "rundare hörn + rund ände". Inget svar än.
- **c och g:** jag tyckte de var ojämna i tjocklek, höjd och kurva, och att g:s knorr ska följa de andra bokstävernas.
  - Förslag: c A (från o:s ring), c B (+ knoppar), c C (smalare, större öppning), g_ny (överdel från q2).
  - Inget val gjort. g_ny är inte vattentät än och måste lagas innan form.
- **Spacing:** jämn kerning längs lutningen (namn.py).

## Versaler
- 10 % tunnare (klart i versaler.py).
- Väntar. De flesta behöver delade lådor vid 61 mm/enhet.

## Öppna frågor
1. Välj c-variant och om g_ny ska användas.
2. Välj ögonspets för e. Sedan ska e och u bli klara och få formar.
3. f: delad låda eller kortare f.
4. Längd på q2.
5. Upphängning: printade väggpinnar + borrmallar 1:1 (behöver brända hålets storlek).
6. Logga: "the little archive" nedsänkt på lerans baksida (variant C, längs stapeln, 8 mm)?
7. Lägga in de godkända gemener-ändringarna i källfilerna.
