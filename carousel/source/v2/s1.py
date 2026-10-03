import sys; sys.path.insert(0, '.')
from comp import *
P = PAL
cv = Canvas(rd('base_names.png'))
# label strip for number
piece(cv, 'kraft', [[70, 70], [215, 62], [218, 118], [72, 124]], None, seed=3, edge='cut')
write(cv, 'Nº 1', 'SpecialElite', 34, 144, 94, P['ink'], rot=-2, typewriter=True, seed=1)
# name, cut from papers
cut_word(cv, 'Alessio', 'AlfaSlabOne', 128, 590, 465, [('stripes', (P['blush'], P['roseDeep'])), ('cream', P['dove'])], seed=4, track=10, rot_amp=3)
# pronunciation typed on a torn butter slip
piece(cv, 'cream', [[330, 520], [850, 505], [856, 590], [334, 604]], P['butter'], seed=8)
write(cv, 'Italian:  [aˈlɛssjo]', 'Gentium-Italic', 44, 592, 556, P['ink'], rot=-1.5, seed=2, bleed=0.5, grain=0.18)
# origin as typed strips
piece(cv, 'cream', [[250, 655], [690, 645], [694, 700], [252, 707]], '#f7f1e3', seed=12, edge='cut')
write(cv, 'From Greek alexō, meaning', 'SpecialElite', 27, 472, 675, P['ink'], rot=-1.2, typewriter=True, seed=5)
piece(cv, 'cream', [[420, 712], [760, 716], [758, 768], [418, 764]], '#f7f1e3', seed=13, edge='cut')
write(cv, '“to defend or help.”', 'SpecialElite', 27, 590, 740, P['ink'], rot=0.6, typewriter=True, seed=6)
# meaning handwritten in ink on the sheet
paragraph(cv, 'Someone whose quiet strength makes others feel safe enough to be themselves.', 'HomemadeApple', 29, 600, 850, 690, 64, '#2f2a3a', rot=-2.5, seed=7, bleed=0.45, grain=0.3)
# stickers & ephemera
sticker(cv, 'lemons', 905, 205, 230, rot=-8, seed=1)
sticker(cv, 'train', 210, 1210, 270, rot=5, seed=2)
stamp(cv, 900, 1135, 140, 172, 'plane', P['roseDeep'], 'POSTE ITALIANE', '5', rot=7, seed=3)
postmark(cv, 900, 1060, 'ROMA', '12.IV.26', rot=-12, seed=4)
tape(cv, 885, 1040, 90, 30, 35, '#e9d6b4', seed=5)
cutout(cv, 'src/d15.png', (140, 95, 385, 410), 120, 360, 0.55, rot=-14)
cutout(cv, 'src/d15.png', (840, 1210, 1045, 1325), 960, 1280, 0.8, rot=-3)
save(finish(cv.img), 's1.png')
